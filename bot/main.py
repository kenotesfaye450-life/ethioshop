"""
EthioShop Telegram Bot — main entry point.

Run from the bot folder:
  cd bot
  pip install -r requirements.txt
  python main.py

Environment (bot/.env):
  TELEGRAM_BOT_TOKEN
  API_BASE_URL=http://localhost:5000
  ADMIN_CHAT_ID (optional)
"""
import logging
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    InlineQueryHandler,
    MessageHandler,
    filters,
)

from config import TELEGRAM_BOT_TOKEN
from handlers import commands, conversations, groups, inline
from handlers.commands import (
    AWAITING_CONTACT,
    AWAITING_REGISTER_NAME,
    CHECKOUT_ADDRESS,
    CHECKOUT_CITY,
    CHECKOUT_CONFIRM,
    checkout_start,
    checkout_address_received,
    checkout_city_received,
    checkout_skip_city,
    checkout_confirm_response,
    checkout_cancel,
)
from handlers.conversations import ASK_ORDER_ID, ASK_PHOTO
from services.api_client import APIClient

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    if not TELEGRAM_BOT_TOKEN:
        print('ERROR: TELEGRAM_BOT_TOKEN not set (bot/.env)')
        sys.exit(1)

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.bot_data['api'] = APIClient()

    start_conv = ConversationHandler(
        entry_points=[CommandHandler('start', commands.cmd_start)],
        states={
            AWAITING_CONTACT: [
                MessageHandler(filters.CONTACT, commands.receive_contact),
                CommandHandler('cancel', commands.cmd_cancel),
            ],
            AWAITING_REGISTER_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, commands.receive_register_name),
                CommandHandler('cancel', commands.cmd_cancel),
            ],
        },
        fallbacks=[CommandHandler('cancel', commands.cmd_cancel)],
    )
    app.add_handler(start_conv)

    pay_conv = ConversationHandler(
        entry_points=[CommandHandler('pay', conversations.pay_start)],
        states={
            ASK_ORDER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, conversations.pay_order_id)],
            ASK_PHOTO: [MessageHandler(filters.PHOTO, conversations.pay_photo)],
        },
        fallbacks=[CommandHandler('cancel', conversations.pay_cancel)],
    )
    app.add_handler(pay_conv)

    checkout_conv = ConversationHandler(
        entry_points=[CommandHandler('checkout', checkout_start)],
        states={
            CHECKOUT_ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, checkout_address_received),
            ],
            CHECKOUT_CITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, checkout_city_received),
                CommandHandler('skip', checkout_skip_city),
            ],
            CHECKOUT_CONFIRM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, checkout_confirm_response),
            ],
        },
        fallbacks=[CommandHandler('cancel', checkout_cancel)],
    )
    app.add_handler(checkout_conv)

    app.add_handler(CommandHandler('help', commands.cmd_help))
    app.add_handler(CommandHandler('shop', commands.cmd_shop))
    app.add_handler(CommandHandler('search', commands.cmd_search))
    app.add_handler(CommandHandler('orders', commands.cmd_orders))
    app.add_handler(CommandHandler('track', commands.cmd_track))
    app.add_handler(CommandHandler('balance', commands.cmd_balance))
    app.add_handler(CommandHandler('store', commands.cmd_store))
    app.add_handler(CommandHandler('support', commands.cmd_support))
    app.add_handler(CommandHandler('add', commands.cmd_add))
    app.add_handler(CommandHandler('cart', commands.cmd_cart))
    app.add_handler(CommandHandler('unsubscribe', commands.cmd_unsubscribe))
    app.add_handler(CommandHandler('stats', commands.cmd_stats))
    app.add_handler(CommandHandler('pending', commands.cmd_pending))
    app.add_handler(CommandHandler('broadcast', commands.cmd_broadcast))
    app.add_handler(CallbackQueryHandler(commands.shop_callback, pattern=r'^(shop:|shopcat:|trk:)'))
    app.add_handler(InlineQueryHandler(inline.inline_query))
    app.add_handler(MessageHandler(filters.Regex(r'^!price\s+'), groups.group_price_command))

    logger.info('EthioShop bot starting (polling)...')
    app.run_polling()


if __name__ == '__main__':
    main()
