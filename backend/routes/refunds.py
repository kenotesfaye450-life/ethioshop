"""Refund routes"""
from flask import Blueprint, request, jsonify
from extensions import db
from models import Refund, Order, User, CreditTransaction, Product, OrderMessage
from utils.auth import require_auth

bp = Blueprint('refunds', __name__, url_prefix='/api/refunds')


def _refund_dict(r, include_order=False):
    data = {
        'id': r.id,
        'order_id': r.order_id,
        'reason': r.reason,
        'status': r.status,
        'admin_notes': r.admin_notes,
        'customer_visible_note': r.customer_visible_note,
        'evidence_requested': bool(r.evidence_requested),
        'additional_evidence_url': r.additional_evidence_url,
        'created_at': r.created_at.isoformat(),
    }
    if include_order and r.order:
        data['order_status'] = r.order.status
        data['order_total'] = r.order.final_total / 100
    return data


@bp.route('', methods=['POST'])
def create_refund():
    try:
        data = request.get_json()
        missing = [f for f in ['order_id', 'reason', 'phone'] if f not in data]
        if missing:
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': f'Missing: {", ".join(missing)}'}}), 400

        order = Order.query.get(data['order_id'])
        if not order:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Order not found'}}), 404

        if not order.user or order.user.phone != data['phone'].strip():
            return jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'Order does not belong to this phone number'}}), 403

        if order.status not in ['confirmed', 'delivered']:
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Only confirmed or delivered orders can be refunded'}}), 400

        if Refund.query.filter_by(order_id=order.id).first():
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Refund already exists for this order'}}), 400

        refund = Refund(order_id=order.id, reason=data['reason'], status='pending_review')
        db.session.add(refund)
        db.session.commit()
        return jsonify({'success': True, 'refund': _refund_dict(refund)}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('', methods=['GET'])
@require_auth
def get_refunds():
    try:
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        limit = min(request.args.get('limit', request.args.get('per_page', 20), type=int), 100)

        query = Refund.query
        if status:
            query = query.filter(Refund.status == status)

        paginated = query.order_by(Refund.created_at.desc()).paginate(page=page, per_page=limit, error_out=False)
        items = [_refund_dict(r, include_order=True) for r in paginated.items]

        return jsonify({
            'success': True,
            'items': items,
            'refunds': items,
            'page': paginated.page,
            'pages': paginated.pages,
            'total': paginated.total,
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:refund_id>', methods=['GET'])
def get_refund(refund_id):
    try:
        phone = request.args.get('phone', '').strip()
        refund = Refund.query.get(refund_id)
        if not refund:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Refund not found'}}), 404
        if phone and (not refund.order or not refund.order.user or refund.order.user.phone != phone):
            return jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'Access denied'}}), 403
        return jsonify({'success': True, 'refund': _refund_dict(refund, include_order=True)}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:refund_id>/process', methods=['PATCH'])
@require_auth
def process_refund(refund_id):
    try:
        data = request.get_json() or {}
        approved = data.get('approved', False)
        admin_notes = data.get('admin_notes', '')
        customer_visible_note = data.get('customer_visible_note') or admin_notes

        refund = Refund.query.get(refund_id)
        if not refund:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': f'Refund {refund_id} not found'}}), 404

        order = Order.query.get(refund.order_id)

        if approved and order.final_total > 500000 and request.admin_role != 'super_admin':
            return jsonify({'success': False, 'error': {'code': 'INSUFFICIENT_PERMISSIONS', 'message': 'Refunds above 5000 ETB require super_admin'}}), 403

        if approved:
            refund.status = 'approved'
            refund.approved_by = request.admin_id
            order.status = 'refunded'

            user = User.query.get(order.user_id)
            user.credit_balance += order.final_total
            db.session.add(CreditTransaction(
                user_id=user.id, amount=order.final_total,
                transaction_type='refund_restored', related_order_id=order.id,
            ))
            for item in order.items:
                product = Product.query.get(item.product_id)
                if product:
                    product.stock += item.quantity
        else:
            refund.status = 'rejected'

        refund.admin_notes = admin_notes
        refund.customer_visible_note = customer_visible_note
        db.session.commit()

        try:
            from services.telegram_service import NotificationService
            NotificationService.notify_refund_update(refund, order)
            NotificationService.notify_order_status_change(order)
        except Exception as e:
            print(f"Notification error: {e}")

        return jsonify({'success': True, 'refund': _refund_dict(refund)}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:refund_id>/request-evidence', methods=['PATCH'])
@require_auth
def request_refund_evidence(refund_id):
    try:
        data = request.get_json() or {}
        note = data.get('note') or data.get('customer_visible_note') or ''

        refund = Refund.query.get(refund_id)
        if not refund:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Refund not found'}}), 404

        refund.evidence_requested = True
        refund.customer_visible_note = note
        db.session.commit()

        try:
            from services.telegram_service import NotificationService
            NotificationService.notify_evidence_requested(refund=refund, note=note)
        except Exception as e:
            print(f"Notification error: {e}")

        return jsonify({'success': True, 'refund': _refund_dict(refund)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:refund_id>/upload-evidence', methods=['PATCH'])
def upload_refund_evidence(refund_id):
    try:
        data = request.get_json() or {}
        phone = data.get('phone', '').strip()
        url = data.get('additional_evidence_url') or data.get('evidence_url')
        if not phone or not url:
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'phone and evidence url required'}}), 400

        refund = Refund.query.get(refund_id)
        if not refund or not refund.order or not refund.order.user or refund.order.user.phone != phone:
            return jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'Access denied'}}), 403

        refund.additional_evidence_url = url
        refund.evidence_requested = False
        db.session.commit()
        return jsonify({'success': True, 'refund': _refund_dict(refund)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:refund_id>/messages', methods=['POST'])
@require_auth
def admin_refund_message(refund_id):
    """Admin posts a message visible to customer on the refund thread (via order messages)."""
    try:
        data = request.get_json() or {}
        message = (data.get('message') or data.get('customer_visible_note') or '').strip()
        if not message:
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'message required'}}), 400

        refund = Refund.query.get(refund_id)
        if not refund:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Refund not found'}}), 404

        refund.customer_visible_note = message
        db.session.add(OrderMessage(order_id=refund.order_id, sender_type='admin', message=message))
        db.session.commit()
        return jsonify({'success': True, 'refund': _refund_dict(refund)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500
