from extensions import db
from datetime import datetime


class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    cost_price = db.Column(db.Integer, nullable=False)  # ETB cents
    selling_price = db.Column(db.Integer, nullable=False)  # ETB cents
    stock = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50), nullable=False, index=True)
    image_url = db.Column(db.String(500))
    thumbnail_url = db.Column(db.String(500))
    manual_price_override = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

    @property
    def primary_image(self):
        for img in self.images:
            if img.is_primary:
                return img
        return self.images[0] if self.images else None
