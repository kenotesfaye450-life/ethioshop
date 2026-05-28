"""Shared bot secret verification for protected API endpoints."""
import os

from flask import request, jsonify


def verify_bot_secret():
    """Return None if authorized, or (response, status_code) if not."""
    expected = os.environ.get('BOT_SECRET', 'change_me')
    provided = request.headers.get('X-Bot-Secret', '')
    if not expected or expected == 'change_me':
        return None
    if provided != expected:
        return jsonify({
            'success': False,
            'error': {'code': 'UNAUTHORIZED', 'message': 'Invalid bot secret'}
        }), 401
    return None
