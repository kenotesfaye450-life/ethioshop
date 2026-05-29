"""Unified inline callback handler for the bot."""
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from handlers.commands import get_phone, _api, PAGE_SIZE, checkout_start
from handlers.keyboards import product_inline_buttons, shop_nav_buttons
from config import WEB_APP_URL

logger = logging.getLogger(__name__)


async def _show_products_message(query, items, search, page, data, prefix='shop'):
    lines = []
    buttons = []
    for p in items:
        stock = '✅' if p.get('in_stock') else '❌'
        lines.append(f"{stock} *{p['name']}* — {p['price']:.2f} ETB")
        buttons.append(product_inline_buttons(p))
    nav = shop_nav_buttons(search, page, data.get('pages', 1), prefix=prefix)
    if nav:
        buttons.append(nav)
    title = '🛍️ *Products*' if prefix == 'shop' else f'📂 *{prefix.split(":")[1] if ":" in prefix else ""}*'
    await query.edit_message_text(
        '\n\n'.join(lines) if lines else 'No products.',
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(buttons) if buttons else None,
    )


async def _show_order_track(query, order, phone, api):
    remaining = max(float(order.get('final_total', 0)) - float(order.get('amount_paid', 0)), 0)
    text = (
        f"📦 *Order #{order['id']}*\n"
        f"Status: {order['status']}\n"
        f"Payment: {order.get('payment_status', '-')}\n"
        f"Delivery: {order['delivery_status']}\n"
        f"Total: {order['final_total']:.2f} ETB\n"
        f"Paid: {order.get('amount_paid', 0):.2f} ETB"
    )
    if remaining > 0:
        text += f"\nRemaining: {remaining:.2f} ETB"
    buttons = []
    if order.get('payment_status') == 'partial' and remaining > 0:
        buttons.append([InlineKeyboardButton('💰 Pay remaining', callback_data=f'pay:{order["id"]}')])
    if order.get('delivery_status') == 'in_transit' and order.get('payment_status') == 'paid':
        buttons.append([InlineKeyboardButton('🚚 Confirm delivery', callback_data=f'del:{order["id"]}')])
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(buttons) if buttons else None,
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ''
    api = _api(context)
    phone = await get_phone(update, context)

    if data.startswith('trk:'):
        order_id = int(data.split(':', 1)[1])
        if not phone:
            await query.edit_message_text('Link your phone with /start first.')
            return
        if not await api.verify_order_ownership(order_id, phone):
            await query.edit_message_text('❌ This order is not yours.')
            return
        order = await api.get_order(order_id)
        if not order:
            await query.edit_message_text('Order not found.')
            return
        await _show_order_track(query, order, phone, api)
        return

    if data.startswith('add:'):
        if not phone:
            await query.edit_message_text('Use /start to link your phone first.')
            return
        _, pid, qty = data.split(':')
        ok = await api.bot_add_cart(phone, int(pid), int(qty))
        await query.answer('Added to cart!' if ok else 'Failed', show_alert=not ok)
        return

    if data.startswith('det:'):
        pid = int(data.split(':', 1)[1])
        prod = await api.get_product(pid)
        if not prod:
            await query.edit_message_text('Product not found.')
            return
        p = prod.get('product') or prod
        text = (
            f"*{p.get('name')}*\n"
            f"Price: {p.get('price', 0):.2f} ETB\n"
            f"Stock: {p.get('stock', 0)}\n"
            f"{(p.get('description') or '')[:400]}"
        )
        kb = InlineKeyboardMarkup([product_inline_buttons({'id': p['id']})])
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=kb)
        return

    if data.startswith('cart:'):
        if not phone:
            await query.edit_message_text('Link phone with /start.')
            return
        parts = data.split(':')
        sub = parts[1]
        if sub == 'clear':
            await api.bot_clear_cart(phone)
            await query.edit_message_text('Cart cleared.')
            return
        if sub == 'checkout':
            from handlers.commands import checkout_start
            fake = Update(update_id=update.update_id, message=query.message)
            await checkout_start(fake, context)
            return
        act, pid = sub, int(parts[2])
        await api.bot_update_cart(phone, pid, act)
        from handlers.commands import refresh_cart_message
        await refresh_cart_message(query, context, phone)
        return

    if data.startswith('pay:'):
        order_id = int(data.split(':', 1)[1])
        context.user_data['pay_phone'] = phone
        context.user_data['pay_order_id'] = order_id
        await query.edit_message_text(f'Order #{order_id}: send a *photo* of your payment proof.', parse_mode='Markdown')
        context.user_data['awaiting_pay_photo'] = True
        return

    if data.startswith('del:'):
        if not phone:
            await query.edit_message_text('Link phone with /start.')
            return
        order_id = int(data.split(':', 1)[1])
        ok = await api.confirm_delivery(order_id, phone)
        await query.edit_message_text(
            f'✅ Delivery confirmed for order #{order_id}.' if ok else 'Could not confirm delivery.'
        )
        return

    if data.startswith('chk:'):
        if data.endswith(':yes'):
            from handlers.commands import _run_bot_checkout
            await _run_bot_checkout(update, context, query=query)
        else:
            await query.edit_message_text('Checkout cancelled.')
        return

    if data.startswith('ref:copy'):
        if not phone:
            return
        user = await api.get_user_by_phone(phone)
        if user:
            link = f"{WEB_APP_URL.rstrip('/')}/?ref={user.get('referral_code', '')}"
            await query.edit_message_text(f'Your referral link:\n`{link}`', parse_mode='Markdown')
        return

    if data.startswith('shopcat:'):
        _, category, page = data.split(':', 2)
        pdata = await api.get_products(category=category, page=int(page), limit=PAGE_SIZE)
        items = pdata.get('items') if pdata else []
        if not items:
            await query.edit_message_text('No products in this category.')
            return
        await _show_products_message(query, items, None, int(page), pdata, prefix=f'shopcat:{category}')
        return

    if data.startswith('shop:'):
        _, search, page = data.split(':', 2)
        search = search or None
        pdata = await api.get_products(search=search, page=int(page), limit=PAGE_SIZE)
        items = pdata.get('items') if pdata else []
        if not items:
            await query.edit_message_text('No products found.')
            return
        await _show_products_message(query, items, search, int(page), pdata)
        return
