from backend.extensions import db
from datetime import datetime


class Referral(db.Model):
    __tablename__ = 'referrals'
    
    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    referred_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    credit_awarded = db.Column(db.Integer, default=5000)  # 50 ETB in cents
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
