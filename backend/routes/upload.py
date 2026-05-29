"""Image upload routes"""
from flask import Blueprint, request, jsonify
from config import Config
from services.image_service import ImageService

bp = Blueprint('upload', __name__, url_prefix='/api/upload')

@bp.route('/image', methods=['POST'])
def upload_image():
    """Upload image endpoint"""
    try:
        if 'file' not in request.files and not request.is_json:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'No image provided'
                }
            }), 400

        folder = request.form.get('folder', 'general')

        if 'file' in request.files:
            file = request.files['file']
            extension = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
            if extension not in Config.ALLOWED_IMAGE_EXTENSIONS:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': f'Invalid file type. Allowed: {", ".join(sorted(Config.ALLOWED_IMAGE_EXTENSIONS))}'
                    }
                }), 400

            file.seek(0, 2)
            size = file.tell()
            file.seek(0)

            if size > Config.UPLOAD_MAX_SIZE:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': f'File size exceeds {Config.UPLOAD_MAX_SIZE // (1024 * 1024)}MB limit'
                    }
                }), 400

            result = ImageService.upload_image(file, folder)

        elif request.is_json and 'image' in request.json:
            image_data = request.json['image']
            result = ImageService.upload_image(image_data, folder)
        else:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'No image payload found'
                }
            }), 400

        return jsonify({
            'success': True,
            'url': result['url'],
            'thumbnail_url': result['thumbnail_url']
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'SERVER_ERROR',
                'message': str(e)
            }
        }), 500
