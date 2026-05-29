"""Demand request routes"""
from flask import Blueprint, request, jsonify
from extensions import db
from models import Request, User, Order, Product, ProductImage, CreditTransaction, SiteSetting
from config import Config
from utils.auth import require_auth, require_role
from services.image_service import ImageService

bp = Blueprint('requests', __name__, url_prefix='/api/requests')


def _cloudinary_public_id_from_url(url: str | None) -> str | None:
    if not url or '/upload/' not in url:
        return None
    tail = url.split('/upload/', 1)[1]
    parts = tail.split('/')
    while parts and (parts[0].startswith('v') and parts[0][1:].isdigit() or ',' in parts[0]):
        parts = parts[1:]
    if not parts:
        return None
    path = '/'.join(parts)
    if '.' in path:
        path = path.rsplit('.', 1)[0]
    return path


@bp.route('', methods=['POST'])
def create_request():
    try:
        data = request.get_json()
        missing = [f for f in ['phone', 'image_url', 'description'] if f not in data]
        if missing:
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': f'Missing: {", ".join(missing)}'}}), 400

        user = User.query.filter_by(phone=data['phone']).first()
        if not user:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'User not found. Register first.'}}), 404

        demand_request = Request(
            user_id=user.id,
            image_url=data['image_url'],
            description=data['description'],
            budget=int(float(data['budget']) * 100) if data.get('budget') else None,
            delivery_location=data.get('delivery_location'),
            status='pending_sourcing'
        )
        db.session.add(demand_request)
        db.session.commit()
        return jsonify({'success': True, 'request': {'id': demand_request.id, 'status': demand_request.status, 'description': demand_request.description}}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('', methods=['GET'])
@require_auth
def get_requests():
    """Paginated requests list (admin). Returns { items, page, pages, total }."""
    try:
        status = request.args.get('status')
        page   = request.args.get('page', 1, type=int)
        limit  = min(request.args.get('limit', request.args.get('per_page', 20), type=int), 100)

        query = Request.query
        if status:
            query = query.filter(Request.status == status)

        paginated = query.order_by(Request.created_at.desc()).paginate(page=page, per_page=limit, error_out=False)

        items = [{
            'id':           r.id,
            'user_phone':   r.user.phone,
            'image_url':    r.image_url,
            'description':  r.description,
            'budget':       r.budget / 100 if r.budget else None,
            'quoted_price': r.quoted_price / 100 if r.quoted_price else None,
            'status':       r.status,
            'admin_response_message': r.admin_response_message,
            'created_at':   r.created_at.isoformat(),
            'updated_at':   r.created_at.isoformat(),
        } for r in paginated.items]

        return jsonify({
            'success':  True,
            'items':    items,
            'requests': items,  # legacy alias
            'page':     paginated.page,
            'pages':    paginated.pages,
            'total':    paginated.total
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:request_id>', methods=['GET'])
def get_request(request_id):
    try:
        r = Request.query.get(request_id)
        if not r:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': f'Request {request_id} not found'}}), 404
        return jsonify({'success': True, 'request': {
            'id': r.id, 'user_phone': r.user.phone, 'image_url': r.image_url,
            'description': r.description,
            'budget':       r.budget / 100 if r.budget else None,
            'quoted_price': r.quoted_price / 100 if r.quoted_price else None,
            'status': r.status, 'delivery_location': r.delivery_location,
            'created_at': r.created_at.isoformat()
        }}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:request_id>/quote', methods=['PATCH'])
@require_auth
def quote_price(request_id):
    try:
        data = request.get_json()
        quoted_price = data.get('quoted_price')
        if not quoted_price:
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'quoted_price required'}}), 400

        r = Request.query.get(request_id)
        if not r:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': f'Request {request_id} not found'}}), 404

        if float(quoted_price) > 10000 and request.admin_role != 'super_admin':
            return jsonify({'success': False, 'error': {'code': 'INSUFFICIENT_PERMISSIONS', 'message': 'Prices above 10000 ETB require super_admin'}}), 403

        r.quoted_price = int(float(quoted_price) * 100)
        r.status = 'price_quoted'
        if data.get('admin_message') or data.get('admin_response_message'):
            r.admin_response_message = (data.get('admin_message') or data.get('admin_response_message') or '').strip()
        db.session.commit()

        try:
            from services.telegram_service import NotificationService
            NotificationService.notify_request_quote(r)
        except Exception as e:
            print(f"Notification error: {e}")

        return jsonify({'success': True, 'request': {'id': r.id, 'quoted_price': r.quoted_price / 100, 'status': r.status}}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:request_id>/reject', methods=['PATCH'])
@require_auth
def reject_request(request_id):
    try:
        r = Request.query.get(request_id)
        if not r:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': f'Request {request_id} not found'}}), 404
        data = request.get_json() or {}
        r.status = 'rejected'
        if data.get('admin_message') or data.get('admin_response_message'):
            r.admin_response_message = (data.get('admin_message') or data.get('admin_response_message') or '').strip()
        if data.get('delete_image'):
            pid = _cloudinary_public_id_from_url(r.image_url)
            if pid:
                try:
                    ImageService.delete_image(pid)
                except Exception:
                    pass
        db.session.commit()
        try:
            from services.telegram_service import NotificationService
            NotificationService.notify_request_rejected(r)
        except Exception as e:
            print(f"Notification error: {e}")
        return jsonify({'success': True, 'request': {'id': r.id, 'status': r.status}}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:request_id>/convert', methods=['POST'])
def convert_to_order(request_id):
    try:
        data = request.get_json() or {}
        phone = data.get('phone', '').strip()
        if not phone:
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'phone is required'}}), 400

        r = Request.query.get(request_id)
        if not r:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': f'Request {request_id} not found'}}), 404

        if not r.user or r.user.phone != phone:
            return jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'Request does not belong to this phone number'}}), 403

        if r.status != 'price_quoted':
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Request must have a quoted price first'}}), 400

        order = Order(
            user_id=r.user_id, subtotal=r.quoted_price, credit_used=0,
            final_total=r.quoted_price,
            payment_method=data.get('payment_method', 'Bank Transfer'),
            delivery_location=r.delivery_location, status='pending_verification'
        )
        db.session.add(order)
        db.session.flush()
        r.converted_order_id = order.id
        r.status = 'converted'
        db.session.commit()
        return jsonify({'success': True, 'order': {'id': order.id, 'final_total': order.final_total / 100, 'status': order.status}}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:request_id>/convert-to-product', methods=['POST'])
@require_auth
def convert_to_product(request_id):
    """Admin converts a request into a product draft."""
    try:
        r = Request.query.get(request_id)
        if not r:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Request not found'}}), 404
        data = request.get_json() or {}
        category = (data.get('category') or data.get('custom_category') or 'Uncategorized').strip()
        name = (data.get('name') or r.description or 'Requested Product').strip()[:100]
        product = Product(
            name=name,
            description=data.get('description') or r.description,
            category=category,
            selling_price=int(float(data.get('selling_price', 0)) * 100),
            cost_price=int(float(data.get('cost_price', 0)) * 100),
            stock=int(data.get('stock', 1)),
            image_url=r.image_url,
            thumbnail_url=r.image_url,
        )
        db.session.add(product)
        db.session.flush()
        if r.image_url:
            db.session.add(ProductImage(
                product_id=product.id,
                image_url=r.image_url,
                thumbnail_url=r.image_url,
                is_primary=True,
                sort_order=0
            ))
        if data.get('mark_converted', True):
            r.status = 'converted'
        reward_etb = float(data.get('request_reward_etb') or SiteSetting.get('request_reward_etb', '20') or 20)
        reward_cents = int(reward_etb * 100)
        requester = User.query.get(r.user_id)
        if requester and not r.request_credit_awarded and reward_cents > 0:
            requester.credit_balance += reward_cents
            r.request_credit_awarded = True
            db.session.add(CreditTransaction(
                user_id=requester.id,
                amount=reward_cents,
                transaction_type='request_reward',
            ))
            try:
                from services.telegram_service import NotificationService
                NotificationService.notify_request_credit_awarded(requester, reward_etb, product.name)
            except Exception as e:
                print(f"Notification error: {e}")
        if data.get('delete_request_image'):
            pid = _cloudinary_public_id_from_url(r.image_url)
            if pid:
                try:
                    ImageService.delete_image(pid)
                except Exception:
                    pass
        db.session.commit()
        return jsonify({'success': True, 'product': {'id': product.id, 'name': product.name}, 'request': {'id': r.id, 'status': r.status}}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500
