from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func
from backend.extensions import db
from backend.models import User, Order, Request, TelegramUser, CreditTransaction, Product, BotCart, SiteSetting
from backend.utils.auth import require_auth
from backend.utils.bot_auth import verify_bot_secret
from backend.config import Config
import re
import random
import string

bp = Blueprint('users', __name__, url_prefix='/api/users')

def validate_ethiopian_phone(phone):
    """Validate Ethiopian phone number format"""
    patterns = [
        r'^\+251[97]\d{8}$',
        r'^251[97]\d{8}$',
        r'^0[97]\d{8}$'
    ]
    return any(re.match(pattern, phone) for pattern in patterns)

def generate_referral_code():
    """Generate unique referral code"""
    while True:
        code = 'ETH' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        if not User.query.filter_by(referral_code=code).first():
            return code

@bp.route('/by-chat-id/<chat_id>', methods=['GET'])
def get_user_by_chat_id(chat_id):
    """Resolve linked phone from Telegram chat_id (used by bot after restart)."""
    try:
        tg = TelegramUser.query.filter_by(chat_id=str(chat_id)).first()
        if not tg:
            return jsonify({
                'success': False,
                'error': {'code': 'NOT_FOUND', 'message': 'Not linked'}
            }), 404

        user = User.query.get(tg.user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': {'code': 'NOT_FOUND', 'message': 'User not found'}
            }), 404

        return jsonify({'success': True, 'phone': user.phone}), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'SERVER_ERROR', 'message': str(e)}
        }), 500


@bp.route('/bot/cart', methods=['GET'])
def bot_get_cart():
    auth_error = verify_bot_secret()
    if auth_error:
        return auth_error
    try:
        phone = request.args.get('phone', '').strip()
        user = User.query.filter_by(phone=phone).first()
        if not user:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'User not found'}}), 404
        rows = BotCart.query.filter_by(user_id=user.id).all()
        items = []
        total = 0
        for row in rows:
            product = Product.query.get(row.product_id)
            if not product:
                continue
            line = int(product.selling_price) * int(row.quantity)
            total += line
            items.append({
                'product_id': product.id,
                'name': product.name,
                'price': product.selling_price / 100,
                'quantity': row.quantity,
                'line_total': line / 100
            })
        return jsonify({'success': True, 'items': items, 'total': total / 100}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/bot/cart', methods=['POST'])
def bot_add_cart():
    auth_error = verify_bot_secret()
    if auth_error:
        return auth_error
    try:
        data = request.get_json() or {}
        phone = data.get('phone', '').strip()
        product_id = int(data.get('product_id'))
        quantity = max(int(data.get('quantity', 1)), 1)
        user = User.query.filter_by(phone=phone).first()
        if not user:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'User not found'}}), 404
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Product not found'}}), 404
        row = BotCart.query.filter_by(user_id=user.id, product_id=product_id).first()
        if row:
            row.quantity += quantity
        else:
            db.session.add(BotCart(user_id=user.id, product_id=product_id, quantity=quantity))
        db.session.commit()
        return jsonify({'success': True}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/bot/cart', methods=['DELETE'])
def bot_clear_cart():
    auth_error = verify_bot_secret()
    if auth_error:
        return auth_error
    try:
        phone = request.args.get('phone', '').strip()
        user = User.query.filter_by(phone=phone).first()
        if not user:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'User not found'}}), 404
        BotCart.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/bot/unsubscribe', methods=['POST'])
def bot_unsubscribe():
    auth_error = verify_bot_secret()
    if auth_error:
        return auth_error
    try:
        data = request.get_json() or {}
        chat_id = str(data.get('chat_id', '')).strip()
        tg = TelegramUser.query.filter_by(chat_id=chat_id).first()
        if not tg:
            return jsonify({'success': True}), 200
        tg.chat_id = f'unsubscribed:{chat_id}'
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/link-telegram', methods=['POST'])
def link_telegram():
    """Link a Telegram chat_id to a user account (called by the bot after /start)."""
    auth_error = verify_bot_secret()
    if auth_error:
        return auth_error

    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        chat_id = str(data.get('chat_id', '')).strip()

        if not phone or not chat_id:
            return jsonify({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': 'phone and chat_id required'}
            }), 400

        user = User.query.filter_by(phone=phone).first()
        if not user:
            return jsonify({
                'success': False,
                'error': {'code': 'NOT_FOUND', 'message': 'User not found'}
            }), 404

        existing = TelegramUser.query.filter_by(user_id=user.id).first()
        if existing:
            existing.chat_id = chat_id
            existing.phone = phone
        else:
            by_chat = TelegramUser.query.filter_by(chat_id=chat_id).first()
            if by_chat:
                by_chat.user_id = user.id
                by_chat.phone = phone
            else:
                db.session.add(TelegramUser(user_id=user.id, phone=phone, chat_id=chat_id))

        db.session.commit()
        return jsonify({'success': True, 'message': 'Telegram linked successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {'code': 'SERVER_ERROR', 'message': str(e)}
        }), 500


