#!/usr/bin/env python3
"""Run once on production database (Railway console or locally with DATABASE_URL). Idempotent."""

import os
import sys

import psycopg2


def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print('ERROR: DATABASE_URL environment variable not set.')
        sys.exit(1)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    return psycopg2.connect(database_url)


def run_migration():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_plan VARCHAR(20) DEFAULT 'full';
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS amount_paid INTEGER DEFAULT 0;
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_status VARCHAR(20) DEFAULT 'pending';
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_status_updated_at TIMESTAMP;
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_confirmed_at TIMESTAMP;
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_confirmed_by VARCHAR(20);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS evidence_requested BOOLEAN DEFAULT FALSE;
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS customer_note TEXT;
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS additional_proof_url TEXT;
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS local_person_name VARCHAR(100);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS local_person_phone VARCHAR(20);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS local_person_notes TEXT;
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
            amount INTEGER NOT NULL,
            payment_proof_url TEXT,
            payment_type VARCHAR(20) DEFAULT 'initial',
            status VARCHAR(20) DEFAULT 'pending',
            verified_by INTEGER REFERENCES admins(id),
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
            product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            rating INTEGER CHECK (rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bot_cart (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
            quantity INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, product_id)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_messages (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
            sender_type VARCHAR(20) NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS site_settings (
            key VARCHAR(100) PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("""
        INSERT INTO site_settings (key, value) VALUES
            ('announcement_message', 'Welcome to EthioShop!'),
            ('announcement_active', 'false'),
            ('announcement_close_delay_seconds', '3'),
            ('announcement_display_seconds', '10'),
            ('max_referral_per_year', '2000'),
            ('owner_message', 'EthioShop is your trusted Ethiopian e-commerce platform.'),
            ('owner_image_url', '')
        ON CONFLICT (key) DO NOTHING;
    """)

    cur.execute("""
        ALTER TABLE requests ADD COLUMN IF NOT EXISTS request_credit_awarded BOOLEAN DEFAULT FALSE;
    """)

    conn.commit()
    cur.close()
    conn.close()
    print('Production migration completed successfully.')


if __name__ == '__main__':
    run_migration()
