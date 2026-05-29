"""Telegram bot command handlers."""
import logging
import os as _os
import re
import sys

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
    WebAppInfo,
)
from config import WEB_APP_URL, ADMIN_CHAT_ID
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

from services.api_client import APIClient
from handlers.keyboards import MAIN_MENU_KEYBOARD, MENU_TEXT_TO_COMMAND, product_inline_buttons, shop_nav_buttons

logger = logging.getLogger(__name__)

AWAITING_CONTACT = 1
AWAITING_REGISTER_NAME = 2
CHECKOUT_ADDRESS = 10
CHECKOUT_CITY = 11
CHECKOUT_CONFIRM = 12
PAGE_SIZE = 5

_BACKEND = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))), 'backend')
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)
from utils.validators import normalize_ethiopian_phone


def _normalize_phone(raw: str) -> str:
    try:
        return normalize_ethiopian_phone(raw or '')
    except ValueError:
        return (raw or '').strip()


def _split_text_chunks(text: str, max_len: int = 4096) -> list:
    text = text or ''
    if len(text) <= max_len:
        return [text]
    chunks = []
    rest = text
    while rest:
        if len(rest) <= max_len:
            chunks.append(rest)
            break
        cut = rest.rfind(' ', 0, max_len)
        if cut <= 0:
            cut = max_len
        chunks.append(rest[:cut].rstrip())
        rest = rest[cut:].lstrip()
    return chunks


def _api(context: ContextTypes.DEFAULT_TYPE) -> APIClient:
    return context.application.bot_data['api']


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str | None:
    """Resolve phone from session or database (survives bot restart)."""
    if context.user_data.get('phone'):
        return context.user_data['phone']

    chat_id = str(update.effective_chat.id)
    api = _api(context)
    phone = await api.get_user_by_chat_id(chat_id)
    if phone:
        context.user_data['phone'] = phone
        return phone
    return None


async def _maybe_send_announcement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api = _api(context)
    data = await api.get_announcement()
    if not data or not data.get('announcement', {}).get('announcement_active'):
        return
    msg = data['announcement'].get('announcement_message', '')
    if msg:
        for chunk in _split_text_chunks(f'📢 {msg}'):
            await update.message.reply_text(chunk)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton('📱 Share my phone number', request_contact=True)]],
        one_time_keyboard=True,
        resize_keyboard=True,
    )
    await update.message.reply_text(
        '👋 Welcome to EthioShop!\n\n'
        'Share your phone number to log in or register.\n'
        'New customers: we will ask for your full name next.',
        reply_markup=keyboard,
    )
    await _maybe_send_announcement(update, context)
    return AWAITING_CONTACT


async def receive_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    chat_id = update.effective_chat.id
    phone = _normalize_phone(contact.phone_number if contact else '')
    api = _api(context)

    if await api.link_telegram(phone, chat_id):
        context.user_data['phone'] = phone
        await update.message.reply_text(
            '✅ Phone linked successfully!\n\n'
            'Use the menu below or /shop to browse.',
            reply_markup=MAIN_MENU_KEYBOARD,
        )
        await _maybe_send_announcement(update, context)
        return ConversationHandler.END

    # Existing user in DB but not linked yet — register path not needed
    user = await api.get_user_by_phone(phone)
    if user:
        if await api.link_telegram(phone, chat_id):
            context.user_data['phone'] = phone
            await update.message.reply_text(
                f"✅ Welcome back, {user.get('name') or 'customer'}! Phone linked.",
                reply_markup=MAIN_MENU_KEYBOARD,
            )
            await _maybe_send_announcement(update, context)
            return ConversationHandler.END

    context.user_data['pending_phone'] = phone
    context.user_data['pending_chat_id'] = chat_id
    await update.message.reply_text(
        '📝 New customer — please type your **full name** to create an account:\n'
        '(e.g. Keno Tesfaye)',
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown',
    )
    return AWAITING_REGISTER_NAME


