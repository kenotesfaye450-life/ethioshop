from extensions import db
from datetime import datetime


class TelegramUser(db.Model):
    """Maps a user's phone/user_id to their Telegram chat_id."""
    __tablename__ = 'telegram_users'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    phone = db.Column(db.Text, nullable=False)
    chat_id = db.Column(db.Text, nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
