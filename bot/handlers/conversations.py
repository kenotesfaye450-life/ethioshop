"""Conversation handlers (e.g. /pay payment proof upload)."""
import logging

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.handlers.commands import get_phone
from bot.services.api_client import APIClient

logger = logging.getLogger(__name__)

ASK_ORDER_ID, ASK_PHOTO = range(2)


def _api(context: ContextTypes.DEFAULT_TYPE) -> APIClient:
    return context.application.bot_data['api']


async def pay_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = await get_phone(update, context)
    if not phone:
        await update.message.reply_text('Link your phone first with /start')
        return ConversationHandler.END

    context.user_data['pay_phone'] = phone
    await update.message.reply_text('Enter your order ID:')
    return ASK_ORDER_ID


async def pay_order_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        order_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text('Please send a valid numeric order ID.')
        return ASK_ORDER_ID

    phone = context.user_data.get('pay_phone')
    api = _api(context)

    if not await api.verify_order_ownership(order_id, phone):
        await update.message.reply_text('❌ This order does not belong to you. Try another order ID.')
        return ASK_ORDER_ID

    context.user_data['pay_order_id'] = order_id
    await update.message.reply_text('Send a photo of your payment proof:')
    return ASK_PHOTO


async def pay_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text('Please send a photo.')
        return ASK_PHOTO

    order_id = context.user_data.get('pay_order_id')
    phone = context.user_data.get('pay_phone')
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_bytes = await file.download_as_bytearray()

    api = _api(context)
    url = await api.upload_payment_proof(bytes(file_bytes), filename=f'proof_{order_id}.jpg')
    if not url:
        await update.message.reply_text('❌ Failed to upload image. Try again later.')
        return ConversationHandler.END

    if await api.attach_payment_proof(order_id, url, phone):
        await update.message.reply_text(f'✅ Payment proof attached to order #{order_id}.')
    else:
        await update.message.reply_text(
            f'⚠️ Image uploaded but could not attach to order #{order_id}. '
            'Check the order ID and status (must be pending verification).'
        )
    return ConversationHandler.END


async def pay_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Payment upload cancelled.')
    return ConversationHandler.END
