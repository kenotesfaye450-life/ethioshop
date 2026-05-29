"""Initialize database with tables and seed data"""
import bcrypt

from app import create_app
from extensions import db
from models import (
    User, Product, Order, Admin, Refund, Request,
    Referral, CreditTransaction, TelegramUser,
)


def init_database():
    app = create_app()

    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()

        print("Creating all tables...")
        db.create_all()

        print("Creating default super admin...")
        password_hash = bcrypt.hashpw(
            'Wisdomlife1@9'.encode('utf-8'),
            bcrypt.gensalt(12)
        ).decode('utf-8')
        admin = Admin(
            username='KenoEthioShop',
            phone='0965806907',
            password_hash=password_hash,
            role='super_admin'
        )
        db.session.add(admin)

        print("Creating sample products...")
        categories = ['Shoes', 'Clothing', 'Watches', 'Phones', 'Beauty']

        for i, category in enumerate(categories):
            product = Product(
                name=f'Sample {category} Product {i+1}',
                description=f'High quality {category.lower()} product',
                cost_price=2000 * 100,
                selling_price=2600 * 100,
                stock=50,
                category=category,
                image_url=f'https://via.placeholder.com/600x600?text={category}',
                thumbnail_url=f'https://via.placeholder.com/300x300?text={category}'
            )
            db.session.add(product)

        db.session.commit()
        print("Database initialized successfully!")
        print("\nDefault super admin credentials:")
        print("Username: KenoEthioShop")
        print("Phone: 0965806907")
        print("Password: Wisdomlife1@9")


if __name__ == '__main__':
    init_database()
