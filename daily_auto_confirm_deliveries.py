"""Daily cron script to auto-confirm overdue in-transit deliveries."""
from datetime import datetime, timedelta
from backend.app import create_app
from backend.extensions import db
from backend.models import Order


def main():
    app = create_app()
    with app.app_context():
        cutoff = datetime.utcnow() - timedelta(days=14)
        orders = Order.query.filter(
            Order.delivery_status == 'in_transit',
            Order.delivery_status_updated_at <= cutoff
        ).all()
        updated = 0
        for order in orders:
            if order.payment_status != 'paid':
                continue
            order.delivery_status = 'delivered'
            order.status = 'delivered'
            order.delivery_status_updated_at = datetime.utcnow()
            order.delivery_confirmed_at = datetime.utcnow()
            order.delivery_confirmed_by = 'system'
            updated += 1
        db.session.commit()
        print(f"Auto-confirmed deliveries: {updated}")


if __name__ == "__main__":
    main()
