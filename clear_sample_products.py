"""One-time cleanup script: remove all products and product images."""
from backend.app import create_app
from backend.extensions import db
from backend.models import Product, ProductImage


def main():
    app = create_app()
    with app.app_context():
        images_deleted = ProductImage.query.delete()
        products_deleted = Product.query.delete()
        db.session.commit()
        print(f"Deleted {images_deleted} product images.")
        print(f"Deleted {products_deleted} products.")
        print("Orders, users, and other data were not touched.")


if __name__ == "__main__":
    main()