@bp.route('/<phone>', methods=['GET'])
def get_user(phone):
    """Get user by phone number"""
    try:
        if not validate_ethiopian_phone(phone):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid Ethiopian phone number format'
                }
            }), 400
        
        user = User.query.filter_by(phone=phone).first()
        
        if not user:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        referral_earnings_cents = db.session.query(func.sum(CreditTransaction.amount)).filter(
            CreditTransaction.user_id == user.id,
            CreditTransaction.transaction_type == 'referral_earned'
        ).scalar() or 0
        since = datetime.utcnow() - timedelta(days=365)
        referral_year_cents = db.session.query(func.sum(CreditTransaction.amount)).filter(
            CreditTransaction.user_id == user.id,
            CreditTransaction.transaction_type == 'referral_earned',
            CreditTransaction.created_at >= since,
        ).scalar() or 0
        try:
            max_cap = float(SiteSetting.get('max_referral_per_year', '2000') or 2000)
        except ValueError:
            max_cap = 2000.0

        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'phone': user.phone,
                'name': user.name,
                'credit_balance': user.credit_balance / 100,  # Convert cents to ETB
                'referral_code': user.referral_code,
                'total_referrals': user.total_referrals,
                'referral_earnings': referral_earnings_cents / 100,
                'referral_earned_this_year': referral_year_cents / 100,
                'referral_cap_per_year': max_cap,
                'referral_remaining_cap': max(max_cap - (referral_year_cents / 100), 0),
                'referral_reward_etb': Config.REFERRAL_REWARD_ETB,
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

@bp.route('', methods=['POST'])
def create_user():
    """Create new user or get existing"""
    try:
        data = request.get_json()
        phone = data.get('phone')
        referral_code = data.get('referral_code')
        
        if not phone:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Phone number is required'
                }
            }), 400
        
        if not validate_ethiopian_phone(phone):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid Ethiopian phone number format'
                }
            }), 400
        
        name = (data.get('name') or '').strip()

        # Check if user exists
        user = User.query.filter_by(phone=phone).first()
        if user:
            if name and not user.name:
                user.name = name
                db.session.commit()
            return jsonify({
                'success': True,
                'user': {
                    'id': user.id,
                    'phone': user.phone,
                    'name': user.name,
                    'credit_balance': user.credit_balance / 100,
                    'referral_code': user.referral_code,
                    'total_referrals': user.total_referrals,
                    'referral_earnings': (
                        (db.session.query(db.func.sum(CreditTransaction.amount)).filter(
                            CreditTransaction.user_id == user.id,
                            CreditTransaction.transaction_type == 'referral_earned'
                        ).scalar() or 0) / 100
                    )
                },
                'existing': True
            }), 200

        if not name or len(name) < 2:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Full name is required to register (at least 2 characters)'
                }
            }), 400
        
        # Validate referral code if provided
        referrer_id = None
        if referral_code:
            referrer = User.query.filter_by(referral_code=referral_code).first()
            if referrer:
                referrer_id = referrer.id
        
        # Create new user
        user = User(
            phone=phone,
            name=name,
            referral_code=generate_referral_code(),
            referred_by=referrer_id
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'phone': user.phone,
                'name': user.name,
                'credit_balance': 0,
                'referral_code': user.referral_code,
                'total_referrals': 0,
                'referral_earnings': 0
            },
            'existing': False
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

@bp.route('/<phone>/orders', methods=['GET'])
def get_user_orders(phone):
    """Get user's order history"""
    try:
        user = User.query.filter_by(phone=phone).first()
        
        if not user:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'orders': [{
                'id': o.id,
                'subtotal': o.subtotal / 100,
                'credit_used': o.credit_used / 100,
                'final_total': o.final_total / 100,
                'amount_paid': (o.amount_paid or 0) / 100,
                'remaining_amount': max((o.final_total or 0) - (o.amount_paid or 0), 0) / 100,
                'payment_status': o.payment_status,
                'payment_plan': o.payment_plan,
                'status': o.status,
                'delivery_status': o.delivery_status,
                'evidence_requested': bool(o.evidence_requested),
                'customer_note': o.customer_note,
                'created_at': o.created_at.isoformat()
            } for o in orders]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': str(e)
            }
        }), 500

@bp.route('/<phone>/refunds', methods=['GET'])
def get_user_refunds(phone):
    try:
        from backend.models import Refund
        user = User.query.filter_by(phone=phone).first()
        if not user:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'User not found'}}), 404

        refunds = (
            Refund.query.join(Order, Order.id == Refund.order_id)
            .filter(Order.user_id == user.id)
            .order_by(Refund.created_at.desc())
            .all()
        )
        return jsonify({
            'success': True,
            'refunds': [{
                'id': r.id,
                'order_id': r.order_id,
                'reason': r.reason,
                'status': r.status,
                'customer_visible_note': r.customer_visible_note,
                'evidence_requested': bool(r.evidence_requested),
                'additional_evidence_url': r.additional_evidence_url,
                'created_at': r.created_at.isoformat(),
            } for r in refunds],
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<phone>/requests', methods=['GET'])
def get_user_requests(phone):
    """Get user's demand requests"""
    try:
        user = User.query.filter_by(phone=phone).first()
        
        if not user:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        requests = Request.query.filter_by(user_id=user.id).order_by(Request.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'requests': [{
                'id': r.id,
                'image_url': r.image_url,
                'description': r.description,
                'budget': r.budget / 100 if r.budget else None,
                'quoted_price': r.quoted_price / 100 if r.quoted_price else None,
                'status': r.status,
                'admin_response_message': r.admin_response_message,
                'converted_order_id': r.converted_order_id,
                'created_at': r.created_at.isoformat(),
            } for r in requests]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': str(e)
            }
        }), 500