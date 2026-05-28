from backend.extensions import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255))
    credit_balance = db.Column(db.Integer, default=0)  # ETB cents
    referral_code = db.Column(db.String(8), unique=True, nullable=False, index=True)
    referred_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    total_referrals = db.Column(db.Integer, default=0)
    telegram_chat_id = db.Column(db.String(50))  # Set when user links via bot
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='user', lazy=True)
    requests = db.relationship('Request', backref='user', lazy=True)
