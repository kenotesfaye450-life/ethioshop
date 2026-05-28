"""One-time migration for payment, delivery confirmation, reviews and bot cart."""
from sqlalchemy import create_engine, text
from backend.config import Config


SQL = [
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_plan VARCHAR(20) DEFAULT 'full';",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS amount_paid INTEGER DEFAULT 0;",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_status VARCHAR(20) DEFAULT 'pending';",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_status_updated_at TIMESTAMP;",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_confirmed_at TIMESTAMP;",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_confirmed_by VARCHAR(20);",
    "UPDATE orders SET amount_paid = COALESCE(final_total, 0) WHERE COALESCE(amount_paid, 0) = 0;",
    "UPDATE orders SET payment_status = CASE WHEN COALESCE(amount_paid,0) >= COALESCE(final_total,0) THEN 'paid' WHEN COALESCE(amount_paid,0) > 0 THEN 'partial' ELSE 'pending' END;",
    "UPDATE orders SET payment_plan = 'full' WHERE payment_plan IS NULL;",
    "UPDATE orders SET delivery_status_updated_at = COALESCE(delivery_status_updated_at, created_at);",
    """
    CREATE TABLE IF NOT EXISTS payments (
        id SERIAL PRIMARY KEY,
        order_id INTEGER NOT NULL REFERENCES orders(id),
        amount INTEGER NOT NULL,
        payment_proof_url VARCHAR(500),
        payment_type VARCHAR(20) DEFAULT 'initial',
        status VARCHAR(20) DEFAULT 'pending',
        verified_by INTEGER REFERENCES admins(id),
        created_at TIMESTAMP DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS reviews (
        id SERIAL PRIMARY KEY,
        order_id INTEGER NOT NULL REFERENCES orders(id),
        product_id INTEGER NOT NULL REFERENCES products(id),
        user_id INTEGER NOT NULL REFERENCES users(id),
        rating INTEGER NOT NULL,
        comment TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS bot_cart (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        product_id INTEGER NOT NULL REFERENCES products(id),
        quantity INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """,
]


def main():
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    with engine.begin() as conn:
        for stmt in SQL:
            conn.execute(text(stmt))
    print("Migration completed: payment/delivery/review/bot_cart fields ready.")


if __name__ == "__main__":
    main()
