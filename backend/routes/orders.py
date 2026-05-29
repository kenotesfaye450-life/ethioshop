from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from math import ceil
from extensions import db
from sqlalchemy import func
from models import (
    Order, OrderItem, User, Product, CreditTransaction, Referral, OrderMessage,
    Payment, Review, SiteSetting,
)
from config import Config
from utils.auth import require_auth, require_role

bp = Blueprint('orders', __name__, url_prefix='/api/orders')

def calculate_max_credit(subtotal, user_credit):
    """Calculate maximum credit that can be applied (all values in cents as int)."""
    subtotal = int(subtotal)
    user_credit = int(user_credit)
    max_by_percentage = int(subtotal * Config.MAX_CREDIT_PERCENTAGE)
    max_by_cap = int(Config.MAX_CREDIT_ETB * 100)
    max_by_balance = user_credit
    return min(max_by_percentage, max_by_cap, max_by_balance)

@bp.route('', methods=['POST'])
def create_order():
    """Create new order"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['phone', 'items', 'payment_method']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': f'Missing required fields: {", ".join(missing)}'
                }
            }), 400
        
        # Get or create user
        user = User.query.filter_by(phone=data['phone']).first()
        if not user:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'User not found. Please register first.'
                }
            }), 404
        
        # Calculate subtotal and validate stock (with row locking)
        items = data['items']
        subtotal = 0
        order_items_data = []
        
        for item in items:
            # Use SELECT FOR UPDATE to lock the row and prevent race conditions
            product = Product.query.filter_by(id=item['product_id']).with_for_update().first()
            if not product:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': f'Product {item["product_id"]} not found'
                    }
                }), 404
            
            qty = int(item['quantity'])
            if int(product.stock) < qty:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': f'Insufficient stock for {product.name}'
                    }
                }), 400
            
            line_total = int(product.selling_price) * qty
            subtotal += line_total
            
            order_items_data.append({
                'product': product,
                'quantity': qty,
                'price': product.selling_price
            })
        
        # Validate minimum order
        min_order = Config.MINIMUM_ORDER_ETB * 100  # Convert to cents
        if subtotal < min_order:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': f'Minimum order is {Config.MINIMUM_ORDER_ETB} ETB'
                }
            }), 400
        
        # Calculate credit usage (ensure numeric types)
        credit_to_use = int(float(data.get('credit_used', 0) or 0) * 100)
        max_credit = calculate_max_credit(subtotal, user.credit_balance)
        
        if credit_to_use > max_credit:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': f'Maximum credit allowed is {max_credit / 100} ETB'
                }
            }), 400
        
        final_total = subtotal - credit_to_use
        payment_plan = (data.get('payment_plan') or 'half').strip().lower()
        if payment_plan not in ['full', 'half']:
            payment_plan = 'full'
        if payment_plan == 'half':
            amount_paid = int(ceil(final_total / 2))
            payment_status = 'partial'
        else:
            amount_paid = int(final_total)
            payment_status = 'paid'
        
        # Create order
        order = Order(
            user_id=user.id,
            subtotal=subtotal,
            credit_used=credit_to_use,
            final_total=final_total,
            payment_method=data['payment_method'],
            payment_proof_url=data.get('payment_proof_url'),
            payment_plan=payment_plan,
            amount_paid=amount_paid,
            payment_status=payment_status,
            delivery_location=data.get('delivery_location'),
            trusted_receiver_name=data.get('trusted_receiver_name'),
            trusted_receiver_phone=data.get('trusted_receiver_phone'),
            local_person_name=(data.get('local_person_name') or '').strip() or None,
            local_person_phone=(data.get('local_person_phone') or '').strip() or None,
            local_person_notes=(data.get('local_person_notes') or '').strip() or None,
            status='pending_verification'
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        db.session.add(Payment(
            order_id=order.id,
            amount=amount_paid,
            payment_proof_url=order.payment_proof_url,
            payment_type='initial',
            status='pending'
        ))
        
        # Create order items and update stock
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data['product'].id,
                quantity=item_data['quantity'],
                price_at_purchase=item_data['price']
            )
            db.session.add(order_item)
            
            # Decrement stock
            item_data['product'].stock -= item_data['quantity']
        
        # Deduct credit from user
        if credit_to_use > 0:
            user.credit_balance -= credit_to_use
            
            # Record credit transaction
            transaction = CreditTransaction(
                user_id=user.id,
                amount=-credit_to_use,
                transaction_type='order_used',
                related_order_id=order.id
            )
            db.session.add(transaction)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order': {
                'id': order.id,
                'subtotal': order.subtotal / 100,
                'credit_used': order.credit_used / 100,
                'final_total': order.final_total / 100,
                'amount_paid': order.amount_paid / 100,
                'remaining_amount': max(order.final_total - order.amount_paid, 0) / 100,
                'payment_status': order.payment_status,
                'payment_plan': order.payment_plan,
                'status': order.status
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': str(e)
            }
        }), 500

@bp.route('/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get order details"""
    try:
        order = Order.query.get(order_id)
        
        if not order:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': f'Order {order_id} not found'
                }
            }), 404
        
        items = [{
            'product_id': item.product_id,
            'product_name': item.product.name,
            'quantity': item.quantity,
            'price': item.price_at_purchase / 100
        } for item in order.items]
        
        return jsonify({
            'success': True,
            'order': {
                'id': order.id,
                'user_phone': order.user.phone if order.user else None,
                'subtotal': order.subtotal / 100,
                'credit_used': order.credit_used / 100,
                'final_total': order.final_total / 100,
                'status': order.status,
                'delivery_status': order.delivery_status,
                'payment_method': order.payment_method,
                'payment_proof_url': order.payment_proof_url,
                'payment_plan': order.payment_plan,
                'amount_paid': order.amount_paid / 100,
                'remaining_amount': max(order.final_total - order.amount_paid, 0) / 100,
                'payment_status': order.payment_status,
                'delivery_location': order.delivery_location,
                'local_person_name': order.local_person_name,
                'local_person_phone': order.local_person_phone,
                'local_person_notes': order.local_person_notes,
                'items': items,
                'created_at': order.created_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': str(e)
            }
        }), 500

