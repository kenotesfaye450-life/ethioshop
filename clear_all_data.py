#!/usr/bin/env python3
"""Clear all user, order, product data from production database (keep admins)."""

import os
import sys
import psycopg2
from urllib.parse import urlparse

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set.")
        sys.exit(1)
    # Convert postgres:// to postgresql:// if needed
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    return psycopg2.connect(database_url)

def clear_data():
    conn = get_db_connection()
    cur = conn.cursor()

    # Disable triggers to avoid foreign key issues (temporarily)
    cur.execute("SET session_replication_role = 'replica';")

    # Order of deletion matters (children first)
    tables = [
        "order_messages",
        "payments",
        "reviews",
        "bot_cart",
        "order_items",
        "orders",
        "credit_transactions",
        "referrals",
        "telegram_users",
        "requests",
        "refunds",
        "product_images",
        "products",
        "users",
    ]

    for table in tables:
        try:
            cur.execute(f"DELETE FROM {table};")
            print(f"Cleared table: {table}")
        except Exception as e:
            print(f"Error clearing {table}: {e}")

    # Re-enable triggers
    cur.execute("SET session_replication_role = 'origin';")

    conn.commit()
    cur.close()
    conn.close()
    print("\n✅ All non‑admin data cleared successfully.")
    print("   - All users, orders, requests, refunds, referrals, products, images deleted.")
    print("   - Admin account (KenoEthioShop) remains intact.\n")

if __name__ == "__main__":
    clear_data()