from flask import Blueprint, request, jsonify
from sqlalchemy import or_
from sqlalchemy import func

from extensions import db
from models import Product, ProductImage, Review, Order, OrderItem, ProductQuestion, User
from utils.validators import normalize_ethiopian_phone
from services.image_service import ImageService
from utils.auth import require_auth

bp = Blueprint('products', __name__, url_prefix='/api/products')

DEFAULT_CATEGORIES = [
    'Shoes', 'Clothing', 'Watches', 'Phones', 'Beauty', 'Bags', 'Electronics',
    'Home Essentials', 'Perfumes', 'Sports', 'Earphones', 'Blankets', 'Jewelry', 'Thermoses',
]


def _image_dict(img):
    return {
        'id': img.id,
        'image_url': img.image_url,
        'thumbnail_url': img.thumbnail_url,
        'is_primary': img.is_primary,
        'sort_order': img.sort_order,
    }


def _sync_legacy_urls(product):
    """Keep image_url/thumbnail_url in sync with primary gallery image."""
    primary = product.primary_image
    if primary:
        product.image_url = primary.image_url
        product.thumbnail_url = primary.thumbnail_url


def _cloudinary_public_id_from_url(url: str | None) -> str | None:
    if not url or '/upload/' not in url:
        return None
    tail = url.split('/upload/', 1)[1]
    # remove optional transformation/version prefixes
    parts = tail.split('/')
    while parts and (parts[0].startswith('v') and parts[0][1:].isdigit() or ',' in parts[0]):
        parts = parts[1:]
    if not parts:
        return None
    path = '/'.join(parts)
    if '.' in path:
        path = path.rsplit('.', 1)[0]
    return path


def _product_dict(p, include_images=False):
    primary = p.primary_image
    data = {
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'price': p.selling_price / 100,
        'stock': int(p.stock or 0),
        'category': p.category,
        'image_url': p.image_url or (primary.image_url if primary else None),
        'thumbnail_url': p.thumbnail_url or (primary.thumbnail_url if primary else None),
        'in_stock': int(p.stock or 0) > 0,
    }
    if include_images:
        imgs = sorted(p.images, key=lambda x: (not x.is_primary, x.sort_order, x.id))
        data['images'] = [_image_dict(i) for i in imgs]
    avg_rating, review_count = db.session.query(
        func.avg(Review.rating), func.count(Review.id)
    ).filter(Review.product_id == p.id).first()
    data['avg_rating'] = round(float(avg_rating), 2) if avg_rating else 0
    data['review_count'] = int(review_count or 0)
    return data


def _product_admin_dict(p, include_images=False):
    data = _product_dict(p, include_images=include_images)
    data['cost_price'] = p.cost_price / 100
    return data


