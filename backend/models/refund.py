from extensions import db
from datetime import datetime


class Refund(db.Model):
    __tablename__ = 'refunds'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='pending_review', index=True)
    admin_notes = db.Column(db.Text)
    customer_visible_note = db.Column(db.Text)
    evidence_requested = db.Column(db.Boolean, default=False)
    additional_evidence_url = db.Column(db.String(500))
    approved_by = db.Column(db.Integer, db.ForeignKey('admins.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
