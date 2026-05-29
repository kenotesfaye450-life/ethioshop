#!/usr/bin/env python3
"""Rotate default admin password using SQLAlchemy (Railway‑compatible)."""

import sys
import os
import bcrypt
import secrets
import string
sys.path.append(os.getcwd())

from app import create_app
from extensions import db
from models import Admin

def generate_strong_password(length=16):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def rotate_admin_password():
    app = create_app()
    with app.app_context():
        admin = Admin.query.filter_by(username='KenoEthioShop', phone='0965806907').first()
        if not admin:
            print("Default admin not found. Skipping.")
            return

        new_password = generate_strong_password()
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt(12))
        admin.password_hash = hashed.decode('utf-8')
        db.session.commit()

        print("=" * 50)
        print("ADMIN PASSWORD ROTATED")
        print("Username: KenoEthioShop")
        print("Phone: 0965806907")
        print(f"New password: {new_password}")
        print("=" * 50)

if __name__ == "__main__":
    rotate_admin_password()
