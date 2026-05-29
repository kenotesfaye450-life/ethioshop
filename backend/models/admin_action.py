from datetime import datetime

from extensions import db


class AdminAction(db.Model):
    __tablename__ = 'admin_actions'

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'))
    action_type = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text)
    records_affected = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
