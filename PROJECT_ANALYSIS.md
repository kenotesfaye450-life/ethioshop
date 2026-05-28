# EthioShop — Full Honest Project Analysis
# For any AI or developer new to this codebase

---

## WHAT THIS PROJECT IS

EthioShop is a real Ethiopian e-commerce system with three separate parts:
1. A Python/Flask REST API backend (the brain)
2. A plain HTML/JS customer-facing frontend (the shop)
3. A plain HTML/JS admin panel (the management tool)

There is no React, no Vue, no build step, no bundler.
The frontend and admin panel are static HTML files that call the backend API directly via fetch().
The backend connects to a Supabase PostgreSQL database hosted in the cloud.

Currency: Everything is stored in the database as INTEGER CENTS (Ethiopian Birr × 100).
Example: 2600 ETB is stored as 260000. All API responses divide by 100 before sending.

---

## CRITICAL FACTS EVERY AI MUST KNOW

1. All money values in the DB are in CENTS (ETB × 100). API returns ETB (divided by 100).
2. The DB is Supabase PostgreSQL. Direct host is IPv6-only on this machine.
   Working connection: host=aws-1-eu-central-1.pooler.supabase.com port=6543
   user=postgres.hoysrktwmrowdpihhxjj
3. The `db` object lives in extensions.py — NOT in app.py. This was fixed to break
   a circular import. Never move db back to app.py.
4. Backend runs on port 5000. Start command (from backend/ folder):
   venv\Scripts\python.exe app.py
5. Admin login requires THREE fields: username + phone + password (not just username+password).
6. Phone numbers must be Ethiopian format: 09XXXXXXXX or +251XXXXXXXXX or 251XXXXXXXXX
7. Minimum order is 500 ETB. Orders below this are rejected by the API.
8. Credit system: users earn 50 ETB credit when someone they referred places their
   first confirmed order. Credit can be used for max 50% of order value or 500 ETB max.
9. status.html is EMPTY — it does not exist/has no content. Order tracking by phone
   is only available in dashboard.html.
10. frontend/assets/js/app.js is EMPTY — it has no content.
11. frontend/assets/js/request.js is EMPTY — it has no content.
12. The Telegram notification service is NOT functional. It only prints to console.
    It does not actually send messages to users.
13. The bot/ folder exists but is completely empty (no handlers, no services).
    The Telegram bot is not implemented.

---

## FOLDER AND FILE MAP


---

## ROOT LEVEL FILES

### .env
The real secrets file for the ROOT of the project (not the backend).
Currently contains the same credentials as backend/.env.
The backend does NOT load this file — it loads backend/.env.
This file is a leftover from earlier attempts. The backend ignores it.
Keep it in sync with backend/.env manually if you change credentials.

Key values:
- DB_USER=postgres.hoysrktwmrowdpihhxjj
- DB_HOST=aws-1-eu-central-1.pooler.supabase.com
- DB_PORT=6543
- DB_PASSWORD=9Wisdomlife1@  (has @ symbol — handled by quote_plus in config.py)

### .env.example
Template showing what variables are needed. Safe to commit. No real secrets.

### .gitignore
Standard gitignore. Ignores .env files, venv/, __pycache__, etc.

### Procfile
Used by Heroku/Railway for deployment.
Content: web: cd backend && gunicorn wsgi:app
Tells the platform to run wsgi.py using gunicorn.
Not used locally.

### railway.json / render.yaml / vercel.json
Deployment config files for Railway, Render, and Vercel platforms.
None of these are currently active — the app is running locally only.
vercel.json is irrelevant (Vercel is for static sites / serverless, not Flask).

### database/ folder
EMPTY. Was probably intended for SQL migration scripts. Nothing is in it.

### docs/ folder
EMPTY. No documentation files inside.

---

## BACKEND FOLDER — THE ACTUAL SERVER

### backend/.env
The file the backend actually loads. This is the one that matters.
Loaded by config.py via python-dotenv's load_dotenv().
Contains all real credentials: DB, Cloudinary, Telegram, JWT secrets.

### backend/extensions.py
CRITICAL FILE. Created to fix a circular import bug.

What it does: Defines three Flask extension objects at module level:
- db = SQLAlchemy()       — the database ORM
- migrate = Migrate()     — handles DB schema migrations
- limiter = Limiter(...)  — rate limiting (1000/day, 100/hour per IP)

Why it exists separately: app.py creates the Flask app, models need db,
routes need db, and app.py imports routes. If db lived in app.py, importing
db in models would import app.py which imports routes which imports models
— infinite loop. extensions.py breaks this cycle.

RULE: Any file that needs db must do: from extensions import db

