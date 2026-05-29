from flask import Blueprint, request, jsonify
import bcrypt
import jwt
from sqlalchemy import func
from datetime import datetime, timedelta

from extensions import db
from models import (
    Admin, Order, User, Refund, Request, Referral,
    OrderItem, Product, CreditTransaction, ProductImage, SiteSetting,
    ProductQuestion, AdminAction,
)
from config import Config
from utils.auth import require_auth, require_role
from utils.bot_auth import verify_bot_secret

bp = Blueprint('admin', __name__, url_prefix='/api/admin')


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


@bp.route('/login', methods=['POST'])
def login():
    """Admin login — requires username + phone + password."""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        phone = data.get('phone', '').strip()
        password = data.get('password', '')

        if not username or not phone or not password:
            return jsonify({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': 'username, phone, and password are required'}
            }), 400

        admin = Admin.query.filter_by(username=username, phone=phone).first()
        if not admin or not bcrypt.checkpw(password.encode(), admin.password_hash.encode()):
            return jsonify({
                'success': False,
                'error': {'code': 'AUTH_FAILED', 'message': 'Invalid credentials'}
            }), 401

        token = jwt.encode({
            'admin_id': admin.id,
            'username': admin.username,
            'phone': admin.phone,
            'role': admin.role,
            'exp': datetime.utcnow() + timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)
        }, Config.JWT_SECRET_KEY, algorithm='HS256')

        return jsonify({
            'success': True,
            'token': token,
            'admin': {
                'id': admin.id,
                'username': admin.username,
                'phone': admin.phone,
                'role': admin.role
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/orders', methods=['GET'])
@require_auth
def get_all_orders():
    """Paginated orders list. Returns { items, page, pages, total }."""
    try:
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        limit = min(request.args.get('limit', request.args.get('per_page', 20), type=int), 100)

        query = Order.query
        if status:
            query = query.filter(Order.status == status)

        paginated = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=limit, error_out=False)

        items = [{
            'id': o.id,
            'user_phone': o.user.phone if o.user else 'unknown',
            'subtotal': o.subtotal / 100,
            'credit_used': o.credit_used / 100,
            'final_total': o.final_total / 100,
            'amount_paid': (o.amount_paid or 0) / 100,
            'remaining_amount': max((o.final_total or 0) - (o.amount_paid or 0), 0) / 100,
            'payment_status': o.payment_status,
            'payment_plan': o.payment_plan,
            'status': o.status,
            'delivery_status': o.delivery_status,
            'payment_method': o.payment_method,
            'payment_proof_url': o.payment_proof_url,
            'created_at': o.created_at.isoformat(),
            'items_count': len(o.items)
        } for o in paginated.items]

        return jsonify({
            'success': True,
            'items': items,
            'orders': items,
            'page': paginated.page,
            'pages': paginated.pages,
            'total': paginated.total
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/users', methods=['POST'])
@require_auth
@require_role('super_admin')
def create_admin():
    """Create admin account (super_admin only)."""
    try:
        data = request.get_json()
        required = ['username', 'phone', 'password', 'role']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': f'Missing: {", ".join(missing)}'}
            }), 400

        valid_roles = ['super_admin', 'warehouse_staff', 'verifier', 'support_agent']
        if data['role'] not in valid_roles:
            return jsonify({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': f'Role must be one of: {", ".join(valid_roles)}'}
            }), 400

        if Admin.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Username already exists'}}), 400
        if Admin.query.filter_by(phone=data['phone']).first():
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Phone already exists'}}), 400

        admin = Admin(
            username=data['username'],
            phone=data['phone'],
            password_hash=bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt(12)).decode(),
            role=data['role'],
            created_by=request.admin_id
        )
        db.session.add(admin)
        db.session.commit()
        return jsonify({
            'success': True,
            'admin': {'id': admin.id, 'username': admin.username, 'phone': admin.phone, 'role': admin.role}
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/users', methods=['GET'])
@require_auth
def get_admins():
    try:
        admins = Admin.query.order_by(Admin.created_at.desc()).all()
        return jsonify({
            'success': True,
            'admins': [
                {
                    'id': a.id,
                    'username': a.username,
                    'phone': a.phone,
                    'role': a.role,
                    'created_at': a.created_at.isoformat()
                }
                for a in admins
            ]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/stats', methods=['GET'])
@require_auth
def get_stats():
    """Analytics: sales, pending, daily orders, top products, referral stats."""
    try:
        total_sales = db.session.query(func.sum(Order.final_total)).filter(
            Order.status.in_(['confirmed', 'delivered'])
        ).scalar() or 0

        pending_count = Order.query.filter_by(status='pending_verification').count()
        total_orders = Order.query.count()

        since_24h = datetime.utcnow() - timedelta(hours=24)
        daily_orders = Order.query.filter(Order.created_at >= since_24h).count()

        recent = Order.query.order_by(Order.created_at.desc()).limit(10).all()
        recent_list = [{
            'id': o.id,
            'user_phone': o.user.phone if o.user else 'unknown',
            'final_total': o.final_total / 100,
            'status': o.status,
            'delivery_status': o.delivery_status,
            'created_at': o.created_at.isoformat()
        } for o in recent]

        top_products = (
            db.session.query(
                Product.id, Product.name,
                func.sum(OrderItem.quantity).label('total_sold')
            )
            .join(OrderItem, OrderItem.product_id == Product.id)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.status.in_(['confirmed', 'delivered']))
            .group_by(Product.id, Product.name)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(5)
            .all()
        )

        referral_count = Referral.query.count()
        referral_credit = db.session.query(func.sum(Referral.credit_awarded)).scalar() or 0

        approved_refunds = Refund.query.filter_by(status='approved').all()
        refund_count = len(approved_refunds)
        total_refunded = sum(r.order.final_total for r in approved_refunds if r.order)

        return jsonify({
            'success': True,
            'stats': {
                'total_sales_etb': total_sales / 100,
                'total_orders': total_orders,
                'pending_orders': pending_count,
                'daily_orders': daily_orders,
                'recent_orders': recent_list,
                'top_products': [
                    {'id': r.id, 'name': r.name, 'total_sold': int(r.total_sold)}
                    for r in top_products
                ],
                'referrals': {
                    'count': referral_count,
                    'total_credit_etb': referral_credit / 100
                },
                'refunds': {
                    'count': refund_count,
                    'total_refunded_etb': total_refunded / 100
                }
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/referral-stats', methods=['GET'])
@require_auth
def get_referral_stats():
    try:
        referral_count = Referral.query.count()
        referral_credit = db.session.query(func.sum(Referral.credit_awarded)).scalar() or 0
        top = (
            db.session.query(
                User.id, User.phone, User.name,
                func.count(Referral.id).label('referral_count')
            )
            .join(Referral, Referral.referrer_id == User.id)
            .group_by(User.id, User.phone, User.name)
            .order_by(func.count(Referral.id).desc())
            .limit(5)
            .all()
        )
        return jsonify({
            'success': True,
            'stats': {
                'total_referrals': referral_count,
                'total_credit_etb': referral_credit / 100,
                'top_referrers': [
                    {'user_id': r.id, 'phone': r.phone, 'name': r.name, 'count': int(r.referral_count)}
                    for r in top
                ],
            },
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/bot/stats', methods=['GET'])
def bot_stats():
    auth_error = verify_bot_secret()
    if auth_error:
        return auth_error
    try:
        today = datetime.utcnow().date()
        start = datetime(today.year, today.month, today.day)
        total_sales = db.session.query(func.sum(Order.final_total)).filter(
            Order.status.in_(['confirmed', 'delivered']),
            Order.created_at >= start
        ).scalar() or 0
        pending = Order.query.filter_by(status='pending_verification').count()
        return jsonify({'success': True, 'stats': {'total_sales_today_etb': total_sales / 100, 'pending_orders': pending}}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/bot/pending', methods=['GET'])
def bot_pending():
    auth_error = verify_bot_secret()
    if auth_error:
        return auth_error
    try:
        pending = Order.query.filter_by(status='pending_verification').order_by(Order.created_at.desc()).limit(20).all()
        return jsonify({'success': True, 'order_ids': [o.id for o in pending]}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/pending-orders', methods=['GET'])
@require_auth
def get_pending_orders():
    try:
        pending = Order.query.filter_by(status='pending_verification').order_by(Order.created_at.desc()).limit(20).all()
        return jsonify({
            'success': True,
            'orders': [{'id': o.id, 'user_phone': o.user.phone if o.user else None, 'created_at': o.created_at.isoformat()} for o in pending]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/questions', methods=['GET'])
@require_auth
def list_product_questions():
    try:
        status = request.args.get('status', 'pending')
        q = ProductQuestion.query
        if status != 'all':
            q = q.filter_by(status=status)
        rows = q.order_by(ProductQuestion.created_at.desc()).limit(100).all()
        items = []
        for pq in rows:
            items.append({
                'id': pq.id,
                'user_id': pq.user_id,
                'user_phone': pq.user.phone if pq.user else None,
                'user_name': pq.user.name if pq.user else None,
                'product_id': pq.product_id,
                'product_name': pq.product.name if pq.product else None,
                'question': pq.question,
                'answer': pq.answer,
                'status': pq.status,
                'created_at': pq.created_at.isoformat(),
                'answered_at': pq.answered_at.isoformat() if pq.answered_at else None,
            })
        return jsonify({'success': True, 'questions': items}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/questions/<int:question_id>/answer', methods=['POST'])
@require_auth
def answer_product_question(question_id):
    try:
        data = request.get_json() or {}
        answer = (data.get('answer') or '').strip()
        if not answer:
            return jsonify({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': 'answer is required'},
            }), 400

        pq = ProductQuestion.query.get(question_id)
        if not pq:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Question not found'}}), 404

        pq.answer = answer
        pq.status = 'answered'
        pq.answered_at = datetime.utcnow()
        db.session.commit()

        from services.telegram_service import NotificationService
        NotificationService.notify_product_question_answered(pq)

        return jsonify({'success': True, 'question': {'id': pq.id, 'status': pq.status}}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/cleanup', methods=['POST'])
@require_auth
@require_role(['super_admin'])
def admin_cleanup():
    """Preview or execute cleanup actions."""
    try:
        data = request.get_json() or {}
        action = data.get('action')
        execute = bool(data.get('execute', False))
        if action not in ('test_orders', 'unconfirmed_users'):
            return jsonify({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': 'Invalid action'},
            }), 400

        admin_id = getattr(request, 'admin_id', None)
        count = 0

        if action == 'test_orders':
            cutoff = datetime.utcnow() - timedelta(days=7)
            q = Order.query.filter(
                Order.status == 'pending_verification',
                Order.created_at < cutoff,
            )
            count = q.count()
            if execute:
                deleted = q.delete(synchronize_session=False)
                db.session.add(AdminAction(
                    admin_id=admin_id,
                    action_type='cleanup_test_orders',
                    details=f'Deleted pending_verification orders older than 7 days',
                    records_affected=deleted,
                ))
                db.session.commit()
                count = deleted
        elif action == 'unconfirmed_users':
            cutoff = datetime.utcnow() - timedelta(days=30)
            users = User.query.filter(User.created_at < cutoff).all()
            to_delete = []
            for u in users:
                has_order = Order.query.filter_by(user_id=u.id).first()
                if not has_order:
                    to_delete.append(u)
            count = len(to_delete)
            if execute:
                for u in to_delete:
                    db.session.delete(u)
                db.session.add(AdminAction(
                    admin_id=admin_id,
                    action_type='cleanup_unconfirmed_users',
                    details='Deleted users with no orders older than 30 days',
                    records_affected=count,
                ))
                db.session.commit()

        return jsonify({
            'success': True,
            'action': action,
            'count': count,
            'executed': execute,
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/storage/cleanup', methods=['POST'])
@require_auth
@require_role(['super_admin', 'support_agent'])
def storage_cleanup():
    """Scan db-referenced image URLs and optionally delete orphan cloudinary assets."""
    try:
        data = request.get_json() or {}
        do_delete = bool(data.get('delete', False))
        prefix = (data.get('prefix') or '').strip()  # optional folder prefix

        referenced = set()
        for url in [x.image_url for x in ProductImage.query.all()]:
            pid = _cloudinary_public_id_from_url(url)
            if pid:
                referenced.add(pid)
        for url in [x.image_url for x in Request.query.all() if x.image_url]:
            pid = _cloudinary_public_id_from_url(url)
            if pid:
                referenced.add(pid)
        for o in Order.query.all():
            for url in [o.payment_proof_url, o.additional_proof_url]:
                pid = _cloudinary_public_id_from_url(url)
                if pid:
                    referenced.add(pid)
        for r in Refund.query.all():
            pid = _cloudinary_public_id_from_url(r.additional_evidence_url)
            if pid:
                referenced.add(pid)
        owner_image = SiteSetting.get('owner_image_url')
        pid = _cloudinary_public_id_from_url(owner_image)
        if pid:
            referenced.add(pid)

        usage = {}
        orphans = []
        try:
            import cloudinary.api
            kwargs = {'max_results': 500}
            if prefix:
                kwargs['prefix'] = prefix
            resources = cloudinary.api.resources(**kwargs).get('resources', [])
            usage = cloudinary.api.usage()
            for r in resources:
                pid = r.get('public_id')
                if pid and pid not in referenced:
                    orphans.append({'public_id': pid, 'bytes': r.get('bytes', 0), 'url': r.get('secure_url')})
            if do_delete and orphans:
                from services.image_service import ImageService
                for o in orphans:
                    try:
                        ImageService.delete_image(o['public_id'])
                    except Exception:
                        pass
        except Exception as e:
            return jsonify({
                'success': False,
                'error': {'code': 'SERVER_ERROR', 'message': f'Cloudinary API error: {e}'},
                'referenced_count': len(referenced),
            }), 500

        return jsonify({
            'success': True,
            'referenced_count': len(referenced),
            'orphans': orphans,
            'orphans_count': len(orphans),
            'deleted': do_delete,
            'usage': {
                'storage': usage.get('storage', {}) if isinstance(usage, dict) else {},
                'transformations': usage.get('transformations', {}) if isinstance(usage, dict) else {},
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


