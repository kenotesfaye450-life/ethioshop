"""
Telegram notification service.
chat_id is stored in the telegram_users table (not users.telegram_chat_id).
"""
import os
import requests as http_requests
from config import Config


def send_telegram_message(chat_id: str, text: str) -> bool:
    return _send(chat_id, text)


def _send(chat_id: str, text: str) -> bool:
    token = Config.TELEGRAM_BOT_TOKEN
    if not token:
        print(f"[notify] No TELEGRAM_BOT_TOKEN — skipping: {text[:60]}")
        return False
    try:
        resp = http_requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=5,
        )
        if resp.status_code != 200:
            print(f"[notify] Telegram error {resp.status_code}: {resp.text[:200]}")
            return False
        return True
    except Exception as e:
        print(f"[notify] Exception: {e}")
        return False


def _get_chat_id(user) -> str | None:
    if user is None:
        return None
    try:
        from models import TelegramUser
        tg = TelegramUser.query.filter_by(user_id=user.id).first()
        if tg and tg.chat_id and not str(tg.chat_id).startswith('unsubscribed:'):
            return tg.chat_id
    except Exception:
        pass
    legacy = getattr(user, 'telegram_chat_id', None)
    if legacy and not str(legacy).startswith('unsubscribed:'):
        return legacy
    return None


class NotificationService:

    @staticmethod
    def _notify_customer(user, message: str):
        chat_id = _get_chat_id(user)
        if chat_id:
            _send(chat_id, message)

    @staticmethod
    def notify_order_status_change(order):
        """Notify customer and admin when order or delivery status changes."""
        user = order.user

        if order.status == 'delivered' or order.delivery_status == 'delivered':
            message = (
                f"📦 <b>Order #{order.id} delivered!</b>\n"
                f"Thank you for shopping with EthioShop. 🛍️"
            )
        elif order.delivery_status == 'in_transit':
            message = (
                f"🚚 <b>Order #{order.id} is on the way!</b>\n"
                f"Delivery: {order.delivery_person_name or 'TBD'}"
                + (f" — {order.delivery_person_phone}" if order.delivery_person_phone else "")
            )
        elif order.delivery_status == 'assigned' and order.status == 'confirmed':
            message = (
                f"📋 <b>Order #{order.id}</b> — delivery person assigned.\n"
                f"{order.delivery_person_name or 'Courier'} "
                f"{('- ' + order.delivery_person_phone) if order.delivery_person_phone else ''}"
            )
        else:
            status_messages = {
                "confirmed": (
                    f"✅ <b>Order #{order.id} confirmed!</b>\n"
                    f"Total: {order.final_total/100:.2f} ETB\n"
                    f"We will assign a delivery person soon."
                ),
                "rejected": (
                    f"❌ <b>Order #{order.id} rejected.</b>\n"
                    f"{order.customer_note or 'Any credit used has been restored.'}"
                ),
                "refunded": (
                    f"💰 <b>Order #{order.id} refunded.</b>\n"
                    f"Credit of {order.final_total/100:.2f} ETB added to your account."
                ),
            }
            message = status_messages.get(
                order.status,
                f"🔔 Order #{order.id} status: <b>{order.status}</b>"
                + (f" | Delivery: <b>{order.delivery_status}</b>" if order.delivery_status else ""),
            )

        NotificationService._notify_customer(user, message)

        admin_chat_id = os.getenv("ADMIN_CHAT_ID")
        if admin_chat_id:
            _send(
                admin_chat_id,
                f"🔔 Order #{order.id} → {order.status} / {order.delivery_status}\n"
                f"Customer: {user.phone if user else 'unknown'}\n"
                f"Total: {order.final_total/100:.2f} ETB",
            )

    @staticmethod
    def notify_request_quote(demand_request):
        user = demand_request.user
        extra = ''
        if demand_request.admin_response_message:
            extra = f"\n\n💬 {demand_request.admin_response_message}"
        msg = (
            f"💰 <b>Price quoted for request #{demand_request.id}</b>\n"
            f"Price: <b>{demand_request.quoted_price/100:.2f} ETB</b>\n"
            f"View My Requests on the website to accept.{extra}"
        )
        NotificationService._notify_customer(user, msg)

    @staticmethod
    def notify_request_credit_awarded(user, amount_etb, product_name):
        msg = (
            f"🎁 <b>Thank you for your product request!</b>\n"
            f"We added <b>{product_name}</b> to our catalog.\n"
            f"You received <b>{amount_etb:.0f} ETB</b> store credit."
        )
        NotificationService._notify_customer(user, msg)

    @staticmethod
    def notify_request_rejected(demand_request):
        user = demand_request.user
        msg = (
            f"❌ <b>Request #{demand_request.id} was not available.</b>\n"
            f"{demand_request.admin_response_message or 'We could not source this item.'}"
        )
        NotificationService._notify_customer(user, msg)

    @staticmethod
    def notify_refund_update(refund, order):
        user = order.user if order else None
        if refund.status == 'approved':
            msg = (
                f"💰 <b>Refund approved for order #{order.id}</b>\n"
                f"{refund.customer_visible_note or 'Credit has been restored to your account.'}"
            )
        elif refund.status == 'rejected':
            msg = (
                f"❌ <b>Refund declined for order #{order.id}</b>\n"
                f"{refund.customer_visible_note or refund.admin_notes or 'See dashboard for details.'}"
            )
        else:
            msg = f"🔔 Refund #{refund.id} status: <b>{refund.status}</b>"
        NotificationService._notify_customer(user, msg)

    @staticmethod
    def notify_evidence_requested(order=None, refund=None, note=''):
        user = None
        if order:
            user = order.user
            msg = (
                f"📎 <b>Additional evidence needed — Order #{order.id}</b>\n"
                f"{note or 'Please upload a clearer payment proof on your dashboard.'}"
            )
        elif refund:
            user = refund.order.user if refund.order else None
            msg = (
                f"📎 <b>Additional evidence needed — Refund #{refund.id}</b>\n"
                f"{note or 'Please upload supporting documents on your dashboard.'}"
            )
        else:
            return
        NotificationService._notify_customer(user, msg)

    @staticmethod
    def notify_product_question_answered(product_question):
        user = product_question.user
        product_name = product_question.product.name if product_question.product else 'product'
        msg = (
            f"💬 <b>Answer about {product_name}</b>\n\n"
            f"<i>Your question:</i> {product_question.question}\n\n"
            f"<i>Answer:</i> {product_question.answer}"
        )
        NotificationService._notify_customer(user, msg)