@bp.route('/<int:order_id>/payment-proof', methods=['PATCH'])
def upload_payment_proof(order_id):
    """Upload payment proof for an order"""
    try:
        data = request.get_json()
        payment_proof_url = data.get('payment_proof_url')
        phone = data.get('phone', '').strip()

        if not phone:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'phone is required'
                }
            }), 400
        
        if not payment_proof_url:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'payment_proof_url is required'
                }
            }), 400
        
        order = Order.query.get(order_id)
        
        if not order:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': f'Order {order_id} not found'
                }
            }), 404

        if not order.user or order.user.phone != phone:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'This order does not belong to the provided phone number'
                }
            }), 403
        
        if order.status != 'pending_verification' and not order.evidence_requested:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': f'Cannot update payment proof for order with status {order.status}'
                }
            }), 400

        order.payment_proof_url = payment_proof_url
        if order.evidence_requested:
            order.additional_proof_url = payment_proof_url
            order.evidence_requested = False
        if order.payment_status == 'pending':
            order.payment_status = 'partial'
        if order.amount_paid <= 0:
            order.amount_paid = min(order.final_total, int(ceil(order.final_total / 2)))
        db.session.add(Payment(
            order_id=order.id,
            amount=max(order.amount_paid, 0),
            payment_proof_url=payment_proof_url,
            payment_type='initial' if order.payment_plan == 'full' else 'initial',
            status='pending'
        ))
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order': {
                'id': order.id,
                'payment_proof_url': order.payment_proof_url
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': str(e)
            }
        }), 500

@bp.route('/<int:order_id>/assign-delivery', methods=['PATCH'])
@require_auth
def assign_delivery(order_id):
    """Assign delivery person to order"""
    try:
        data = request.get_json()
        
        required = ['delivery_person_name', 'delivery_person_phone']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': f'Missing required fields: {", ".join(missing)}'
                }
            }), 400
        
        order = Order.query.get(order_id)
        
        if not order:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': f'Order {order_id} not found'
                }
            }), 404
        
        if order.status != 'confirmed':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Only confirmed orders can be assigned for delivery'
                }
            }), 400
        
        order.delivery_person_name = data['delivery_person_name']
        order.delivery_person_phone = data['delivery_person_phone']
        order.delivery_status = 'assigned'
        
        db.session.commit()
        
        # Send notification
        try:
            from services.telegram_service import NotificationService
            NotificationService.notify_order_status_change(order)
        except Exception as e:
            print(f"Notification error: {e}")
        
        return jsonify({
            'success': True,
            'order': {
                'id': order.id,
                'delivery_status': order.delivery_status
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': str(e)
            }
        }), 500