@bp.route('/categories', methods=['GET'])
def get_categories():
    try:
        db_cats = [
            c[0] for c in db.session.query(Product.category).distinct().all()
            if c[0]
        ]
        merged = list(dict.fromkeys(DEFAULT_CATEGORIES + sorted(db_cats)))
        return jsonify({'success': True, 'categories': merged}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('', methods=['GET'])
def get_products():
    try:
        category = request.args.get('category')
        search = request.args.get('search')
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', request.args.get('per_page', 20))), 100)

        query = Product.query
        if category:
            query = query.filter(Product.category == category)
        if search:
            query = query.filter(or_(
                Product.name.ilike(f'%{search}%'),
                Product.description.ilike(f'%{search}%'),
            ))

        paginated = query.paginate(page=page, per_page=limit, error_out=False)
        items = [_product_dict(p) for p in paginated.items]

        return jsonify({
            'success': True,
            'items': items,
            'products': items,
            'page': paginated.page,
            'pages': paginated.pages,
            'total': paginated.total,
            'per_page': limit,
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/manage', methods=['GET'])
@require_auth
def get_products_admin():
    try:
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 100)
        paginated = Product.query.order_by(Product.created_at.desc()).paginate(
            page=page, per_page=limit, error_out=False
        )
        items = [_product_admin_dict(p, include_images=True) for p in paginated.items]
        return jsonify({
            'success': True,
            'items': items,
            'products': items,
            'page': paginated.page,
            'pages': paginated.pages,
            'total': paginated.total,
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Product not found'}}), 404
        recent_reviews = Review.query.filter_by(product_id=product.id).order_by(Review.created_at.desc()).limit(10).all()
        payload = _product_dict(product, include_images=True)
        payload['reviews'] = [{
            'id': r.id,
            'rating': r.rating,
            'comment': r.comment,
            'created_at': r.created_at.isoformat(),
        } for r in recent_reviews]
        return jsonify({'success': True, 'product': payload}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:product_id>/manage', methods=['GET'])
@require_auth
def get_product_admin(product_id):
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Product not found'}}), 404
        return jsonify({'success': True, 'product': _product_admin_dict(product, include_images=True)}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('', methods=['POST'])
@require_auth
def create_product():
    try:
        data = request.get_json() or {}
        category = (data.get('category') or data.get('custom_category') or '').strip()
        required = ['name', 'cost_price', 'selling_price']
        missing = [f for f in required if f not in data]
        if missing or not category:
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Missing required fields'}}), 400

        product = Product(
            name=data['name'],
            description=data.get('description', ''),
            cost_price=int(float(data['cost_price']) * 100),
            selling_price=int(float(data['selling_price']) * 100),
            stock=int(data.get('stock', 0)),
            category=category,
            image_url=data.get('image_url'),
            thumbnail_url=data.get('thumbnail_url'),
            manual_price_override=data.get('manual_price_override', False),
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({'success': True, 'product': _product_admin_dict(product)}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:product_id>', methods=['PATCH'])
@require_auth
def update_product(product_id):
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Product not found'}}), 404

        data = request.get_json() or {}
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'cost_price' in data:
            product.cost_price = int(float(data['cost_price']) * 100)
        if 'selling_price' in data:
            product.selling_price = int(float(data['selling_price']) * 100)
        if 'stock' in data:
            product.stock = int(data['stock'])
        if 'category' in data or 'custom_category' in data:
            product.category = (data.get('category') or data.get('custom_category') or product.category).strip()
        if 'image_url' in data:
            product.image_url = data['image_url']
        if 'thumbnail_url' in data:
            product.thumbnail_url = data['thumbnail_url']

        db.session.commit()
        return jsonify({'success': True, 'product': _product_admin_dict(product, include_images=True)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:product_id>', methods=['DELETE'])
@require_auth
def delete_product(product_id):
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Product not found'}}), 404
        # delete product image assets from cloudinary if possible
        for img in list(product.images):
            pid = _cloudinary_public_id_from_url(img.image_url)
            if pid:
                try:
                    ImageService.delete_image(pid)
                except Exception:
                    pass
        db.session.delete(product)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Product deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:product_id>/images', methods=['POST'])
@require_auth
def upload_product_images(product_id):
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Product not found'}}), 404

        files = request.files.getlist('file') or request.files.getlist('files')
        if not files and 'file' in request.files:
            files = [request.files['file']]

        if not files:
            return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'No files uploaded'}}), 400

        uploaded = []
        has_primary = any(i.is_primary for i in product.images)
        for idx, file in enumerate(files):
            if not file or not file.filename:
                continue
            result = ImageService.upload_image(file, 'products')
            img = ProductImage(
                product_id=product.id,
                image_url=result['url'],
                thumbnail_url=result['thumbnail_url'],
                is_primary=(not has_primary and idx == 0),
                sort_order=len(product.images) + idx,
            )
            if img.is_primary:
                has_primary = True
            db.session.add(img)
            uploaded.append(img)

        _sync_legacy_urls(product)
        db.session.commit()
        return jsonify({
            'success': True,
            'images': [_image_dict(i) for i in uploaded],
            'product': _product_admin_dict(product, include_images=True),
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:product_id>/images/<int:image_id>', methods=['DELETE'])
@require_auth
def delete_product_image(product_id, image_id):
    try:
        img = ProductImage.query.filter_by(id=image_id, product_id=product_id).first()
        if not img:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Image not found'}}), 404
        was_primary = img.is_primary
        product = img.product
        db.session.delete(img)
        db.session.flush()
        if was_primary and product.images:
            product.images[0].is_primary = True
        _sync_legacy_urls(product)
        db.session.commit()
        return jsonify({'success': True, 'product': _product_admin_dict(product, include_images=True)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:product_id>/images/<int:image_id>/primary', methods=['PATCH'])
@require_auth
def set_primary_image(product_id, image_id):
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Product not found'}}), 404
        for img in product.images:
            img.is_primary = img.id == image_id
        _sync_legacy_urls(product)
        db.session.commit()
        return jsonify({'success': True, 'product': _product_admin_dict(product, include_images=True)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/reviews/recent', methods=['GET'])
def recent_reviews():
    """Recent product reviews for social proof (public)."""
    try:
        rows = Review.query.order_by(Review.created_at.desc()).limit(8).all()
        items = []
        for r in rows:
            product = Product.query.get(r.product_id)
            items.append({
                'id': r.id,
                'product_name': product.name if product else 'Product',
                'rating': r.rating,
                'comment': (r.comment or '')[:200],
                'created_at': r.created_at.isoformat(),
            })
        return jsonify({'success': True, 'reviews': items}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/<int:product_id>/ask', methods=['POST'])
def ask_product_question(product_id):
    """Customer asks about product stock/availability."""
    try:
        data = request.get_json() or {}
        question = (data.get('question') or '').strip()
        if not question:
            return jsonify({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': 'phone and question are required'},
            }), 400
        try:
            phone = normalize_ethiopian_phone(data.get('phone') or '')
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': str(e)},
            }), 400

        product = Product.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Product not found'}}), 404

        user = User.query.filter_by(phone=phone).first()
        if not user:
            return jsonify({
                'success': False,
                'error': {'code': 'NOT_FOUND', 'message': 'User not found. Please register first.'},
            }), 404

        pq = ProductQuestion(
            user_id=user.id,
            product_id=product.id,
            question=question,
            status='pending',
        )
        db.session.add(pq)
        db.session.flush()
        from services.telegram_service import NotificationService
        NotificationService.notify_admin_new_question(pq, product)
        db.session.commit()

        return jsonify({
            'success': True,
            'question': {
                'id': pq.id,
                'product_id': product.id,
                'product_name': product.name,
                'question': pq.question,
                'status': pq.status,
                'created_at': pq.created_at.isoformat(),
            },
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500


@bp.route('/recent-sales', methods=['GET'])
def recent_sales():
    """Recent confirmed/delivered sales for social proof."""
    try:
        rows = (
            db.session.query(OrderItem, Order, Product)
            .join(Order, Order.id == OrderItem.order_id)
            .join(Product, Product.id == OrderItem.product_id)
            .filter(Order.status.in_(['confirmed', 'delivered']))
            .order_by(Order.created_at.desc())
            .limit(10)
            .all()
        )
        items = []
        for item, order, product in rows:
            city = 'Addis Ababa'
            if isinstance(order.delivery_location, dict):
                city = order.delivery_location.get('city') or order.delivery_location.get('address') or city
            items.append({
                'order_id': order.id,
                'product_id': product.id,
                'product_name': product.name,
                'city': city[:80],
                'created_at': order.created_at.isoformat(),
            })
        return jsonify({'success': True, 'items': items}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500
