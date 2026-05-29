"""Bot-only API routes (checkout from Telegram cart)."""
from math import ceil

from flask import Blueprint, jsonify, request

from config import Config
from extensions import db
from models import (
    BotCart,
    CreditTransaction,
    Order,
    OrderItem,
    Payment,
    Product,
    TelegramUser,
    User,
)
from routes.orders import calculate_max_credit
from utils.bot_auth import verify_bot_secret

bp = Blueprint('bot_api', __name__, url_prefix='/api/bot')


@bp.route('/checkout', methods=['POST'])
def bot_checkout():
    """Create order from bot cart. Protected by X-Bot-Secret."""
    auth_error = verify_bot_secret()
    if auth_error:
        return auth_error

    data = request.get_json() or {}
    chat_id = str(data.get('chat_id', '')).strip()
    delivery_location = data.get('delivery_location') or {}
    payment_plan = (data.get('payment_plan') or 'half').strip().lower()
    notes = (data.get('notes') or '').strip()

    if not chat_id:
        return jsonify({'success': False, 'message': 'chat_id required'}), 400

    if payment_plan not in ('half', 'full'):
        payment_plan = 'half'

    tg_user = TelegramUser.query.filter_by(chat_id=chat_id).first()
    if not tg_user:
        return jsonify({
            'success': False,
            'message': 'Telegram account not linked. Please use /start first.',
        }), 400

    user = User.query.get(tg_user.user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    cart_items = BotCart.query.filter_by(user_id=user.id).all()
    if not cart_items:
        return jsonify({
            'success': False,
            'message': 'Cart is empty. Use /add to add products.',
        }), 400

    order_items_data = []
    subtotal = 0

    try:
        for cart_item in cart_items:
            product = Product.query.filter_by(id=cart_item.product_id).with_for_update().first()
            if not product:
                return jsonify({
                    'success': False,
                    'message': f'Product {cart_item.product_id} not found',
                }), 400
            qty = int(cart_item.quantity)
            if int(product.stock) < qty:
                return jsonify({
                    'success': False,
                    'message': f'Insufficient stock for {product.name}',
                }), 400
            line_total = int(product.selling_price) * qty
            subtotal += line_total
            order_items_data.append({
                'product': product,
                'quantity': qty,
                'price': product.selling_price,
            })

        min_order = int(Config.MINIMUM_ORDER_ETB * 100)
        credit_used = calculate_max_credit(subtotal, user.credit_balance)
        final_total = subtotal - credit_used

        if final_total < min_order:
            return jsonify({
                'success': False,
                'message': (
                    f'Minimum order is {Config.MINIMUM_ORDER_ETB} ETB. '
                    f'Your total after credit is {final_total / 100:.2f} ETB.'
                ),
            }), 400

        if payment_plan == 'half':
            amount_paid = int(ceil(final_total / 2))
            payment_status = 'partial'
        else:
            amount_paid = final_total
            payment_status = 'pending'

        order = Order(
            user_id=user.id,
            subtotal=subtotal,
            credit_used=credit_used,
            final_total=final_total,
            payment_method='Telebirr',
            status='pending_verification',
            delivery_location=delivery_location,
            customer_note=notes or None,
            payment_plan=payment_plan,
            amount_paid=amount_paid,
            payment_status=payment_status,
        )
        db.session.add(order)
        db.session.flush()

        db.session.add(Payment(
            order_id=order.id,
            amount=amount_paid,
            payment_type='initial',
            status='pending',
        ))

        for item_data in order_items_data:
            db.session.add(OrderItem(
                order_id=order.id,
                product_id=item_data['product'].id,
                quantity=item_data['quantity'],
                price_at_purchase=item_data['price'],
            ))
            item_data['product'].stock -= item_data['quantity']

        if credit_used > 0:
            user.credit_balance -= credit_used
            db.session.add(CreditTransaction(
                user_id=user.id,
                amount=-credit_used,
                transaction_type='order_used',
                related_order_id=order.id,
            ))

        BotCart.query.filter_by(user_id=user.id).delete()
        db.session.commit()

        return jsonify({
            'success': True,
            'order_id': order.id,
            'final_total_etb': final_total / 100,
            'credit_used_etb': credit_used / 100,
            'payment_plan': payment_plan,
            'amount_paid_etb': amount_paid / 100,
            'message': f'Order #{order.id} created. Upload payment proof via /pay {order.id}',
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