@bp.route('/<int:order_id>/verify', methods=['PUT'])
@require_auth
def verify_order(order_id):
    """Verify order payment (admin only)"""
    try:
        data = request.get_json()
        approved = data.get('approved', False)
        
        order = Order.query.get(order_id)
        
        if not order:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': f'Order {order_id} not found'
                }
            }), 404
        
        if approved:
            # Process referral reward BEFORE confirming order
            user = User.query.get(order.user_id)
            if user.referred_by:
                # Award once per referred user (not per order attempt)
                already_awarded = Referral.query.filter_by(referred_user_id=user.id).first()
                if not already_awarded:
                    referrer = User.query.get(user.referred_by)
                    if referrer:
                        reward_amount = int(Config.REFERRAL_REWARD_ETB * 100)
                        max_year_etb = float(SiteSetting.get('max_referral_per_year', '2000') or 2000)
                        since = datetime.utcnow() - timedelta(days=365)
                        earned_year = db.session.query(func.sum(CreditTransaction.amount)).filter(
                            CreditTransaction.user_id == referrer.id,
                            CreditTransaction.transaction_type == 'referral_earned',
                            CreditTransaction.created_at >= since,
                        ).scalar() or 0
                        cap_cents = int(max_year_etb * 100)
                        if int(earned_year) + reward_amount <= cap_cents:
                            referrer.credit_balance += reward_amount
                            referrer.total_referrals += 1
                            db.session.add(Referral(
                                referrer_id=referrer.id,
                                referred_user_id=user.id,
                                order_id=order.id,
                                credit_awarded=reward_amount,
                            ))
                            db.session.add(CreditTransaction(
                                user_id=referrer.id,
                                amount=reward_amount,
                                transaction_type='referral_earned',
                                related_order_id=order.id,
                            ))
            
            # Now confirm the order
            order.status = 'confirmed'
            order.delivery_status = 'pending_assignment'
            order.delivery_status_updated_at = datetime.utcnow()
        else:
            order.status = 'rejected'
            order.customer_note = data.get('customer_note') or data.get('admin_notes') or order.customer_note

            # Restore credit
            if order.credit_used > 0:
                user = User.query.get(order.user_id)
                user.credit_balance += order.credit_used
                
                transaction = CreditTransaction(
                    user_id=user.id,
                    amount=order.credit_used,
                    transaction_type='cancellation_reversed',
                    related_order_id=order.id
                )
                db.session.add(transaction)
            
            # Restore stock
            for item in order.items:
                product = Product.query.get(item.product_id)
                if product:
                    product.stock += item.quantity
        
        db.session.commit()
        
        # Send notification
        try:
            from services.telegram_service import NotificationService
            NotificationService.notify_order_status_change(order)
        except Exception as e:
            print(f"Notification error: {e}")
        
        return jsonify({
            'success': True,
            'order': {
                'id': order.id,
                'status': order.status
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': str(e)
            }
        }), 500


