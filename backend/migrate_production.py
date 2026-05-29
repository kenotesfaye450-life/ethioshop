#!/usr/bin/env python3
"""Production migration using Flask+SQLAlchemy (Railway‑compatible)."""

import sys
import os
sys.path.append(os.getcwd())

from app import create_app
from extensions import db

def run_migration():
    app = create_app()
    with app.app_context():
        # Orders table additions
        db.session.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_plan VARCHAR(20) DEFAULT 'full'")
        db.session.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS amount_paid INTEGER DEFAULT 0")
        db.session.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_status VARCHAR(20) DEFAULT 'pending'")
        db.session.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_status_updated_at TIMESTAMP")
        db.session.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_confirmed_at TIMESTAMP")
        db.session.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_confirmed_by VARCHAR(20)")
        db.session.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS evidence_requested BOOLEAN DEFAULT FALSE")
        db.session.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS customer_note TEXT")
        db.session.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS additional_proof_url TEXT")
        db.session.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS local_person_name VARCHAR(100)")
        db.session.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS local_person_phone VARCHAR(20)")
        db.session.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS local_person_notes TEXT")

        db.session.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
                amount INTEGER NOT NULL,
                payment_proof_url TEXT,
                payment_type VARCHAR(20) DEFAULT 'initial',
                status VARCHAR(20) DEFAULT 'pending',
                verified_by INTEGER REFERENCES admins(id),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        db.session.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
                product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                comment TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        db.session.execute("""
            CREATE TABLE IF NOT EXISTS bot_cart (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
                quantity INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(user_id, product_id)
            )
        """)

        db.session.execute("""
            CREATE TABLE IF NOT EXISTS order_messages (
                id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
                sender_type VARCHAR(20) NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        db.session.execute("""
            CREATE TABLE IF NOT EXISTS site_settings (
                key VARCHAR(100) PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        db.session.execute("""
            INSERT INTO site_settings (key, value) VALUES
                ('announcement_message', 'Welcome to EthioShop!'),
                ('announcement_active', 'false'),
                ('announcement_close_delay_seconds', '3'),
                ('announcement_display_seconds', '10'),
                ('max_referral_per_year', '2000'),
                ('owner_message', 'EthioShop is your trusted Ethiopian e-commerce platform.'),
                ('owner_image_url', '')
            ON CONFLICT (key) DO NOTHING
        """)

        db.session.execute("ALTER TABLE requests ADD COLUMN IF NOT EXISTS request_credit_awarded BOOLEAN DEFAULT FALSE")

        db.session.execute("""
            CREATE TABLE IF NOT EXISTS product_questions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
                question TEXT NOT NULL,
                answer TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT NOW(),
                answered_at TIMESTAMP
            )
        """)
        db.session.execute("""
            CREATE TABLE IF NOT EXISTS admin_actions (
                id SERIAL PRIMARY KEY,
                admin_id INTEGER REFERENCES admins(id),
                action_type VARCHAR(50) NOT NULL,
                details TEXT,
                records_affected INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        db.session.commit()
        print("✅ Production migration completed successfully.")

if __name__ == "__main__":
    run_migration()
