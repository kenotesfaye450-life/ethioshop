from backend.extensions import db
from datetime import datetime


class CreditTransaction(db.Model):
    __tablename__ = 'credit_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # ETB cents (positive or negative)
    transaction_type = db.Column(db.String(50), nullable=False)  # referral_earned, order_used, refund_restored, cancellation_reversed
    related_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
