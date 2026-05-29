from extensions import db
from datetime import datetime


class OrderMessage(db.Model):
    __tablename__ = 'order_messages'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    sender_type = db.Column(db.String(20), nullable=False)  # 'admin' | 'customer'
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order = db.relationship('Order', backref=db.backref('messages', lazy=True))
