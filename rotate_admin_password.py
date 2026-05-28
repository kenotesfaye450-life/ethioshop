#!/usr/bin/env python3
"""Run once after deployment to change default admin password."""

import os
import secrets
import string
import sys

import bcrypt
import psycopg2


def generate_strong_password(length=16):
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print('ERROR: DATABASE_URL environment variable not set.')
        sys.exit(1)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    return psycopg2.connect(database_url)


def rotate_admin_password():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, username FROM admins WHERE username = 'KenoEthioShop' AND phone = '0965806907'"
    )
    admin = cur.fetchone()
    if not admin:
        print('Default admin not found. Skipping.')
        cur.close()
        conn.close()
        return

    new_password = generate_strong_password()
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt(12))

    cur.execute('UPDATE admins SET password_hash = %s WHERE id = %s', (hashed.decode('utf-8'), admin[0]))
    conn.commit()

    print('=' * 50)
    print('ADMIN PASSWORD ROTATED')
    print('Username: KenoEthioShop')
    print('Phone: 0965806907')
    print(f'New password: {new_password}')
    print('=' * 50)
    print('Please save this password and change it again after login if desired.')

    cur.close()
    conn.close()


if __name__ == '__main__':
    rotate_admin_password()
