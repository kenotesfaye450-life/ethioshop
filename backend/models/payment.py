from extensions import db
from datetime import datetime


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    amount = db.Column(db.Integer, nullable=False)  # ETB cents
    payment_proof_url = db.Column(db.String(500))
    payment_type = db.Column(db.String(20), default='initial')  # initial | remaining | manual
    status = db.Column(db.String(20), default='pending')  # pending | verified | rejected
    verified_by = db.Column(db.Integer, db.ForeignKey('admins.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