async def receive_register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = (update.message.text or '').strip()
    if len(name) < 2:
        await update.message.reply_text('Please enter your full name (at least 2 characters).')
        return AWAITING_REGISTER_NAME

    phone = context.user_data.get('pending_phone')
    chat_id = context.user_data.get('pending_chat_id')
    if not phone or not chat_id:
        await update.message.reply_text('Session expired. Please send /start again.')
        return ConversationHandler.END

    api = _api(context)
    user = await api.register_user(phone, name)
    if not user:
        await update.message.reply_text(
            '❌ Registration failed. Try again or register on the website first.'
        )
        return ConversationHandler.END

    if await api.link_telegram(phone, chat_id):
        context.user_data['phone'] = phone
        await update.message.reply_text(
            f"✅ Account created for *{name}*!\n"
            f"Your referral code: `{user.get('referral_code', '-')}`",
            parse_mode='Markdown',
            reply_markup=MAIN_MENU_KEYBOARD,
        )
        await _maybe_send_announcement(update, context)
    else:
        await update.message.reply_text(
            f'✅ Account created, but Telegram link failed. Run /start again.'
        )
    return ConversationHandler.END


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Cancelled.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '🛍️ EthioShop Bot\n\n'
        '/start — Register or link phone\n'
        '/shop — Browse products\n'
        '/search <keyword> — Search products\n'
        '/orders — Your order history\n'
        '/track <order_id> — Track an order\n'
        '/balance — Credit balance\n'
        '/pay — Upload payment proof\n'
        '/add <id> <qty> — Add to cart\n'
        '/cart — View persistent cart\n'
        '/checkout — Create order from cart\n'
        '/unsubscribe — Stop bot notifications\n'
        '/store — Open web shop (Mini App)\n'
        '/support <msg> — Contact support\n'
        '/help — This message'
    )


async def cmd_store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shop_url = WEB_APP_URL.rstrip('/')
    if not shop_url.endswith('.html'):
        shop_url = f'{shop_url}/shop.html'
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton('🛒 Open EthioShop', web_app=WebAppInfo(url=shop_url)),
    ]])
    await update.message.reply_text(
        '🛒 Open the shop in Telegram or browse with inline search:\n'
        'Type @EthioShopTrusted_bot <product name> in any chat.',
        reply_markup=keyboard,
    )