### backend/app.py
The Flask application factory. Does NOT run directly in production (wsgi.py does).
Can run directly for development: python app.py

What it actually does:
1. Imports db, migrate, limiter from extensions.py
2. Creates Flask app instance
3. Loads config from config.py (which reads backend/.env)
4. Calls db.init_app(app), migrate.init_app(app), limiter.init_app(app)
5. Adds ProxyFix middleware (for correct IP detection behind reverse proxies)
6. Adds Talisman (security headers — HTTPS forced only in production)
7. Adds CORS for /api/* routes
8. Defines two health check routes: GET / and GET /health
9. ALSO defines a duplicate GET /api/products route inline (redundant —
   the same endpoint exists in routes/products.py as a Blueprint)
10. Registers 7 Blueprints: products, orders, users, admin, upload, requests, refunds

KNOWN ISSUE: There are now TWO GET /api/products handlers — one inline in app.py
and one in routes/products.py. Flask will use the Blueprint one. The inline one
in app.py returns a different format (no success wrapper, uses selling_price directly
without /100 conversion). This is a bug — the inline route should be removed.


### backend/config.py
Reads all environment variables and exposes them as class attributes.

How DB URL is built:
- If DATABASE_URL env var exists → use it directly
- If not → build from DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
- Password is URL-encoded with quote_plus() to handle the @ symbol in "9Wisdomlife1@"
- Final URL format: postgresql+psycopg2://user:encoded_pass@host:port/dbname

Three config classes: DevelopmentConfig, StagingConfig, ProductionConfig
ConfigFactory.get() picks the right one based on FLASK_ENV env var.
Default is DevelopmentConfig (DEBUG=True, SESSION_COOKIE_SECURE=False).

Business rule constants (read from .env with defaults):
- MINIMUM_ORDER_ETB = 500  (minimum order value in ETB)
- MAX_CREDIT_PERCENTAGE = 0.5  (max 50% of order can be paid with credit)
- MAX_CREDIT_ETB = 500  (hard cap: max 500 ETB credit per order)
- REFERRAL_REWARD_ETB = 50  (referrer earns 50 ETB when referred user's first order confirmed)

SESSION_TYPE = 'redis' is set but Redis is NOT configured or running locally.
Flask-Session with Redis is not actually initialized in app.py — this config
key exists but has no effect because Flask-Session is never imported or init'd.

### backend/wsgi.py
Two lines. Used by gunicorn in production.
from app import create_app
app = create_app()
That's it. Gunicorn calls this file and uses the `app` object.

### backend/run.py
EMPTY FILE. Does nothing. Can be deleted.

### backend/init_db.py
One-time setup script. Run manually when you need to reset the database.
WARNING: It calls db.drop_all() first — this DELETES ALL DATA.

What it creates:
- All 9 database tables (from models)
- One super admin: username=KenoEthioShop, phone=0965806907, password=Wisdomlife1@9
- 5 sample products (one per category: Shoes, Clothing, Watches, Phones, Beauty)
  All priced at 2600 ETB selling / 2000 ETB cost, stock=50 each
  Images are placeholder.com URLs — not real product images

Run with: venv\Scripts\python.exe init_db.py (from backend/ folder)

### backend/alembic.ini
Config file for Alembic database migrations.
Flask-Migrate uses Alembic under the hood.
The migrations/versions/ folder is empty (only has .gitkeep).
No migrations have been created or run. The database was created with db.create_all()
in init_db.py, not through migrations. This means schema changes require either
running init_db.py again (loses data) or manually creating migration files.

### backend/requirements.txt
All Python dependencies. Key ones:
- Flask 3.x — web framework
- Flask-SQLAlchemy — ORM
- Flask-Migrate — DB migrations via Alembic
- Flask-CORS — allows frontend to call API from different origin
- Flask-Limiter — rate limiting
- Flask-Talisman — security headers
- psycopg2-binary — PostgreSQL driver (MUST be installed, was missing initially)
- PyJWT — JWT token creation/verification for admin auth
- bcrypt — password hashing for admin accounts
- cloudinary — image upload service
- python-dotenv — loads .env files
- gunicorn — production WSGI server


---

## BACKEND/MODELS/__INIT__.PY — THE DATABASE SCHEMA

All 9 database tables defined as SQLAlchemy models. All import db from extensions.py.

### User table (users)
Who shops on the site. No password — identified by phone number only.
- id, phone (unique, indexed), name (optional)
- credit_balance: INTEGER in cents. Default 0.
- referral_code: 8-char string like "ETH12345", auto-generated, unique
- referred_by: FK to users.id (self-referential — who invited this user)
- total_referrals: count of successful referrals (incremented when referral reward fires)
- created_at

### Product table (products)
Items for sale.
- id, name, description
- cost_price: INTEGER cents (what the shop paid — not shown to customers)
- selling_price: INTEGER cents (what customers pay — divided by 100 in API responses)
- stock: INTEGER (decremented on order, restored on rejection/refund)
- category: string (Shoes, Clothing, Watches, Phones, Beauty, etc.)
- image_url: full-size image (Cloudinary URL or placeholder)
- thumbnail_url: 300x300 thumbnail (Cloudinary URL or placeholder)
- manual_price_override: BOOLEAN — flag for manually set prices (not used in logic yet)
- created_at

### Order table (orders)
A customer's purchase.
- id, user_id (FK to users)
- subtotal: INTEGER cents (sum of items before credit)
- credit_used: INTEGER cents (how much credit was applied)
- final_total: INTEGER cents (subtotal - credit_used — what customer actually pays)
- payment_method: string (e.g. "bank_transfer", "telebirr")
- payment_proof_url: URL to screenshot of payment (uploaded to Cloudinary)
- status: string with these possible values:
    pending_verification → confirmed → (in_transit) → delivered → refunded
    OR: pending_verification → rejected
- delivery_location: JSON (address object)
- trusted_receiver_name/phone: optional — if someone else receives the order
- delivery_status: pending_assignment → assigned → (in_transit) → delivered
- delivery_person_name/phone: filled when admin assigns delivery
- delivery_confirmation_method/data: not used in current code
- created_at

### OrderItem table (order_items)
Line items within an order. One row per product per order.
- id, order_id (FK), product_id (FK)
- quantity: INTEGER
- price_at_purchase: INTEGER cents (snapshot of price at time of order — important
  because product price can change later)
- created_at

### Request table (requests)
"I want this product but it's not in the shop" — customer sends image + description.
Admin sources it, quotes a price, customer confirms, it becomes an Order.
- id, user_id (FK)
- image_url: photo of the desired item (required)
- description: text description
- budget: INTEGER cents (optional — what customer wants to pay)
- quoted_price: INTEGER cents (filled by admin after sourcing)
- status: pending_sourcing → price_quoted → converted (or rejected)
- delivery_location: JSON
- converted_order_id: FK to orders (set when request becomes an order)
- created_at

### Referral table (referrals)
Audit trail of referral rewards paid out.
- id, referrer_id (FK to users), referred_user_id (FK to users)
- order_id: FK to the order that triggered the reward
- credit_awarded: INTEGER cents (default 5000 = 50 ETB)
- created_at

### Refund table (refunds)
Customer requests money back on a confirmed/delivered order.
- id, order_id (FK, unique — one refund per order)
- reason: text (required)
- status: pending_review → approved OR rejected
- admin_notes: text (filled by admin when processing)
- approved_by: FK to admins.id
- created_at

### CreditTransaction table (credit_transactions)
Every time a user's credit_balance changes, a record is written here.
- id, user_id (FK)
- amount: INTEGER cents — POSITIVE means credit added, NEGATIVE means credit spent
- transaction_type: one of:
    referral_earned — someone they referred placed first confirmed order
    order_used — they spent credit on an order
    refund_restored — refund approved, credit returned
    cancellation_reversed — order rejected, credit they spent is returned
- related_order_id: FK to orders (optional)
- created_at

### Admin table (admins)
Staff who manage the system. NOT the same as User.
- id, username (unique), phone (unique)
- password_hash: bcrypt hash (cost factor 12)
- role: one of: super_admin, warehouse_staff, verifier, support_agent
  (only super_admin can create other admins and approve large refunds)
- created_by: FK to admins.id (who created this admin account)
- created_at


---

## BACKEND/ROUTES/ — ALL API ENDPOINTS

Authentication: Admin routes use JWT. Token is sent as "Authorization: Bearer <token>".
The require_auth decorator is copy-pasted identically into every route file (products,
orders, admin, requests, refunds). This is code duplication — it should be in a shared
utils file but currently is not.

### routes/products.py — /api/products

GET /api/products
  Public. No auth required.
  Query params: ?category=Shoes, ?search=phone
  Returns all products. Category is exact match. Search is case-insensitive LIKE on
  name and description. Returns: id, name, description, price (ETB), stock, category,
  image_url, thumbnail_url, in_stock (bool).

GET /api/products/<id>
  Public. Returns single product by ID. 404 if not found.

POST /api/products
  REQUIRES admin JWT token.
  Creates a new product. Required fields: name, cost_price, selling_price, category.
  Prices are sent as ETB floats, stored as cents (multiplied by 100).

PATCH /api/products/<id>
  REQUIRES admin JWT token.
  Updates any subset of product fields. Partial update — only fields present in
  request body are changed.

DELETE /api/products/<id>
  REQUIRES admin JWT token.
  Hard deletes the product. No soft delete. If product has order_items referencing it,
  this will fail with a FK constraint error (not handled gracefully).

### routes/orders.py — /api/orders

POST /api/orders
  Public. No auth required (customer places order by phone number).
  Required: phone, items (array of {product_id, quantity}), payment_method.
  Optional: credit_used (ETB float), delivery_location (JSON), trusted_receiver_name,
            trusted_receiver_phone, payment_proof_url.

  What it does step by step:
  1. Looks up user by phone — returns 404 if user doesn't exist yet
     (user must be created first via POST /api/users)
  2. For each item: locks the product row (SELECT FOR UPDATE) to prevent race conditions
  3. Checks stock for each item
  4. Calculates subtotal
  5. Validates subtotal >= 500 ETB (MINIMUM_ORDER_ETB)
  6. Validates credit_used <= min(50% of subtotal, 500 ETB, user's balance)
  7. Creates Order record with status='pending_verification'
  8. Creates OrderItem records
  9. Decrements stock for each product
  10. If credit used: deducts from user.credit_balance, creates CreditTransaction
  11. Commits everything atomically
  Returns: order id, subtotal, credit_used, final_total, status

GET /api/orders/<id>
  Public. Returns full order details including items array.

PATCH /api/orders/<id>/payment-proof
  Public. Updates payment_proof_url on a pending_verification order.
  Only works if order.status == 'pending_verification'.

PATCH /api/orders/<id>/assign-delivery
  REQUIRES admin JWT.
  Sets delivery_person_name, delivery_person_phone, delivery_status='assigned'.
  Only works if order.status == 'confirmed'.
  Calls NotificationService after (which only prints to console — does nothing real).

PUT /api/orders/<id>/verify
  REQUIRES admin JWT.
  The most complex endpoint. Approves or rejects an order.

  If approved=True:
  1. Checks if this user was referred by someone
  2. If yes, checks if this is their FIRST ever confirmed order
  3. If first order: adds REFERRAL_REWARD_ETB (50 ETB = 5000 cents) to referrer's
     credit_balance, increments referrer.total_referrals, creates Referral record
     and CreditTransaction record
  4. Sets order.status = 'confirmed', delivery_status = 'pending_assignment'

  If approved=False:
  1. Sets order.status = 'rejected'
  2. If credit was used: restores it to user.credit_balance, creates CreditTransaction
  3. Restores stock for all items

  Calls NotificationService after (console only).


### routes/users.py — /api/users

Phone validation: accepts +251[97]XXXXXXXX, 251[97]XXXXXXXX, or 0[97]XXXXXXXX.
Only numbers starting with 9 or 7 after the country code are valid.

GET /api/users/<phone>
  Public. Returns user by phone. 400 if invalid phone format. 404 if not found.
  Returns: id, phone, name, credit_balance (ETB), referral_code, total_referrals.

POST /api/users
  Public. Creates a new user OR returns existing user if phone already registered.
  Required: phone. Optional: name, referral_code.
  If referral_code is provided and valid: sets referred_by to that user's id.
  Auto-generates a unique referral_code like "ETH12345".
  Returns 201 for new user, 200 for existing user (with existing=True flag).

GET /api/users/<phone>/orders
  Public. Returns all orders for a user (by phone). Ordered newest first.

GET /api/users/<phone>/requests
  Public. Returns all demand requests for a user (by phone).

### routes/admin.py — /api/admin

POST /api/admin/login
  Public (no auth needed — this is how you get the token).
  Required: username, phone, password (ALL THREE must match).
  Looks up Admin by username AND phone together.
  Verifies password with bcrypt.checkpw().
  Returns JWT token valid for JWT_ACCESS_TOKEN_EXPIRES seconds (default 86400 = 24h).
  Token payload contains: admin_id, username, phone, role, exp.

GET /api/admin/orders
  REQUIRES admin JWT.
  Returns all orders. Optional ?status= filter.
  Returns: id, user_phone, subtotal, credit_used, final_total, status,
           delivery_status, payment_method, payment_proof_url, created_at, items_count.

POST /api/admin/users
  REQUIRES admin JWT with role='super_admin'.
  Creates a new admin account.
  Valid roles: super_admin, warehouse_staff, verifier, support_agent.
  Hashes password with bcrypt (cost 12).

GET /api/admin/users
  REQUIRES admin JWT.
  Returns list of all admin accounts (no passwords).

### routes/upload.py — /api/upload

POST /api/upload/image
  Public. No auth required.
  Accepts either multipart/form-data with 'file' field OR JSON with 'image' field
  (base64 or URL).
  Validates file extension (png, jpg, jpeg, webp, gif) and size (max 5MB).
  Uploads to Cloudinary. Returns url and thumbnail_url.
  Cloudinary transforms: max 1200x1200, quality auto:good, format auto.
  Thumbnail: 300x300 crop fill.
  REQUIRES Cloudinary credentials to be set — throws RuntimeError if not configured.

### routes/requests.py — /api/requests

POST /api/requests
  Public. Customer submits a "find this for me" request.
  Required: phone, image_url, description.
  Optional: budget (ETB float), delivery_location (JSON).
  User must already exist (looked up by phone).
  Creates Request with status='pending_sourcing'.

GET /api/requests
  REQUIRES admin JWT. Returns all requests with optional ?status= filter.

GET /api/requests/<id>
  Public. Returns single request details.

PATCH /api/requests/<id>/quote
  REQUIRES admin JWT.
  Admin sets quoted_price (ETB float). Sets status='price_quoted'.
  If quoted_price > 10000 ETB, requires super_admin role.

POST /api/requests/<id>/convert
  Public. Converts a price_quoted request into an Order.
  Creates Order with final_total = quoted_price, status='pending_verification'.
  Sets request.status = 'converted', request.converted_order_id = new order id.
  NOTE: The created order has no items (no OrderItem records) — it's a custom order.

### routes/refunds.py — /api/refunds

POST /api/refunds
  Public. Customer requests a refund.
  Required: order_id, reason.
  Order must have status 'confirmed' or 'delivered'.
  Only one refund per order allowed.
  Creates Refund with status='pending_review'.

GET /api/refunds
  REQUIRES admin JWT. Returns all refunds with optional ?status= filter.

PATCH /api/refunds/<id>/process
  REQUIRES admin JWT.
  Approves or rejects a refund.
  If approved and order.final_total > 500000 cents (5000 ETB): requires super_admin.
  If approved:
    - Sets refund.status = 'approved', order.status = 'refunded'
    - Adds order.final_total to user.credit_balance (refund is in CREDIT, not cash)
    - Creates CreditTransaction (type='refund_restored')
    - Restores stock for all order items
  If rejected: sets refund.status = 'rejected'.


---

## BACKEND/SERVICES/

### services/image_service.py
Wraps the Cloudinary Python SDK.
Configured at module load time using Config values (not inside a function).
This means if Cloudinary env vars are missing when the module loads, it silently
configures with empty strings — the error only appears when upload_image() is called.

upload_image(file_data, folder):
  Uploads to Cloudinary. file_data can be a file object or base64 string or URL.
  Returns dict with url, thumbnail_url, public_id.
  Raises RuntimeError if Cloudinary not configured or upload fails.

delete_image(public_id):
  Deletes from Cloudinary. Not called anywhere in the current codebase.

### services/notification_service.py
DOES NOT ACTUALLY SEND NOTIFICATIONS.
send_telegram_notification() just prints to console.
The comment says "In production, you would look up Telegram chat_id from phone number
mapping" — this mapping does not exist anywhere in the codebase.

notify_order_status_change(order): called from orders.py after verify and assign-delivery.
notify_request_quote(demand_request): defined but never called anywhere.

To make this work for real, you would need:
1. A way to link a user's phone number to their Telegram chat_id
   (user must start the bot and the bot stores the mapping)
2. The bot/ folder to be implemented
3. This service to look up the chat_id and call the Telegram Bot API

### services/__init__.py
Empty file. Just marks the folder as a Python package.

---

## BACKEND/MIGRATIONS/

### migrations/env.py
Alembic environment file. Auto-generated by Flask-Migrate.
Connects Alembic to the Flask app's database.

### migrations/script.py.mako
Template for generating new migration files. Auto-generated.

### migrations/versions/
EMPTY (only .gitkeep). No migrations have ever been created.
The database schema was created directly with db.create_all() in init_db.py.

---

## FRONTEND FOLDER — THE CUSTOMER SHOP

All files are plain HTML. They open directly in a browser.
They call the backend at http://localhost:5000 when running locally.
The API base URL is set in frontend/config.js.

### frontend/config.js
Defines API_BASE_URL and API_ENDPOINTS.
Auto-detects localhost vs production:
  localhost → http://localhost:5000
  anything else → https://your-backend.onrender.com (PLACEHOLDER — not a real URL)
Also defines SOCIAL_LINKS (TikTok, Facebook, YouTube, Telegram channel/group/bot).

### frontend/index.html
Landing page. Shows shop branding, social media links, call-to-action buttons.
Links to shop.html and request.html.

### frontend/shop.html
Product listing page. Uses product.js to load and display products.
Has category filter dropdown and search input.
Each product card has "Add to Cart" button.

### frontend/product.html
Single product detail page. Loaded with ?id=<product_id> in URL.
Shows full image, description, price, stock status.
Add to Cart button.

### frontend/cart.html
Shopping cart page. Reads cart from localStorage.
Shows items, quantities (editable), subtotal.
"Proceed to Checkout" button → checkout.html.

### frontend/checkout.html
Order placement page. Uses checkout.js.
Customer enters phone number → system looks up or creates user.
If user has credit, shows option to apply it.
Selects payment method, enters delivery address.
Submits order to POST /api/orders.
On success → redirects to order-success.html?id=<order_id>.

### frontend/order-success.html
Shown after order is placed. Displays order ID.
Has a file upload section for payment proof screenshot.
Calls PATCH /api/orders/<id>/payment-proof with the uploaded image URL.
The image upload itself calls POST /api/upload/image first.

### frontend/dashboard.html
Customer's personal page. Accessed by entering phone number.
Shows: credit balance, total referrals, referral code (with copy button), order history.
Each order shows status and a "Request Refund" button (for confirmed/delivered orders).
Refund button calls POST /api/refunds with a reason prompt.
Phone is stored in sessionStorage — persists for the browser session only.

### frontend/request.html
"Request a product" page. Customer uploads image and describes what they want.
Calls POST /api/upload/image then POST /api/requests.
IMPORTANT: frontend/assets/js/request.js is EMPTY.
The request.html page likely has its own inline script or is broken.

### frontend/status.html
EMPTY FILE. Does not exist / has no content.
Order tracking by phone was intended here but was never built.
Currently, order tracking is only available in dashboard.html.


---

## FRONTEND/ASSETS/JS/ — JAVASCRIPT FILES

### assets/js/api.js
Defines apiCall() wrapper around fetch() with JSON headers.
Defines four API client objects:
- ProductAPI: getAll(category), getById(id), create(data)
- UserAPI: getByPhone(phone), create(data), getOrders(phone)
- OrderAPI: create(data), getById(id)
- AdminAPI: login(username, password) — NOTE: this only sends username+password,
  NOT phone. The backend requires username+phone+password. This AdminAPI.login()
  in the frontend api.js is WRONG and will fail. The admin panel uses its own
  inline fetch() calls that correctly send all three fields.

### assets/js/app-state.js
Global state manager class AppState. Singleton stored as window.appState.
Manages: user session, cart, loading state, error state.
Persists user to sessionStorage, cart to localStorage (key: 'ethioshop_cart').
Has subscribe/notify pattern for reactive updates.
Has showToast() for notifications (success/error/warning/info).
Has refreshUser() to re-fetch user data from API.

NOTE: cart.js also manages cart separately using localStorage key 'cart'.
There are TWO cart implementations: ShoppingCart class in cart.js and AppState
in app-state.js. They use DIFFERENT localStorage keys ('cart' vs 'ethioshop_cart').
This is a bug — they can get out of sync. checkout.js uses the cart.js version.

### assets/js/cart.js
ShoppingCart class. Stores cart in localStorage key 'cart'.
Methods: addItem, removeItem, updateQuantity, getSubtotal, getItemCount, clear.
Updates cart badge in navbar.
Shows green toast notification when item added.
Global instance: const cart = new ShoppingCart()

### assets/js/checkout.js
Handles the checkout form submission.
Reads cart from cart.js (not app-state.js).
Creates user if not exists, then creates order.
Handles credit toggle (checkbox to apply available credit).
Credit calculation: min(subtotal * 0.5, 500, user.credit_balance).
On success: clears cart, redirects to order-success.html?id=<id>.

### assets/js/product.js
Loads and renders product grid on shop.html.
Calls ProductAPI.getAll() with optional category filter.
Client-side search: filters allProducts array by name/description (no API call).
Category filter updates URL query param.
Hardcoded category list: Shoes, Clothing, Watches, Phones, Beauty, Bags,
Electronics, Home Essentials, Perfumes, Sports, Earphones, Blankets, Jewelry, Thermoses.
NOTE: The DB only has 5 categories from init_db.py. The other 9 categories in this
list will show empty results until products are added to those categories.

### assets/js/app.js
EMPTY FILE. No content. Does nothing.

### assets/js/request.js
EMPTY FILE. No content. Does nothing.

### assets/js/router.js
Router class. Singleton stored as window.router.
navigate(path, params): redirects to a page with query params.
getParam(name): reads URL query params.
isProtectedRoute(): checks if current page is /dashboard or /checkout.
requireAuth(): redirects if not authenticated (checks appState.state.isAuthenticated).
NOTE: This router is defined but it's unclear which pages actually use it.
Most pages do their own navigation with window.location.href directly.

### assets/js/ui-utils.js
UI helper object stored as window.UI.
showLoading/hideLoading: shows/hides a spinner element.
showError/hideError: shows/hides an error message element.
showEmptyState: renders an empty state with icon and message.
updateCartBadge: syncs cart count badge in navbar.
formatCurrency: formats number as "X.XX ETB".
formatDate: formats ISO date string to readable format.
disableButton/enableButton: manages button loading state.
createSkeleton: generates skeleton loader HTML.
showModal: creates a modal overlay dynamically.

---

## ADMIN-PANEL FOLDER — THE MANAGEMENT INTERFACE

All files are plain HTML. Open directly in browser.
Token stored in localStorage key 'adminToken'.
Admin user info stored in localStorage key 'adminUser'.

### admin-panel/config.js
Defines ADMIN_API_BASE_URL.
Auto-detects localhost vs production (same pattern as frontend/config.js).
Also defines adminApi(path) helper function.

### admin-panel/admin-api.js
Defines AdminAPI object with methods:
- getOrders(status): GET /api/admin/orders with auth header
- getOrderDetails(orderId): GET /api/orders/<id> with auth header
- verifyOrder(orderId, approved): PUT /api/orders/<id>/verify
- createProduct(data): POST /api/products
- updateProduct(id, data): PATCH /api/products/<id>
- deleteProduct(id): DELETE /api/products/<id>
getAuthToken(): reads from localStorage, redirects to index.html if missing.
On 401 response: clears token and redirects to login.

### admin-panel/index.html (Admin Login)
Login form with username, phone, password fields.
Calls POST /api/admin/login with all three fields.
On success: stores token and admin object in localStorage, redirects to orders.html.
If already logged in (token exists): auto-redirects to orders.html.

### admin-panel/orders.html (Orders Management)
Main admin page. Shows all orders in a table.
Filter by status dropdown (all / pending_verification / confirmed / rejected).
Each row has: View, Approve, Reject buttons (Approve/Reject only for pending).
"Assign Delivery" button appears for confirmed orders with pending_assignment status.
View opens a modal with full order details including items table and payment proof link.
Approve/Reject calls AdminAPI.verifyOrder().
Assign Delivery uses prompt() dialogs to get delivery person name and phone,
then calls PATCH /api/orders/<id>/assign-delivery directly.

NOTE: The orders.html file has a structural bug — the JavaScript code that defines
the loadOrders() function appears to start mid-file without a proper <script> tag
opening. The file shows "orders = data.orders;" as the first line of a script block.
This means the loadOrders function definition is missing its opening. The page may
not work correctly as-is.

### admin-panel/products.html (Products Management)
Shows all products in a table.
"Add Product" button opens a modal form.
Edit button pre-fills the form (cost_price is estimated as selling_price * 0.7 —
the actual cost_price is not returned by the public GET /api/products endpoint).
Save calls createProduct or updateProduct via AdminAPI.
Delete calls deleteProduct via AdminAPI.
Category dropdown has: Electronics, Fashion, Home, Beauty, Sports, Books.
NOTE: These categories don't match the ones in product.js (Shoes, Clothing, etc.).
This inconsistency means products created in admin panel may not show in the
correct category filter on the customer shop.

### admin-panel/admins.html (Admin Management)
Lists all admin accounts.
"Create Admin" button opens a modal form.
Calls POST /api/admin/users (requires super_admin JWT).
Role options: super_admin, warehouse_staff, verifier, support_agent.
No delete or edit functionality for admins.

### admin-panel/admin-style.css
Styles for the admin panel. Sidebar layout, tables, modals, status badges.


---

## BOT FOLDER — TELEGRAM BOT (NOT IMPLEMENTED)

### bot/bot.py
Exists but the handlers/ and services/ folders inside bot/ are EMPTY.
The bot is not functional. It has a config and requirements file but no actual code.

### bot/config.py
Reads bot-specific env vars (TELEGRAM_BOT_TOKEN, API_BASE_URL, etc.)

### bot/requirements.txt
Lists python-telegram-bot library. Not installed anywhere.

### bot/.env
Bot-specific env file. Has TELEGRAM_BOT_TOKEN and API_BASE_URL.

---

## KNOWN BUGS AND INCOMPLETE FEATURES

1. DUPLICATE /api/products ROUTE
   app.py defines GET /api/products inline AND routes/products.py defines it as a
   Blueprint. Flask uses the Blueprint version. The inline one in app.py returns
   a different format (no success wrapper, wrong price format). Should be removed.

2. TWO CART IMPLEMENTATIONS OUT OF SYNC
   cart.js uses localStorage key 'cart'. app-state.js uses 'ethioshop_cart'.
   checkout.js uses cart.js. If any page uses appState.addToCart(), those items
   won't appear at checkout.

3. status.html IS EMPTY
   Order tracking page doesn't exist. Users must go to dashboard.html.

4. request.js IS EMPTY
   The request.html page has no JS logic from this file. May have inline script
   or may be broken.

5. app.js IS EMPTY
   Any page that relies on app.js for initialization will silently do nothing.

6. ADMIN PANEL orders.html HAS BROKEN SCRIPT TAG
   The loadOrders function appears to be missing its opening. Needs inspection.

7. TELEGRAM NOTIFICATIONS DO NOTHING
   NotificationService only prints to console. No real messages sent.

8. BOT IS NOT IMPLEMENTED
   bot/ folder is empty. No Telegram bot functionality exists.

9. CATEGORY MISMATCH
   product.js has 14 categories. admin-panel/products.html has 6 different ones.
   They don't match. Products created in admin may not filter correctly in shop.

10. REFUNDS ARE CREDIT-ONLY
    When a refund is approved, the customer gets credit added to their account,
    NOT a cash refund. This is by design but may surprise customers.

11. NO PASSWORD RESET FOR ADMINS
    No endpoint exists to reset an admin password. Must use init_db.py (wipes all data)
    or manually update the DB.

12. NO PAGINATION
    GET /api/products, GET /api/admin/orders, etc. return ALL records with no limit.
    Will become slow with large datasets.

13. MIGRATIONS NEVER USED
    Schema changes require either running init_db.py (loses all data) or manually
    writing Alembic migration files and running flask db upgrade.

14. EDIT PRODUCT SHOWS WRONG COST PRICE
    products.html estimates cost_price as selling_price * 0.7 because the public
    products API doesn't return cost_price. Editing a product will overwrite the
    real cost_price with this estimate.

15. AdminAPI.login() IN frontend/assets/js/api.js IS WRONG
    It only sends username+password, not phone. The backend requires all three.
    This function is not used by the admin panel (which has its own inline fetch).
    But if any frontend page tries to use AdminAPI.login(), it will fail.

---

## EXTERNAL SERVICES USED

### Supabase (PostgreSQL database)
Project ref: hoysrktwmrowdpihhxjj
Region: eu-central-1 (Frankfurt, AWS)
Direct host: db.hoysrktwmrowdpihhxjj.supabase.co (IPv6 only — won't work on this machine)
Working pooler: aws-1-eu-central-1.pooler.supabase.com:6543
User: postgres.hoysrktwmrowdpihhxjj
Password: 9Wisdomlife1@ (the @ is URL-encoded to %40 by quote_plus in config.py)

### Cloudinary (image storage)
Cloud name: dcu5tuayd
Used for: product images, payment proof screenshots, request item photos
Credentials in backend/.env: CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
Free tier has 25GB storage and 25GB bandwidth/month.

### Telegram Bot
Token: 8745018086:AAF-0g3rC1jfSOzmh79aIRXhG1_PcSBkCq4
Bot username: @EthioShopTrusted_bot
Admin chat ID: 1885291815
Currently: NOT functional. Token is configured but bot code doesn't exist.

---

## HOW TO START THE SYSTEM

1. Start backend (from backend/ folder):
   venv\Scripts\python.exe app.py

2. Open frontend pages directly in browser:
   frontend/index.html — home
   frontend/shop.html — browse products
   frontend/dashboard.html — customer account

3. Open admin panel directly in browser:
   admin-panel/index.html — admin login
   Credentials: KenoEthioShop / 0965806907 / Wisdomlife1@9

4. If database needs reset (WARNING: deletes all data):
   venv\Scripts\python.exe init_db.py (from backend/ folder)

---

## WHAT NEEDS TO BE BUILT NEXT (HONEST GAPS)

- Telegram bot (bot/ folder is empty)
- Real Telegram notifications (notification_service.py is fake)
- status.html (order tracking page — currently empty)
- request.js (request page JS — currently empty)
- Pagination on all list endpoints
- Admin dashboard with stats (revenue, order counts, etc.)
- Delivery status updates (in_transit, delivered) — columns exist but no endpoints
- Password reset for admins
- Proper Alembic migrations instead of drop-all init_db.py
- Fix category mismatch between admin panel and customer shop
- Fix duplicate /api/products route in app.py
- Fix AdminAPI.login() in frontend/assets/js/api.js to include phone field
- Fix orders.html broken script tag in admin panel
