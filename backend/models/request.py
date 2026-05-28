from backend.extensions import db
from datetime import datetime


class Request(db.Model):
    __tablename__ = 'requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    budget = db.Column(db.Integer)  # ETB cents
    quoted_price = db.Column(db.Integer)  # ETB cents
    status = db.Column(db.String(50), default='pending_sourcing', index=True)
    delivery_location = db.Column(db.JSON)
    converted_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    admin_response_message = db.Column(db.Text)
    request_credit_awarded = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
