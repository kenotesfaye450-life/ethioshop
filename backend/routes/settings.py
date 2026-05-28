"""Public site settings and admin management."""
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from datetime import datetime, timedelta

from backend.extensions import db
from backend.models import SiteSetting
from backend.config import Config
from backend.utils.auth import require_auth

bp = Blueprint('settings', __name__, url_prefix='/api')

DEFAULT_ABOUT = {
    'owner_name': 'Keno Tesfaye',
    'owner_title': 'Founder, EthioShop',
    'owner_image_url': '',
    'owner_bio': 'Meet your trusted seller — quality products and honest service across Ethiopia.',
    'years_experience': '5+',
    'contact_phone': '0965806907',
    'social_telegram': 'https://t.me/ethioshopofficial',
    'social_facebook': 'https://www.facebook.com/profile.php?id=61590636471935',
}
DEFAULT_ANNOUNCEMENT = {
    'announcement_message': '',
    'announcement_active': 'false',
    'announcement_close_delay_seconds': '3',
    'announcement_display_seconds': '0',
}
DEFAULT_LANDING = {
    'owner_message': (
        'Welcome to EthioShop — honest prices, secure half-payment, and delivery you can confirm. '
        'We are building trusted online shopping for customers across Ethiopia.'
    ),
    'max_referral_per_year': '2000',
}


def _about_dict():
    return {
        'owner_name': SiteSetting.get('owner_name', DEFAULT_ABOUT['owner_name']),
        'owner_title': SiteSetting.get('owner_title', DEFAULT_ABOUT['owner_title']),
        'owner_image_url': SiteSetting.get('owner_image_url', DEFAULT_ABOUT['owner_image_url']),
        'owner_bio': SiteSetting.get('owner_bio', DEFAULT_ABOUT['owner_bio']),
        'years_experience': SiteSetting.get('years_experience', DEFAULT_ABOUT['years_experience']),
        'contact_phone': SiteSetting.get('contact_phone', DEFAULT_ABOUT['contact_phone']),
        'social_telegram': SiteSetting.get('social_telegram', DEFAULT_ABOUT['social_telegram']),
        'social_facebook': SiteSetting.get('social_facebook', DEFAULT_ABOUT['social_facebook']),
        'owner_message': SiteSetting.get('owner_message', DEFAULT_LANDING['owner_message']),
    }


def _announcement_dict():
    try:
        close_delay = int(SiteSetting.get('announcement_close_delay_seconds', '3') or 3)
    except ValueError:
        close_delay = 3
    try:
        display_seconds = int(SiteSetting.get('announcement_display_seconds', '0') or 0)
    except ValueError:
        display_seconds = 0
    return {
        'announcement_message': SiteSetting.get('announcement_message', DEFAULT_ANNOUNCEMENT['announcement_message']),
        'announcement_active': str(SiteSetting.get('announcement_active', DEFAULT_ANNOUNCEMENT['announcement_active'])).lower() in ('1', 'true', 'yes', 'on'),
        'announcement_close_delay_seconds': max(close_delay, 3),
        'announcement_display_seconds': max(display_seconds, 0),
    }


def _referral_settings_dict():
    try:
        cap = float(SiteSetting.get('max_referral_per_year', DEFAULT_LANDING['max_referral_per_year']) or 2000)
    except ValueError:
        cap = 2000.0
    return {
        'referral_reward_etb': Config.REFERRAL_REWARD_ETB,
        'request_reward_etb': float(SiteSetting.get('request_reward_etb', '20') or 20),
        'max_referral_per_year': cap,
    }


@bp.route('/settings/about', methods=['GET'])
def get_about():
    try:
        data = _about_dict()
        data.update(_referral_settings_dict())
        return jsonify({'success': True, 'about': data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/settings/landing', methods=['GET'])
def get_landing():
    """Public landing page content."""
    try:
        return jsonify({
            'success': True,
            'landing': {
                **_about_dict(),
                **_referral_settings_dict(),
            },
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/settings/announcement', methods=['GET'])
def get_announcement():
    try:
        return jsonify({'success': True, 'announcement': _announcement_dict()}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/admin/settings', methods=['GET'])
@require_auth
def get_admin_settings():
    try:
        merged = _about_dict()
        merged.update(_announcement_dict())
        merged.update(_referral_settings_dict())
        return jsonify({'success': True, 'settings': merged}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/admin/settings', methods=['PATCH'])
@require_auth
def update_settings():
    try:
        data = request.get_json() or {}
        allowed = (
            list(DEFAULT_ABOUT.keys())
            + list(DEFAULT_ANNOUNCEMENT.keys())
            + list(DEFAULT_LANDING.keys())
            + ['request_reward_etb']
        )
        for key in allowed:
            if key in data:
                if key == 'announcement_active':
                    SiteSetting.set(key, 'true' if bool(data[key]) else 'false')
                else:
                    SiteSetting.set(key, str(data[key] or ''))
        db.session.commit()
        merged = _about_dict()
        merged.update(_announcement_dict())
        merged.update(_referral_settings_dict())
        return jsonify({'success': True, 'settings': merged}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500
