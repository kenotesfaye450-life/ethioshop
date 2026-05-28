# EthioShop — Local testing links

## 1. Start services

**Terminal 1 — Backend API**
```powershell
cd C:\Users\kenot\Desktop\ethioshop
$env:PYTHONPATH="C:\Users\kenot\Desktop\ethioshop"
backend\venv\Scripts\python backend\app.py
```
Health: http://localhost:5000/health

**Terminal 2 — Frontend (static server)**
```powershell
cd C:\Users\kenot\Desktop\ethioshop\frontend
python -m http.server 5500
```

> If you see `WinError 10013` on port 8080, Windows has that port reserved. Use **5500** or **8888** instead.

**Terminal 3 — Telegram bot**
```powershell
cd C:\Users\kenot\Desktop\ethioshop\bot
python main.py
```

Ensure `bot/.env` and `backend/.env` share the same `BOT_SECRET` value.

---

## 2. Customer panel (full flow)

| Step | URL |
|------|-----|
| 1. Login / Register | http://localhost:5500/index.html |
| 2. Shop | http://localhost:5500/shop.html |
| 2b. Product detail | http://localhost:5500/product.html?id=1 |
| 2c. Referral link test | http://localhost:5500/index.html?ref=YOUR_CODE |
| 3. Cart | http://localhost:5500/cart.html |
| 4. Checkout | http://localhost:5500/checkout.html |
| 5. Order success | http://localhost:5500/order-success.html?id=1 |
| 6. Dashboard | http://localhost:5500/dashboard.html |
| 6b. My Requests | http://localhost:5500/my-requests.html |
| 6c. About | http://localhost:5500/about.html |
| 6d. Upload evidence | http://localhost:5500/upload-evidence.html?order_id=1 |
| 7. Track orders | http://localhost:5500/status.html |
| 8. Request product | http://localhost:5500/request.html |

**Customer flow:** Register (name + phone) or Login → Shop → Cart → Checkout → Payment proof → Dashboard.

**New customer on Telegram:** `/start` → share phone → type full name → account created & linked.

---

## 3. Admin panel (full flow)

| Step | URL |
|------|-----|
| 1. Admin login | http://localhost:5500/admin/index.html |
| 2. Orders | http://localhost:5500/admin/orders.html |
| 3. Products | http://localhost:5500/admin/products.html |
| 4. Customer requests | http://localhost:5500/admin/requests.html |
| 5. Dashboard | http://localhost:5500/admin/dashboard.html |
| 6. Admins | http://localhost:5500/admin/admins.html |
| 7. Refunds | http://localhost:5500/admin/refunds.html |
| 8. Site settings | http://localhost:5500/admin/settings.html |

**Default admin (after `init_db.py`):**
- Username: `KenoEthioShop`
- Phone: `0965806907`
- Password: `Wisdomlife1@9`

**Admin flow:** Login → Orders (verify payment, assign delivery) → Products (CRUD) → Dashboard (stats).

---

## 4. Telegram bot

- Bot: https://t.me/EthioShopTrusted_bot
- `/start` → share phone → `/shop`, `/orders`, `/balance`, `/track <id>`, `/pay`

---

## 5. API quick checks

- Health: `GET http://localhost:5000/health`
- Products: `GET http://localhost:5000/api/products`
- Categories: `GET http://localhost:5000/api/products/categories`
- Admin login: `POST http://localhost:5000/api/admin/login`

**One-time DB migration (multiple product images):**
```powershell
cd C:\Users\kenot\Desktop\ethioshop
$env:PYTHONPATH="C:\Users\kenot\Desktop\ethioshop"
backend\venv\Scripts\python add_product_images_table.py
backend\venv\Scripts\python add_enhancement_columns.py
```
