"""Inline query handler for product search."""
import logging
from uuid import uuid4

from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import ContextTypes

from services.api_client import APIClient

logger = logging.getLogger(__name__)


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = (update.inline_query.query or '').strip()
    api: APIClient = context.application.bot_data['api']

    data = await api.get_products(search=query or None, page=1, limit=20)
    results = []

    if data and data.get('items'):
        for p in data['items']:
            desc = (p.get('description') or '')[:200]
            price = p.get('price', 0)
            stock = 'In stock' if p.get('in_stock') else 'Out of stock'
            thumb = p.get('thumbnail_url') or p.get('image_url')

            results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=f"{p['name']} — {price:.2f} ETB",
                    description=f"{stock} | {p.get('category', '')}",
                    input_message_content=InputTextMessageContent(
                        f"🛍️ *{p['name']}*\n"
                        f"Price: {price:.2f} ETB\n"
                        f"Category: {p.get('category', 'N/A')}\n"
                        f"Product ID: {p['id']}\n"
                        f"{desc}",
                        parse_mode='Markdown',
                    ),
                    thumbnail_url=thumb,
                )
            )

    if not results:
        results.append(
            InlineQueryResultArticle(
                id='empty',
                title='No products found',
                description='Try another search term',
                input_message_content=InputTextMessageContent('No products found.'),
            )
        )

    await update.inline_query.answer(results, cache_time=30)
