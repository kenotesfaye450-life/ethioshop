from extensions import db
from datetime import datetime


class SiteSetting(db.Model):
    __tablename__ = 'site_settings'

    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get(key, default=None):
        row = SiteSetting.query.get(key)
        return row.value if row else default

    @staticmethod
    def set(key, value):
        row = SiteSetting.query.get(key)
        if row:
            row.value = value
        else:
            row = SiteSetting(key=key, value=value)
            db.session.add(row)
        return row