async def cmd_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forward support messages to admin chat."""
    phone = await get_phone(update, context)
    user = update.effective_user
    text = ' '.join(context.args).strip() if context.args else ''
    if not text:
        await update.message.reply_text(
            'Usage: /support <your message>\n'
            'Example: /support I need help with order #12'
        )
        return
    if ADMIN_CHAT_ID:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=(
                f"🆘 Support from {user.full_name} (@{user.username or 'n/a'})\n"
                f"Phone: {phone or 'not linked'}\n"
                f"Chat ID: {update.effective_chat.id}\n\n{text}"
            ),
        )
        await update.message.reply_text('✅ Your message was sent to support. We will reply soon.')
    else:
        await update.message.reply_text('Support is unavailable right now. Try the website dashboard.')


async def _send_products(update: Update, context: ContextTypes.DEFAULT_TYPE, search: str | None = None, page: int = 1):
    api = _api(context)
    data = await api.get_products(search=search, page=page, limit=PAGE_SIZE)
    if not data or not data.get('items'):
        target = update.message or update.callback_query.message
        await target.reply_text('No products found.')
        return

    items = data['items']
    lines = []
    buttons = []
    for p in items:
        stock = '✅' if p.get('in_stock') else '❌'
        lines.append(f"{stock} *{p['name']}* — {p['price']:.2f} ETB")
        buttons.append(product_inline_buttons(p))
    nav = shop_nav_buttons(search, page, data.get('pages', 1))
    if nav:
        buttons.append(nav)

    text = '🛍️ *Products*\n\n' + '\n\n'.join(lines)
    target = update.message or update.callback_query.message
    await target.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(buttons) if buttons else None,
    )


async def cmd_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api = _api(context)
    cats = await api.get_categories()
    if not cats:
        await _send_products(update, context, page=1)
        return
    keyboard = []
    for c in cats[:12]:
        keyboard.append([InlineKeyboardButton(c, callback_data=f'shopcat:{c}:1')])
    await update.message.reply_text('Choose category:', reply_markup=InlineKeyboardMarkup(keyboard))


async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = ' '.join(context.args).strip() if context.args else ''
    if not query:
        await update.message.reply_text('Usage: /search shoes')
        return
    await _send_products(update, context, search=query, page=1)


async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith('trk:'):
        order_id = int(query.data.split(':', 1)[1])
        phone = await get_phone(update, context)
        if not phone:
            await query.edit_message_text('Link your phone first with /start')
            return
        api = _api(context)
        if not await api.verify_order_ownership(order_id, phone):
            await query.edit_message_text('❌ This order does not belong to you.')
            return
        order = await api.get_order(order_id)
        if not order:
            await query.edit_message_text('Order not found.')
            return
        await query.edit_message_text(
            f"📦 Order #{order['id']}\n"
            f"Status: {order['status']}\n"
            f"Delivery: {order['delivery_status']}\n"
            f"Total: {order['final_total']:.2f} ETB"
        )
        return
    if query.data.startswith('shopcat:'):
        _, category, page = query.data.split(':', 2)
        api = _api(context)
        data = await api.get_products(category=category, page=int(page), limit=PAGE_SIZE)
        items = data.get('items') if data else []
        if not items:
            await query.edit_message_text('No products found in this category.')
            return
        lines = [f"{'✅' if p.get('in_stock') else '❌'} *{p['name']}* — {p['price']:.2f} ETB\nUse /add {p['id']} 1" for p in items]
        pg = int(page)
        buttons = []
        nav = []
        if pg > 1:
            nav.append(InlineKeyboardButton('◀ Prev', callback_data=f'shopcat:{category}:{pg - 1}'))
        if data and pg < data.get('pages', 1):
            nav.append(InlineKeyboardButton('Next ▶', callback_data=f'shopcat:{category}:{pg + 1}'))
        if nav:
            buttons.append(nav)
        await query.edit_message_text(
            '\n\n'.join(lines),
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(buttons) if buttons else None,
        )
        return
    _, search, page = query.data.split(':', 2)
    search = search or None
    api = _api(context)
    data = await api.get_products(search=search, page=int(page), limit=PAGE_SIZE)
    if not data or not data.get('items'):
        await query.edit_message_text('No products found.')
        return

    items = data['items']
    lines = [f"{'✅' if p.get('in_stock') else '❌'} *{p['name']}* — {p['price']:.2f} ETB" for p in items]
    text = '🛍️ *Products*\n\n' + '\n\n'.join(lines)
    buttons = []
    nav = []
    pg = int(page)
    if pg > 1:
        nav.append(InlineKeyboardButton('◀ Prev', callback_data=f'shop:{search or ""}:{pg - 1}'))
    if pg < data.get('pages', 1):
        nav.append(InlineKeyboardButton('Next ▶', callback_data=f'shop:{search or ""}:{pg + 1}'))
    if nav:
        buttons.append(nav)
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(buttons) if buttons else None)


async def cmd_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = await get_phone(update, context)
    if not phone:
        await update.message.reply_text('Link your phone first with /start')
        return

    api = _api(context)
    orders = await api.get_user_orders(phone)
    if not orders:
        await update.message.reply_text('No orders yet.')
        return

    buttons = [[InlineKeyboardButton(f"Order #{o['id']} • {o['status']}", callback_data=f"trk:{o['id']}")] for o in orders[:10]]
    await update.message.reply_text('📦 *Your Orders*', parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(buttons))


async def cmd_track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text('Usage: /track <order_id>')
        return

    try:
        order_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text('Invalid order ID.')
        return

    phone = await get_phone(update, context)
    if not phone:
        await update.message.reply_text('Link your phone first with /start')
        return

    api = _api(context)
    if not await api.verify_order_ownership(order_id, phone):
        await update.message.reply_text('❌ This order does not belong to you.')
        return

    order = await api.get_order(order_id)
    if not order:
        await update.message.reply_text('Order not found.')
        return

    await update.message.reply_text(
        f"📦 Order #{order['id']}\n"
        f"Status: {order['status']}\n"
        f"Delivery: {order['delivery_status']}\n"
        f"Total: {order['final_total']:.2f} ETB"
    )


async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = await get_phone(update, context)
    if not phone:
        await update.message.reply_text('Link your phone first with /start')
        return

    api = _api(context)
    user = await api.get_user_by_phone(phone)
    if not user:
        await update.message.reply_text('User not found.')
        return

    link = f"{WEB_APP_URL.rstrip('/')}/?ref={user['referral_code']}"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton('🔗 Copy referral link', callback_data='ref:copy')]])
    await update.message.reply_text(
        f"💰 Credit balance: *{user['credit_balance']:.2f} ETB*\n"
        f"Referral code: `{user['referral_code']}`\n"
        f"Referrals: {user['total_referrals']}\n"
        f"Link: {link}",
        parse_mode='Markdown',
        reply_markup=kb,
    )


async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = await get_phone(update, context)
    if not phone:
        await update.message.reply_text('Link your phone first with /start')
        return
    if len(context.args) < 2:
        await update.message.reply_text('Usage: /add <product_id> <quantity>')
        return
    try:
        product_id = int(context.args[0])
        quantity = max(int(context.args[1]), 1)
    except ValueError:
        await update.message.reply_text('Invalid product ID or quantity.')
        return
    ok = await _api(context).bot_add_cart(phone, product_id, quantity)
    await update.message.reply_text('✅ Added to cart.' if ok else '❌ Failed to add to cart.')


async def _cart_keyboard(data: dict) -> InlineKeyboardMarkup:
    buttons = []
    for i in data.get('items', []):
        pid = i['product_id']
        buttons.append([
            InlineKeyboardButton('+1', callback_data=f'cart:inc:{pid}'),
            InlineKeyboardButton('-1', callback_data=f'cart:dec:{pid}'),
            InlineKeyboardButton('❌ Remove', callback_data=f'cart:remove:{pid}'),
        ])
    buttons.append([
        InlineKeyboardButton('✅ Checkout', callback_data='cart:checkout'),
        InlineKeyboardButton('🗑️ Clear cart', callback_data='cart:clear'),
    ])
    return InlineKeyboardMarkup(buttons)


async def refresh_cart_message(query, context, phone):
    data = await _api(context).bot_get_cart(phone)
    if not data or not data.get('items'):
        await query.edit_message_text('Your cart is empty.')
        return
    lines = [f"{i['name']} x{i['quantity']} — {i['line_total']:.2f} ETB" for i in data['items']]
    await query.edit_message_text(
        "🛒 *Your cart*\n\n" + "\n".join(lines) + f"\n\nTotal: *{data.get('total', 0):.2f} ETB*",
        parse_mode='Markdown',
        reply_markup=await _cart_keyboard(data),
    )


async def cmd_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = await get_phone(update, context)
    if not phone:
        await update.message.reply_text('Link your phone first with /start')
        return
    data = await _api(context).bot_get_cart(phone)
    if not data or not data.get('items'):
        await update.message.reply_text('Your cart is empty.')
        return
    lines = [f"{i['name']} x{i['quantity']} — {i['line_total']:.2f} ETB" for i in data['items']]
    await update.message.reply_text(
        "🛒 *Your cart*\n\n" + "\n".join(lines) + f"\n\nTotal: *{data.get('total', 0):.2f} ETB*",
        parse_mode='Markdown',
        reply_markup=await _cart_keyboard(data),
    )


async def checkout_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    api = _api(context)
    phone = await api.get_user_by_chat_id(chat_id)
    if not phone:
        await update.message.reply_text('Please link your phone first using /start.')
        return ConversationHandler.END

    cart = await api.bot_get_cart(phone)
    if not cart or not cart.get('items'):
        await update.message.reply_text('Your cart is empty. Add items with /add <product_id> <quantity>.')
        return ConversationHandler.END

    context.user_data['checkout_chat_id'] = chat_id
    context.user_data['checkout_phone'] = phone
    await update.message.reply_text(
        "Let's create an order from your cart.\n\n"
        'Enter your delivery address (e.g. Addis Ababa, Bole, near Friendship Park):'
    )
    return CHECKOUT_ADDRESS


async def checkout_address_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['delivery_address'] = (update.message.text or '').strip()
    await update.message.reply_text(
        'Great. Now enter your city (or send /skip to use the address as city):'
    )
    return CHECKOUT_CITY


async def checkout_city_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['delivery_city'] = (update.message.text or '').strip()
    return await _checkout_show_summary(update, context)


async def checkout_skip_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['delivery_city'] = context.user_data.get('delivery_address', '')
    return await _checkout_show_summary(update, context)


async def _checkout_show_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = context.user_data.get('delivery_address', '')
    city = context.user_data.get('delivery_city', '')
    context.user_data['delivery_location'] = {'address': address, 'city': city}

    api = _api(context)
    cart = await api.bot_get_cart(context.user_data.get('checkout_phone', ''))
    if not cart or not cart.get('items'):
        await update.message.reply_text('Your cart is empty.')
        return ConversationHandler.END

    total = cart.get('total', 0)
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('✅ Confirm order', callback_data='chk:yes'),
            InlineKeyboardButton('❌ Cancel', callback_data='chk:no'),
        ],
    ])
    await update.message.reply_text(
        f'Order summary:\n'
        f'Delivery: {address}, {city}\n'
        f'Total: {total:.2f} ETB (half payment on first installment)',
        parse_mode='Markdown',
        reply_markup=kb,
    )
    return CHECKOUT_CONFIRM


async def _run_bot_checkout(update, context, query=None):
    api = _api(context)
    result = await api.bot_checkout(
        chat_id=context.user_data['checkout_chat_id'],
        delivery_location=context.user_data.get('delivery_location', {}),
        payment_plan='half',
    )
    msg = (
        f"Order #{result['order_id']} created!\n"
        f"Pay the first half ({result.get('amount_paid_etb', 0):.2f} ETB) and upload proof: /pay"
        if result.get('order_id')
        else f"Failed: {result.get('message', 'Unknown error')}"
    )
    if query:
        await query.edit_message_text(msg)
    else:
        await update.message.reply_text(msg)


async def checkout_confirm_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return ConversationHandler.END


async def checkout_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Checkout cancelled.')
    return ConversationHandler.END


async def cmd_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok = await _api(context).bot_unsubscribe(update.effective_chat.id)
    await update.message.reply_text('You are unsubscribed from bot notifications.' if ok else 'Unable to unsubscribe now.')


def _is_admin_chat(update: Update) -> bool:
    return str(update.effective_chat.id) == str(ADMIN_CHAT_ID or '')


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin_chat(update):
        await update.message.reply_text('Admin only.')
        return
    data = await _api(context).bot_stats()
    if not data or not data.get('success'):
        await update.message.reply_text('Could not fetch stats.')
        return
    s = data['stats']
    await update.message.reply_text(f"📊 Sales today: {s.get('total_sales_today_etb', 0):.2f} ETB\nPending orders: {s.get('pending_orders', 0)}")


async def cmd_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin_chat(update):
        await update.message.reply_text('Admin only.')
        return
    data = await _api(context).bot_pending()
    if not data or not data.get('success'):
        await update.message.reply_text('Could not fetch pending orders.')
        return
    ids = data.get('order_ids', [])
    await update.message.reply_text('Pending IDs: ' + (', '.join(str(i) for i in ids) if ids else 'none'))


async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin_chat(update):
        await update.message.reply_text('Admin only.')
        return
    text = ' '.join(context.args).strip()
    if not text:
        await update.message.reply_text('Usage: /broadcast <message>')
        return
    import sys
    import os
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    backend = os.path.join(root, 'backend')
    if backend not in sys.path:
        sys.path.insert(0, backend)
    from app import create_app
    from models import TelegramUser
    sent = 0
    app = create_app()
    with app.app_context():
        users = TelegramUser.query.filter(~TelegramUser.chat_id.like('unsubscribed:%')).all()
        for tg in users:
            try:
                await context.bot.send_message(chat_id=tg.chat_id, text=f"📣 {text}")
                sent += 1
            except Exception:
                continue
    await update.message.reply_text(f'Broadcast sent to {sent} users.')


async def handle_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or '').strip().lower()
    cmd = MENU_TEXT_TO_COMMAND.get(text)
    if cmd == 'shop':
        await cmd_shop(update, context)
    elif cmd == 'cart':
        await cmd_cart(update, context)
    elif cmd == 'orders':
        await cmd_orders(update, context)
    elif cmd == 'balance':
        await cmd_balance(update, context)
    elif cmd == 'help':
        await cmd_help(update, context)


NL_INTENTS = {
    'help': 'help',
    'start': 'start',
    'shop': 'shop',
    'cart': 'cart',
    'orders': 'orders',
    'balance': 'balance',
}


async def handle_natural_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or '').strip()
    if not text or text.startswith('/'):
        return
    if text.lower() in MENU_TEXT_TO_COMMAND:
        return
    intent = NL_INTENTS.get(text.lower())
    if intent:
        if intent == 'help':
            await cmd_help(update, context)
        elif intent == 'start':
            await cmd_start(update, context)
        elif intent == 'shop':
            await cmd_shop(update, context)
        elif intent == 'cart':
            await cmd_cart(update, context)
        elif intent == 'orders':
            await cmd_orders(update, context)
        elif intent == 'balance':
            await cmd_balance(update, context)
        return
    phone = await get_phone(update, context)
    if not phone:
        await update.message.reply_text('Please /start and share your phone first.')
        return
    await _send_products(update, context, search=text, page=1)
