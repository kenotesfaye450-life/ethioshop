from backend.extensions import db
from datetime import datetime


class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subtotal = db.Column(db.Integer, nullable=False)  # ETB cents
    credit_used = db.Column(db.Integer, default=0)  # ETB cents
    final_total = db.Column(db.Integer, nullable=False)  # ETB cents
    payment_method = db.Column(db.String(50), nullable=False)
    payment_proof_url = db.Column(db.String(500))
    payment_plan = db.Column(db.String(20), default='full')  # full | half
    amount_paid = db.Column(db.Integer, default=0)  # ETB cents
    payment_status = db.Column(db.String(20), default='pending')  # pending | partial | paid
    evidence_requested = db.Column(db.Boolean, default=False)
    customer_note = db.Column(db.Text)
    additional_proof_url = db.Column(db.String(500))
    status = db.Column(db.String(50), default='pending_verification', index=True)
    delivery_location = db.Column(db.JSON)
    trusted_receiver_name = db.Column(db.String(255))
    trusted_receiver_phone = db.Column(db.String(20))
    local_person_name = db.Column(db.String(255))
    local_person_phone = db.Column(db.String(20))
    local_person_notes = db.Column(db.Text)
    delivery_status = db.Column(db.String(50), default='pending_assignment', index=True)
    delivery_status_updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_person_name = db.Column(db.String(255))
    delivery_person_phone = db.Column(db.String(20))
    delivery_confirmed_at = db.Column(db.DateTime)
    delivery_confirmed_by = db.Column(db.String(20))  # customer | admin | system
    delivery_confirmation_method = db.Column(db.String(50))
    delivery_confirmation_data = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    refund = db.relationship('Refund', backref='order', uselist=False, lazy=True)


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Integer, nullable=False)  # ETB cents
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
