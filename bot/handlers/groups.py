"""Group chat handlers."""
import re

from telegram import Update
from telegram.ext import ContextTypes

from services.api_client import APIClient

PRICE_CMD = re.compile(r'^!price\s+(.+)', re.IGNORECASE)


async def group_price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    match = PRICE_CMD.match(update.message.text.strip())
    if not match:
        return

    keyword = match.group(1).strip()
    api: APIClient = context.application.bot_data['api']
    data = await api.get_products(search=keyword, page=1, limit=3)

    if not data or not data.get('items'):
        await update.message.reply_text(f'No products found for "{keyword}".')
        return

    lines = []
    for p in data['items']:
        lines.append(f"*{p['name']}* — {p['price']:.2f} ETB (ID: {p['id']})")

    await update.message.reply_text(
        f'💰 Price check for "{keyword}":\n\n' + '\n'.join(lines),
        parse_mode='Markdown',
    )
