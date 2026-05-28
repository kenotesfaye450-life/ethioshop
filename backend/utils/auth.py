"""
Centralized auth decorator — replaces the copy-pasted require_auth in every route file.

Usage:
    from utils.auth import require_auth, require_role

    @bp.route('/something')
    @require_auth
    def my_view():
        # request.admin_id and request.admin_role are set
        ...

    @bp.route('/admin-only')
    @require_auth
    @require_role('super_admin')
    def admin_only():
        ...

    @bp.route('/staff-or-admin')
    @require_auth
    @require_role(['super_admin', 'warehouse_staff'])
    def staff_view():
        ...
"""
from functools import wraps
from flask import request, jsonify
import jwt
from backend.config import Config


def require_auth(f):
    """Validate JWT token and attach admin_id + admin_role to request."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()

        if not token:
            return jsonify({
                'success': False,
                'error': {'code': 'AUTH_REQUIRED', 'message': 'Authentication required'}
            }), 401

        try:
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            request.admin_id   = payload['admin_id']
            request.admin_role = payload['role']
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'error': {'code': 'TOKEN_EXPIRED', 'message': 'Token has expired'}
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'error': {'code': 'INVALID_TOKEN', 'message': 'Invalid token'}
            }), 401

        return f(*args, **kwargs)
    return decorated


def require_role(roles):
    """
    Role-check decorator. Must be applied AFTER @require_auth.
    roles: str or list of str — allowed roles.
    Pass '*' to allow any authenticated admin.
    """
    if isinstance(roles, str):
        roles = [roles]

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if '*' not in roles and request.admin_role not in roles:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INSUFFICIENT_PERMISSIONS',
                        'message': f'Required role: {", ".join(roles)}'
                    }
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
