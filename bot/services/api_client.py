"""Async HTTP client for EthioShop backend API."""
import logging

import aiohttp

from bot.config import API_BASE_URL, BOT_SECRET

logger = logging.getLogger(__name__)

API_ROOT = API_BASE_URL.rstrip('/') + '/api'


class APIClient:
    def __init__(self, session: aiohttp.ClientSession | None = None):
        self._session = session
        self._owns_session = session is None

    def _bot_headers(self) -> dict:
        headers = {}
        if BOT_SECRET and BOT_SECRET != 'change_me':
            headers['X-Bot-Secret'] = BOT_SECRET
        return headers

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._owns_session and self._session:
            await self._session.close()
            self._session = None

    async def _request(self, method: str, path: str, **kwargs) -> dict | list | None:
        url = f"{API_ROOT}{path}"
        headers = kwargs.pop('headers', {})
        headers.update(self._bot_headers())
        try:
            session = await self._get_session()
            async with session.request(
                method, url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
                **kwargs
            ) as resp:
                if resp.status >= 400:
                    logger.warning('API %s %s -> %s', method, path, resp.status)
                    return None
                data = await resp.json()
                if isinstance(data, dict) and data.get('success') is False:
                    return None
                return data
        except Exception as e:
            logger.error('API error %s %s: %s', method, path, e)
            return None

    async def get_products(
        self,
        search: str | None = None,
        category: str | None = None,
        page: int = 1,
        limit: int = 10,
    ) -> dict | None:
        params = {'page': page, 'limit': limit}
        if search:
            params['search'] = search
        if category:
            params['category'] = category
        return await self._request('GET', '/products', params=params)

    async def get_categories(self) -> list[str]:
        data = await self._request('GET', '/products/categories')
        if not data:
            return []
        return data.get('categories', [])

    async def get_user_by_phone(self, phone: str) -> dict | None:
        data = await self._request('GET', f'/users/{phone}')
        return data.get('user') if data else None

    async def get_user_by_chat_id(self, chat_id: str | int) -> str | None:
        data = await self._request('GET', f'/users/by-chat-id/{chat_id}')
        return data.get('phone') if data else None

    async def get_user_orders(self, phone: str) -> list | None:
        data = await self._request('GET', f'/users/{phone}/orders')
        return data.get('orders') if data else None

    async def get_order(self, order_id: int) -> dict | None:
        data = await self._request('GET', f'/orders/{order_id}')
        return data.get('order') if data else None

    async def verify_order_ownership(self, order_id: int, phone: str) -> bool:
        order = await self.get_order(order_id)
        if not order:
            return False
        return order.get('user_phone') == phone

    async def register_user(self, phone: str, name: str, referral_code: str | None = None) -> dict | None:
        payload = {'phone': phone, 'name': name}
        if referral_code:
            payload['referral_code'] = referral_code
        data = await self._request('POST', '/users', json=payload)
        return data.get('user') if data else None

    async def link_telegram(self, phone: str, chat_id: int | str) -> bool:
        data = await self._request(
            'POST',
            '/users/link-telegram',
            json={'phone': phone, 'chat_id': str(chat_id)},
        )
        return data is not None and data.get('success', True)

    async def upload_payment_proof(self, file_bytes: bytes, filename: str = 'proof.jpg') -> str | None:
        try:
            session = await self._get_session()
            form = aiohttp.FormData()
            form.add_field('file', file_bytes, filename=filename, content_type='image/jpeg')
            form.add_field('folder', 'payment_proofs')
            url = f"{API_ROOT}/upload/image"
            async with session.post(url, data=form, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                data = await resp.json()
                if resp.status == 200 and data.get('success'):
                    return data.get('url')
        except Exception as e:
            logger.error('upload_payment_proof: %s', e)
        return None

    async def attach_payment_proof(self, order_id: int, image_url: str, phone: str) -> bool:
        data = await self._request(
            'PATCH',
            f'/orders/{order_id}/payment-proof',
            json={'payment_proof_url': image_url, 'phone': phone},
        )
        return data is not None

    async def bot_add_cart(self, phone: str, product_id: int, quantity: int) -> bool:
        data = await self._request('POST', '/users/bot/cart', json={'phone': phone, 'product_id': product_id, 'quantity': quantity})
        return data is not None

    async def bot_get_cart(self, phone: str) -> dict | None:
        return await self._request('GET', '/users/bot/cart', params={'phone': phone})

    async def bot_clear_cart(self, phone: str) -> bool:
        data = await self._request('DELETE', '/users/bot/cart', params={'phone': phone})
        return data is not None

    async def bot_unsubscribe(self, chat_id: int | str) -> bool:
        data = await self._request('POST', '/users/bot/unsubscribe', json={'chat_id': str(chat_id)})
        return data is not None

    async def bot_stats(self) -> dict | None:
        return await self._request('GET', '/admin/bot/stats')

    async def bot_pending(self) -> dict | None:
        return await self._request('GET', '/admin/bot/pending')

    async def bot_checkout(
        self,
        chat_id: str | int,
        delivery_location: dict,
        payment_plan: str = 'half',
        notes: str = '',
    ) -> dict:
        url = f'{API_ROOT}/bot/checkout'
        headers = self._bot_headers()
        headers['Content-Type'] = 'application/json'
        payload = {
            'chat_id': str(chat_id),
            'delivery_location': delivery_location,
            'payment_plan': payment_plan,
            'notes': notes,
        }
        try:
            session = await self._get_session()
            async with session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                data = await resp.json()
                if resp.status == 201 and data.get('order_id'):
                    return data
                return {
                    'success': False,
                    'message': data.get('message') or data.get('error', {}).get('message') or 'Checkout failed',
                }
        except Exception as e:
            logger.error('bot_checkout: %s', e)
            return {'success': False, 'message': str(e)}