@bp.route('/<int:order_id>/delivery-status', methods=['PATCH'])
@require_auth
def update_delivery_status(order_id):
    """Update delivery status (warehouse_staff, verifier, super_admin only)."""
    try:
        allowed_roles = ['warehouse_staff', 'verifier', 'super_admin']
        if request.admin_role not in allowed_roles:
            return jsonify({
                'success': False,
                'error': {'code': 'INSUFFICIENT_PERMISSIONS', 'message': 'Only warehouse staff or admin can update delivery status'}
            }), 403

        data = request.get_json()
        new_status = data.get('status')
        valid_statuses = ['assigned', 'in_transit', 'delivered']

        if new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': f'Status must be one of: {", ".join(valid_statuses)}'}
            }), 400

        order = Order.query.get(order_id)
        if not order:
            return jsonify({
                'success': False,
                'error': {'code': 'NOT_FOUND', 'message': f'Order {order_id} not found'}
            }), 404

        if order.status != 'confirmed':
            return jsonify({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': 'Only confirmed orders can have delivery status updated'}
            }), 400

        order.delivery_status = new_status
        order.delivery_status_updated_at = datetime.utcnow()
        # Auto-mark order as delivered when delivery is confirmed
        if new_status == 'delivered':
            if order.payment_status != 'paid':
                return jsonify({
                    'success': False,
                    'error': {'code': 'VALIDATION_ERROR', 'message': 'Remaining payment must be completed before delivery confirmation'}
                }), 400
            order.status = 'delivered'
            order.delivery_confirmed_at = datetime.utcnow()
            order.delivery_confirmed_by = 'admin'

        db.session.commit()

        try:
            from services.telegram_service import NotificationService
            NotificationService.notify_order_status_change(order)
        except Exception as e:
            print(f"Notification error: {e}")

        return jsonify({
            'success': True,
            'order': {
                'id': order.id,
                'status': order.status,
                'delivery_status': order.delivery_status
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {'code': 'SERVER_ERROR', 'message': str(e)}
        }), 500


@bp.route('/<int:order_id>/pay-remaining', methods=['POST'])
def pay_remaining(order_id):
    """Upload proof for remaining amount payment."""
    try:
        data = request.get_json() or {}
        phone = data.get('phone', '').strip()
        payment_proof_url = data.get('payment_proof_url')
        if not phone or not payment_proof_url:
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'phone and payment_proof_url are required'}}), 400

        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Order not found'}}), 404
        if not order.user or order.user.phone != phone:
            return jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'Order does not belong to this phone number'}}), 403
        if order.payment_status == 'paid':
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Order already fully paid'}}), 400

        remaining = max(order.final_total - (order.amount_paid or 0), 0)
        if remaining <= 0:
            order.payment_status = 'paid'
            db.session.commit()
            return jsonify({'success': True, 'order': {'id': order.id, 'payment_status': order.payment_status}}), 200

        order.amount_paid = order.final_total
        order.payment_status = 'paid'
        order.payment_proof_url = payment_proof_url
        db.session.add(Payment(
            order_id=order.id,
            amount=remaining,
            payment_proof_url=payment_proof_url,
            payment_type='remaining',
            status='pending'
        ))
        db.session.commit()
        return jsonify({
            'success': True,
            'order': {
                'id': order.id,
                'payment_status': order.payment_status,
                'amount_paid': order.amount_paid / 100,
                'remaining_amount': 0
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:order_id>/confirm-delivery', methods=['POST'])
def confirm_delivery(order_id):
    """Customer confirms delivery when fully paid."""
    try:
        data = request.get_json() or {}
        phone = data.get('phone', '').strip()
        if not phone:
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'phone is required'}}), 400
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Order not found'}}), 404
        if not order.user or order.user.phone != phone:
            return jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'Order does not belong to this phone number'}}), 403
        if order.delivery_status != 'in_transit':
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Order is not in transit'}}), 400
        if order.payment_status != 'paid':
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Please complete remaining payment before confirming delivery'}}), 400

        order.delivery_status = 'delivered'
        order.delivery_status_updated_at = datetime.utcnow()
        order.status = 'delivered'
        order.delivery_confirmed_at = datetime.utcnow()
        order.delivery_confirmed_by = 'customer'
        db.session.commit()
        return jsonify({'success': True, 'order': {'id': order.id, 'status': order.status, 'delivery_status': order.delivery_status}}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:order_id>/force-confirm-delivery', methods=['PATCH'])
@require_auth
def force_confirm_delivery(order_id):
    """Admin force confirms delivery."""
    try:
        if request.admin_role not in ['warehouse_staff', 'super_admin']:
            return jsonify({'success': False, 'error': {'code': 'INSUFFICIENT_PERMISSIONS', 'message': 'Only warehouse staff or super admin'}}), 403
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Order not found'}}), 404
        if order.payment_status != 'paid':
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Cannot force confirm before full payment'}}), 400

        order.delivery_status = 'delivered'
        order.delivery_status_updated_at = datetime.utcnow()
        order.status = 'delivered'
        order.delivery_confirmed_at = datetime.utcnow()
        order.delivery_confirmed_by = 'admin'
        db.session.commit()
        return jsonify({'success': True, 'order': {'id': order.id, 'status': order.status, 'delivery_status': order.delivery_status}}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:order_id>/mark-remaining-paid', methods=['PATCH'])
@require_auth
def mark_remaining_paid(order_id):
    """Admin marks remaining payment as paid (e.g., cash on delivery)."""
    try:
        if request.admin_role not in ['warehouse_staff', 'super_admin', 'verifier']:
            return jsonify({'success': False, 'error': {'code': 'INSUFFICIENT_PERMISSIONS', 'message': 'Not allowed'}}), 403
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Order not found'}}), 404
        remaining = max(order.final_total - (order.amount_paid or 0), 0)
        if remaining <= 0:
            order.payment_status = 'paid'
            db.session.commit()
            return jsonify({'success': True, 'order': {'id': order.id, 'payment_status': order.payment_status}}), 200
        order.amount_paid = order.final_total
        order.payment_status = 'paid'
        db.session.add(Payment(order_id=order.id, amount=remaining, payment_type='manual', status='verified', verified_by=request.admin_id))
        db.session.commit()
        return jsonify({'success': True, 'order': {'id': order.id, 'payment_status': order.payment_status, 'amount_paid': order.amount_paid / 100}}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/auto-confirm-overdue', methods=['POST'])
@require_auth
def auto_confirm_overdue():
    """Auto-confirm in-transit orders older than 14 days."""
    try:
        if request.admin_role not in ['super_admin', 'warehouse_staff']:
            return jsonify({'success': False, 'error': {'code': 'INSUFFICIENT_PERMISSIONS', 'message': 'Only warehouse staff or super admin'}}), 403
        cutoff = datetime.utcnow() - timedelta(days=14)
        orders = Order.query.filter(
            Order.delivery_status == 'in_transit',
            Order.delivery_status_updated_at <= cutoff
        ).all()
        updated = []
        for order in orders:
            if order.payment_status != 'paid':
                continue
            order.delivery_status = 'delivered'
            order.status = 'delivered'
            order.delivery_status_updated_at = datetime.utcnow()
            order.delivery_confirmed_at = datetime.utcnow()
            order.delivery_confirmed_by = 'system'
            updated.append(order.id)
        db.session.commit()
        return jsonify({'success': True, 'updated_count': len(updated), 'order_ids': updated}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:order_id>/reviews', methods=['POST'])
def submit_reviews(order_id):
    """Customer rates delivered order items."""
    try:
        data = request.get_json() or {}
        phone = data.get('phone', '').strip()
        reviews = data.get('reviews') or []
        if not phone or not reviews:
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'phone and reviews are required'}}), 400
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Order not found'}}), 404
        if not order.user or order.user.phone != phone:
            return jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'Order does not belong to this phone number'}}), 403
        if order.status != 'delivered':
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Only delivered orders can be reviewed'}}), 400

        product_ids_in_order = {item.product_id for item in order.items}
        created = 0
        for r in reviews:
            product_id = int(r.get('product_id'))
            rating = int(r.get('rating'))
            comment = (r.get('comment') or '').strip()
            if product_id not in product_ids_in_order or rating < 1 or rating > 5:
                continue
            exists = Review.query.filter_by(order_id=order.id, product_id=product_id, user_id=order.user_id).first()
            if exists:
                exists.rating = rating
                exists.comment = comment
            else:
                db.session.add(Review(
                    order_id=order.id,
                    product_id=product_id,
                    user_id=order.user_id,
                    rating=rating,
                    comment=comment
                ))
                created += 1
        db.session.commit()
        return jsonify({'success': True, 'created': created}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:order_id>/request-evidence', methods=['PATCH'])
@require_auth
def request_order_evidence(order_id):
    """Admin requests additional payment proof from customer."""
    try:
        data = request.get_json() or {}
        note = data.get('note') or data.get('customer_note') or ''

        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Order not found'}}), 404

        order.evidence_requested = True
        order.customer_note = note
        db.session.commit()

        try:
            from services.telegram_service import NotificationService
            NotificationService.notify_evidence_requested(order=order, note=note)
        except Exception as e:
            print(f"Notification error: {e}")

        return jsonify({'success': True, 'order': {'id': order.id, 'evidence_requested': True}}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:order_id>/messages', methods=['GET'])
def get_order_messages(order_id):
    try:
        phone = request.args.get('phone', '').strip()
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Order not found'}}), 404
        if phone and (not order.user or order.user.phone != phone):
            return jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'Access denied'}}), 403

        msgs = OrderMessage.query.filter_by(order_id=order_id).order_by(OrderMessage.created_at.asc()).all()
        return jsonify({
            'success': True,
            'messages': [{
                'id': m.id,
                'sender_type': m.sender_type,
                'message': m.message,
                'created_at': m.created_at.isoformat(),
            } for m in msgs],
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:order_id>/messages', methods=['POST'])
def post_order_message(order_id):
    try:
        data = request.get_json() or {}
        phone = data.get('phone', '').strip()
        message = (data.get('message') or '').strip()
        if not message:
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'message required'}}), 400

        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Order not found'}}), 404

        sender_type = 'customer'
        if getattr(request, 'admin_id', None):
            sender_type = 'admin'
        elif not phone or not order.user or order.user.phone != phone:
            return jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'Access denied'}}), 403

        msg = OrderMessage(order_id=order_id, sender_type=sender_type, message=message)
        db.session.add(msg)
        if sender_type == 'admin':
            order.customer_note = message
        db.session.commit()
        return jsonify({'success': True, 'message': {'id': msg.id, 'sender_type': sender_type}}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500
