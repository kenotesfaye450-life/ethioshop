"""Telegram keyboard builders."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton('🛍️ Shop'), KeyboardButton('🛒 Cart')],
        [KeyboardButton('📦 Orders'), KeyboardButton('💰 Balance')],
        [KeyboardButton('ℹ️ Help')],
    ],
    resize_keyboard=True,
)

MENU_TEXT_TO_COMMAND = {
    '🛍️ shop': 'shop',
    '🛒 cart': 'cart',
    '📦 orders': 'orders',
    '💰 balance': 'balance',
    'ℹ️ help': 'help',
}


def product_inline_buttons(product: dict) -> list:
    pid = product['id']
    return [
        InlineKeyboardButton('➕ Add to cart', callback_data=f'add:{pid}:1'),
        InlineKeyboardButton('🔍 Details', callback_data=f'det:{pid}'),
    ]


def shop_nav_buttons(search: str | None, page: int, total_pages: int, prefix: str = 'shop') -> list:
    nav = []
    key = search or ''
    if page > 1:
        nav.append(InlineKeyboardButton('⏪ Previous', callback_data=f'{prefix}:{key}:{page - 1}'))
    if page < total_pages:
        nav.append(InlineKeyboardButton('Next ⏩', callback_data=f'{prefix}:{key}:{page + 1}'))
    return nav
