from datetime import datetime

from extensions import db


class ProductQuestion(db.Model):
    __tablename__ = 'product_questions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending', index=True)  # pending | answered
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answered_at = db.Column(db.DateTime)

    user = db.relationship('User', backref='product_questions')
    product = db.relationship('Product', backref='questions')
