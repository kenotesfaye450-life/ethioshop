"""One-time migration: local person fields, request credit flag, site settings."""
from sqlalchemy import create_engine, text
from backend.config import Config

SQL = [
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS local_person_name VARCHAR(255);",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS local_person_phone VARCHAR(20);",
    "ALTER TABLE orders ADD COLUMN IF NOT EXISTS local_person_notes TEXT;",
    "ALTER TABLE requests ADD COLUMN IF NOT EXISTS request_credit_awarded BOOLEAN DEFAULT FALSE;",
    """
    INSERT INTO site_settings (key, value, updated_at)
    SELECT 'owner_message', 'Welcome to EthioShop — honest prices, secure half-payment, and delivery you can confirm.', NOW()
    WHERE NOT EXISTS (SELECT 1 FROM site_settings WHERE key = 'owner_message');
    """,
    """
    INSERT INTO site_settings (key, value, updated_at)
    SELECT 'max_referral_per_year', '2000', NOW()
    WHERE NOT EXISTS (SELECT 1 FROM site_settings WHERE key = 'max_referral_per_year');
    """,
    """
    INSERT INTO site_settings (key, value, updated_at)
    SELECT 'request_reward_etb', '20', NOW()
    WHERE NOT EXISTS (SELECT 1 FROM site_settings WHERE key = 'request_reward_etb');
    """,
    """
    INSERT INTO site_settings (key, value, updated_at)
    SELECT 'announcement_close_delay_seconds', '3', NOW()
    WHERE NOT EXISTS (SELECT 1 FROM site_settings WHERE key = 'announcement_close_delay_seconds');
    """,
    """
    INSERT INTO site_settings (key, value, updated_at)
    SELECT 'announcement_display_seconds', '0', NOW()
    WHERE NOT EXISTS (SELECT 1 FROM site_settings WHERE key = 'announcement_display_seconds');
    """,
]


def main():
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    with engine.begin() as conn:
        for stmt in SQL:
            conn.execute(text(stmt))
    print("Migration completed: local person fields, request credit flag, site settings.")


if __name__ == "__main__":
    main()
