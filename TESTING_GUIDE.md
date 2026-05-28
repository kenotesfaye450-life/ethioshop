# EthioShop — Complete Testing Guide

**Date:** May 28, 2026  
**Status:** All improvements implemented and ready for testing

---

## 🚀 QUICK START — How to Run the System

### 1. Start the Backend Server

```cmd
cd c:\Users\kenot\Desktop\ethioshop\backend
venv\Scripts\python.exe app.py
```

**Expected output:**
```
 * Running on http://127.0.0.1:5000
 * Running on http://[your-ip]:5000
```

**Keep this terminal open.** The backend must be running for everything else to work.

---

### 2. Open the Customer Frontend

Open in your browser:
```
file:///c:/Users/kenot/Desktop/ethioshop/frontend/index.html
```

Or use a local web server (recommended):
```cmd
cd c:\Users\kenot\Desktop\ethioshop\frontend
python -m http.server 8080
```
Then open: `http://localhost:8080`

---

### 3. Open the Admin Panel

Open in your browser:
```
file:///c:/Users/kenot/Desktop/ethioshop/admin-panel/index.html
```

Or use a local web server:
```cmd
cd c:\Users\kenot\Desktop\ethioshop\admin-panel
python -m http.server 8081
```
Then open: `http://localhost:8081`

**Admin Login Credentials:**
- **Username:** KenoEthioShop
- **Phone:** 0965806907
- **Password:** Wisdomlife1@9

⚠️ **IMPORTANT:** All three fields are required. The admin login requires username + phone + password.

---

## 📱 CUSTOMER SIDE TESTING

### Test 1: Browse Products

1. Open `frontend/shop.html`
2. You should see 5 sample products (Shoes, Clothing, Watches, Phones, Beauty)
3. **Test category filter:** Select "Shoes" from dropdown → only shoes should show
4. **Test search:** Type "phone" in search box → only phone products should show
5. **Test product details:** Click on any product → should open `product.html` with full details

**What to verify:**
- ✅ Products load and display correctly
- ✅ Category filter works
- ✅ Search works (case-insensitive)
- ✅ Product images show (placeholder.com images)
- ✅ Prices display in ETB (e.g., "2,600.00 ETB")
- ✅ Stock status shows ("In Stock" or "Out of Stock")

---

### Test 2: Add to Cart

1. On `shop.html`, click "Add to Cart" on any product
2. **Expected:** Green toast notification "Added to cart!"
3. **Expected:** Cart badge in navbar updates (shows "1")
4. Add 2 more different products
5. **Expected:** Cart badge shows "3"

**What to verify:**
- ✅ Cart badge updates correctly
- ✅ Toast notifications appear
- ✅ Cart persists after page refresh (stored in localStorage)

---

### Test 3: View and Edit Cart

1. Click the cart icon in navbar → opens `cart.html`
2. You should see all 3 products you added
3. **Test quantity change:** Change quantity of first item to 2
4. **Expected:** Subtotal updates automatically
5. **Test remove item:** Click "Remove" on second item
6. **Expected:** Item disappears, subtotal updates, cart badge updates

**What to verify:**
- ✅ All cart items display correctly
- ✅ Quantity changes update subtotal
- ✅ Remove button works
- ✅ Subtotal calculation is correct (sum of price × quantity)
- ✅ "Proceed to Checkout" button is visible

---

### Test 4: Place an Order (New Customer)

1. From cart, click "Proceed to Checkout" → opens `checkout.html`
2. **Enter phone number:** 0912345678 (a new number, not in database)
3. Click "Continue"
4. **Expected:** Form expands showing "New Customer" message
5. **Enter name:** Test Customer
6. **Referral code (optional):** Leave blank for now
7. **Select payment method:** Bank Transfer
8. **Enter delivery address:**
   - Region: Addis Ababa
   - City: Bole
   - Subcity: Bole Subcity
   - Woreda: 03
   - House Number: 123
   - Landmark: Near Edna Mall
9. **Credit toggle:** Should be OFF (new customer has 0 credit)
10. Click "Place Order"
11. **Expected:** Redirects to `order-success.html` with order ID

**What to verify:**
- ✅ Phone validation works (rejects invalid formats)
- ✅ New customer is created automatically
- ✅ Order is created with status "pending_verification"
- ✅ Cart is cleared after order placement
- ✅ Order ID is displayed on success page

---

### Test 5: Upload Payment Proof

1. On `order-success.html`, you should see a file upload section
2. **Upload an image:** Select any image file (PNG, JPG, etc.)
3. Click "Upload Payment Proof"
4. **Expected:** Success message "Payment proof uploaded successfully"
5. **Expected:** Image preview appears

**What to verify:**
- ✅ File upload works
- ✅ Image is uploaded to Cloudinary (check backend logs for URL)
- ✅ Order's payment_proof_url is updated
- ✅ Only image files are accepted (test with .txt file → should reject)

---

### Test 6: View Order History (Customer Dashboard)

1. Open `frontend/dashboard.html`
2. **Enter phone number:** 0912345678 (the customer you just created)
3. Click "View Dashboard"
4. **Expected:** Dashboard loads showing:
   - Credit balance: 0.00 ETB
   - Total referrals: 0
   - Referral code: ETH##### (8 characters)
   - Order history: 1 order with status "Pending Verification"

**What to verify:**
- ✅ Dashboard loads for existing customer
- ✅ Credit balance is correct
- ✅ Referral code is displayed and copyable
- ✅ Order history shows all orders
- ✅ Order status is displayed correctly

---

### Test 7: Place Order with Referral Code

1. Open `checkout.html` again (add items to cart first)
2. **Enter phone number:** 0923456789 (a different new number)
3. **Enter name:** Referred Customer
4. **Referral code:** Copy the referral code from the first customer's dashboard (ETH#####)
5. Complete the order
6. **Expected:** Order is created successfully

**Now verify referral reward:**
1. Go to admin panel → Orders
2. Find the new order and click "Verify" → Approve it
3. Go back to customer dashboard for the FIRST customer (0912345678)
4. **Expected:** Credit balance is now 50.00 ETB
5. **Expected:** Total referrals is now 1

**What to verify:**
- ✅ Referral code is accepted during registration
- ✅ Referral reward (50 ETB) is credited when referred user's first order is confirmed
- ✅ Referrer's total_referrals count increments
- ✅ Credit transaction is recorded

---

### Test 8: Use Credit on Order

1. Add items to cart (total should be at least 200 ETB)
2. Go to checkout
3. **Enter phone number:** 0912345678 (the customer with 50 ETB credit)
4. **Expected:** Credit toggle appears showing "You have 50.00 ETB credit"
5. **Toggle credit ON**
6. **Expected:** Final total decreases by 50 ETB
7. Complete the order
8. **Expected:** Order is created with credit_used = 50 ETB

**Now verify credit was deducted:**
1. Go to dashboard for this customer
2. **Expected:** Credit balance is now 0.00 ETB

**What to verify:**
- ✅ Credit toggle appears only when customer has credit
- ✅ Credit calculation respects limits (max 50% of subtotal, max 500 ETB)
- ✅ Final total is reduced by credit amount
- ✅ Credit is deducted from customer's balance
- ✅ Credit transaction is recorded

---

### Test 9: Request a Product (Demand Request)

1. Open `frontend/request.html`
2. **Enter phone number:** 0912345678
3. **Upload image:** Select an image of a product you want
4. **Description:** "I want this Nike Air Max shoes in size 42"
5. **Budget (optional):** 3000
6. **Delivery location:** Same as before
7. Click "Submit Request"
8. **Expected:** Success message "Request submitted successfully"

**What to verify:**
- ✅ Request is created with status "pending_sourcing"
- ✅ Image is uploaded to Cloudinary
- ✅ Request appears in admin panel → Requests

---

### Test 10: Track Order Status

1. Open `frontend/status.html`
2. **Enter phone number:** 0912345678
3. **Expected:** All orders for this customer are displayed with:
   - Order ID
   - Total amount
   - Status (Pending Verification, Confirmed, etc.)
   - Delivery status
   - Payment proof link (if uploaded)
   - Delivery timeline visualization

**What to verify:**
- ✅ Order tracking page loads
- ✅ All orders are displayed
- ✅ Status information is accurate
- ✅ Delivery timeline shows correct progress

---

## 🔐 ADMIN SIDE TESTING

### Test 11: Admin Login

1. Open `admin-panel/index.html`
2. **Enter credentials:**
   - Username: KenoEthioShop
   - Phone: 0965806907
   - Password: Wisdomlife1@9
3. Click "Login"
4. **Expected:** Redirects to `dashboard.html`

**Test wrong credentials:**
- Wrong username → "Invalid credentials"
- Wrong phone → "Invalid credentials"
- Wrong password → "Invalid credentials"
- Missing any field → "All fields are required"

**What to verify:**
- ✅ Login works with correct credentials
- ✅ Login fails with wrong credentials
- ✅ All three fields are required
- ✅ JWT token is stored in localStorage
- ✅ Redirect to dashboard after successful login

---

### Test 12: Admin Dashboard Metrics

1. After login, you should see the dashboard with metrics:
   - **Total Sales:** Sum of all confirmed orders
   - **Pending Orders:** Count of pending_verification orders
   - **Daily Orders:** Orders in last 24 hours
   - **Top Products:** Products with most sales (by quantity)
   - **Referral Stats:** Total referrals and credit awarded
   - **Recent Orders:** Last 10 orders

**What to verify:**
- ✅ All metrics display correctly
- ✅ Numbers match actual data
- ✅ Top products table shows product names and quantities
- ✅ Recent orders table shows order details

---

### Test 13: Verify Orders

1. Click "Orders" in sidebar → opens `orders.html`
2. You should see all orders with status "Pending Verification"
3. **Click "View" on any order**
4. **Expected:** Modal opens showing full order details:
   - Customer phone and name
   - Items list with quantities and prices
   - Subtotal, credit used, final total
   - Payment method and proof image
   - Delivery address
5. **Click "Verify Order"**
6. **Expected:** Confirmation dialog appears
7. **Click "Approve"**
8. **Expected:** Order status changes to "Confirmed"
9. **Expected:** Delivery status changes to "Pending Assignment"

**Test rejection:**
1. Find another pending order
2. Click "Verify" → "Reject"
3. **Expected:** Order status changes to "Rejected"
4. **Expected:** Stock is restored for all items
5. **Expected:** If credit was used, it's returned to customer

**What to verify:**
- ✅ Orders list loads correctly
- ✅ Order details modal shows all information
- ✅ Payment proof image is displayed
- ✅ Approve button works
- ✅ Reject button works
- ✅ Stock is restored on rejection
- ✅ Credit is restored on rejection
- ✅ Referral reward is triggered on first order approval

---

### Test 14: Assign Delivery

1. On `orders.html`, find a "Confirmed" order
2. **Expected:** "Assign Delivery" button appears
3. Click "Assign Delivery"
4. **Expected:** Form appears with fields:
   - Delivery Person Name
   - Delivery Person Phone
5. **Enter:** Name: "John Doe", Phone: "0911111111"
6. Click "Assign"
7. **Expected:** Delivery status changes to "Assigned"
8. **Expected:** Delivery person info is saved

**What to verify:**
- ✅ Assign button only appears for confirmed orders
- ✅ Form validation works (required fields)
- ✅ Delivery status updates correctly
- ✅ Delivery person info is saved

---

### Test 15: Update Delivery Status

1. Find an order with delivery_status = "Assigned"
2. **Expected:** "In Transit" button appears
3. Click "In Transit"
4. **Expected:** Delivery status changes to "In Transit"
5. **Expected:** "Delivered" button now appears
6. Click "Delivered"
7. **Expected:** Delivery status changes to "Delivered"
8. **Expected:** Order status also changes to "Delivered"

**What to verify:**
- ✅ Status transition buttons appear based on current status
- ✅ In Transit button works
- ✅ Delivered button works
- ✅ Order status updates when delivered
- ✅ Telegram notification is sent (check backend logs)

---

### Test 16: Manage Products

1. Click "Products" in sidebar → opens `products.html`
2. You should see all 5 sample products

**Test: Create New Product**
1. Click "Add New Product"
2. **Enter details:**
   - Name: "Samsung Galaxy S24"
   - Description: "Latest flagship phone"
   - Cost Price: 45000
   - Selling Price: 55000
   - Stock: 20
   - Category: Phones (select from dropdown)
   - Image URL: https://via.placeholder.com/800x800/4A90E2/FFFFFF?text=Samsung+S24
3. Click "Save"
4. **Expected:** Product is created and appears in list

**Test: Edit Product**
1. Click "Edit" on any product
2. Change the price to 3000
3. Click "Save"
4. **Expected:** Product is updated

**Test: Delete Product**
1. Click "Delete" on any product
2. **Expected:** Confirmation dialog appears
3. Click "Confirm"
4. **Expected:** Product is deleted

**What to verify:**
- ✅ Products list loads correctly
- ✅ Create product works
- ✅ Category dropdown shows all 14 categories
- ✅ Edit product works
- ✅ Delete product works
- ✅ Image URLs are validated
- ✅ Prices are stored correctly (ETB → cents conversion)

---

### Test 17: Process Demand Requests

1. Click "Requests" in sidebar → opens requests page
2. You should see the request created in Test 9
3. **Click "View" on the request**
4. **Expected:** Modal shows request details with image
5. **Click "Quote Price"**
6. **Enter quoted price:** 3500
7. Click "Submit Quote"
8. **Expected:** Request status changes to "Price Quoted"

**Now convert to order (customer side):**
1. Go to customer dashboard (0912345678)
2. Click "Requests" tab
3. You should see the request with quoted price 3500 ETB
4. Click "Accept Quote"
5. **Expected:** Order is created from the request
6. **Expected:** Request status changes to "Converted"

**What to verify:**
- ✅ Requests list loads correctly
- ✅ Request details modal shows image and description
- ✅ Quote price form works
- ✅ Status updates to "Price Quoted"
- ✅ Customer can accept quote
- ✅ Order is created from request
- ✅ Request status updates to "Converted"

---

### Test 18: Process Refunds

1. Click "Refunds" in sidebar
2. You should see any refund requests submitted by customers

**Create a refund request (customer side first):**
1. Go to customer dashboard (0912345678)
2. Find a "Confirmed" or "Delivered" order
3. Click "Request Refund"
4. **Enter reason:** "Product is defective"
5. Click "Submit"
6. **Expected:** Refund request is created

**Now process it (admin side):**
1. Go to admin panel → Refunds
2. Click "View" on the refund
3. **Expected:** Modal shows refund details and order info
4. **Click "Approve"**
5. **Enter admin notes:** "Approved - product defect confirmed"
6. Click "Confirm"
7. **Expected:** Refund status changes to "Approved"
8. **Expected:** Order status changes to "Refunded"
9. **Expected:** Customer's credit balance increases by order total
10. **Expected:** Stock is restored for all items

**Test rejection:**
1. Create another refund request
2. Click "Reject" instead
3. **Expected:** Refund status changes to "Rejected"
4. **Expected:** Order status remains unchanged
5. **Expected:** No credit is added

**What to verify:**
- ✅ Refunds list loads correctly
- ✅ Refund details modal shows all information
- ✅ Approve button works
- ✅ Reject button works
- ✅ Credit is added to customer on approval
- ✅ Stock is restored on approval
- ✅ Order status updates correctly
- ✅ Admin notes are saved

---

### Test 19: Manage Admin Users (Super Admin Only)

1. Click "Admins" in sidebar → opens `admins.html`
2. You should see the current admin (KenoEthioShop)

**Test: Create New Admin**
1. Click "Add New Admin"
2. **Enter details:**
   - Username: TestAdmin
   - Phone: 0922222222
   - Password: TestPass123
   - Role: Warehouse Staff (select from dropdown)
3. Click "Create"
4. **Expected:** New admin is created and appears in list

**Test: Login as New Admin**
1. Logout (click "Logout" in navbar)
2. Login with new credentials:
   - Username: TestAdmin
   - Phone: 0922222222
   - Password: TestPass123
3. **Expected:** Login succeeds
4. **Expected:** Dashboard shows (but with limited permissions)

**Test: Role Permissions**
1. As "Warehouse Staff", try to access "Admins" page
2. **Expected:** Should work (all roles can view admins)
3. Try to create a new admin
4. **Expected:** Should fail with "Permission denied" (only super_admin can create admins)

**What to verify:**
- ✅ Admins list loads correctly
- ✅ Create admin works (super_admin only)
- ✅ New admin can login
- ✅ Role-based permissions work
- ✅ Password is hashed (not stored in plain text)

---

## 🔍 ADVANCED TESTING

### Test 20: Stock Management

1. Create a product with stock = 2
2. Place an order for 1 unit → stock should be 1
3. Place another order for 1 unit → stock should be 0
4. Try to place another order for 1 unit → should fail with "Insufficient stock"
5. Reject one of the orders → stock should be restored to 1

**What to verify:**
- ✅ Stock decrements on order creation
- ✅ Stock is restored on order rejection
- ✅ Stock is restored on refund approval
- ✅ Orders fail when stock is insufficient
- ✅ Race conditions are prevented (SELECT FOR UPDATE)

---

### Test 21: Credit Limits

**Test: 50% limit**
1. Customer has 1000 ETB credit
2. Place order with subtotal = 1000 ETB
3. Apply credit
4. **Expected:** Only 500 ETB credit is applied (50% limit)

**Test: 500 ETB hard cap**
1. Customer has 1000 ETB credit
2. Place order with subtotal = 2000 ETB
3. Apply credit
4. **Expected:** Only 500 ETB credit is applied (hard cap)

**Test: Balance limit**
1. Customer has 100 ETB credit
2. Place order with subtotal = 1000 ETB
3. Apply credit
4. **Expected:** Only 100 ETB credit is applied (balance limit)

**What to verify:**
- ✅ Credit cannot exceed 50% of subtotal
- ✅ Credit cannot exceed 500 ETB
- ✅ Credit cannot exceed customer's balance
- ✅ Minimum of all three limits is applied

---

### Test 22: Minimum Order Value

1. Add items to cart with total < 500 ETB
2. Try to place order
3. **Expected:** Error message "Minimum order value is 500 ETB"

**What to verify:**
- ✅ Orders below 500 ETB are rejected
- ✅ Error message is clear

---

### Test 23: Phone Number Validation

**Valid formats:**
- 0912345678 ✅
- 0712345678 ✅
- +251912345678 ✅
- 251912345678 ✅

**Invalid formats:**
- 0812345678 ❌ (must start with 9 or 7)
- 091234567 ❌ (too short)
- 09123456789 ❌ (too long)
- abc123 ❌ (not a number)

**What to verify:**
- ✅ Valid formats are accepted
- ✅ Invalid formats are rejected with clear error message

---

### Test 24: Image Upload Security

**Test: File type validation**
1. Try to upload a .txt file as payment proof
2. **Expected:** Error "Invalid file type"

**Test: File size validation**
1. Try to upload an image > 5MB
2. **Expected:** Error "File too large"

**What to verify:**
- ✅ Only image files are accepted (png, jpg, jpeg, webp, gif)
- ✅ Files > 5MB are rejected
- ✅ MIME type validation works (if python-magic is installed)

---

### Test 25: Pagination

**Test: Products pagination**
1. Create 25 products (more than default page size)
2. Go to `shop.html`
3. **Expected:** Only 20 products show (default limit)
4. **Expected:** Pagination controls appear
5. Click "Next" → next 5 products show

**Test: Orders pagination**
1. Create 25 orders
2. Go to admin panel → Orders
3. **Expected:** Only 20 orders show
4. **Expected:** Pagination controls appear

**What to verify:**
- ✅ All list endpoints support pagination
- ✅ Default limit is 20
- ✅ Max limit is 100
- ✅ Response includes: items, page, pages, total

---

## 🐛 KNOWN ISSUES TO TEST

### Issue 1: Duplicate Cart Implementations
- `cart.js` uses localStorage key `'cart'`
- `app-state.js` uses localStorage key `'ethioshop_cart'`
- **Test:** Add items using shop.html, check if they appear in checkout.html
- **Expected:** Should work (checkout uses cart.js)
- **Issue:** If you use app-state.js elsewhere, carts will be out of sync

### Issue 2: Telegram Notifications Don't Work
- Backend logs "Sending Telegram notification" but doesn't actually send
- **Test:** Verify an order, check if customer receives Telegram message
- **Expected:** No message is sent (only console log)
- **Fix needed:** Implement bot/ folder and link users to chat_ids

### Issue 3: Empty Files
- `frontend/assets/js/app.js` is empty
- `frontend/assets/js/request.js` is empty
- **Test:** Check if request.html works
- **Expected:** May have inline script or be broken

### Issue 4: Admin API in frontend/api.js is Wrong
- `AdminAPI.login()` only sends username + password
- Backend requires username + phone + password
- **Test:** Try using AdminAPI.login() from console
- **Expected:** Will fail
- **Note:** Admin panel uses its own fetch() calls (correct)

---

## 📊 VERIFICATION CHECKLIST

After completing all tests, verify:

### Database Integrity
- [ ] All tables exist (users, products, orders, order_items, requests, refunds, referrals, credit_transactions, admins)
- [ ] Foreign keys are enforced
- [ ] Indexes exist on frequently queried columns
- [ ] No orphaned records

### Business Logic
- [ ] Referral rewards work correctly
- [ ] Credit limits are enforced
- [ ] Stock management is accurate
- [ ] Minimum order value is enforced
- [ ] Phone validation works
- [ ] Price conversions (ETB ↔ cents) are correct

### Security
- [ ] Admin routes require JWT token
- [ ] Passwords are hashed (bcrypt)
- [ ] File uploads are validated
- [ ] SQL injection is prevented (using ORM)
- [ ] CORS is configured correctly
- [ ] Rate limiting is active

### User Experience
- [ ] All pages load without errors
- [ ] Forms validate input
- [ ] Error messages are clear
- [ ] Success messages appear
- [ ] Loading states work
- [ ] Mobile responsive (test on phone)

---

## 🔗 IMPORTANT URLS

### Customer Frontend
- Home: `file:///c:/Users/kenot/Desktop/ethioshop/frontend/index.html`
- Shop: `file:///c:/Users/kenot/Desktop/ethioshop/frontend/shop.html`
- Cart: `file:///c:/Users/kenot/Desktop/ethioshop/frontend/cart.html`
- Checkout: `file:///c:/Users/kenot/Desktop/ethioshop/frontend/checkout.html`
- Dashboard: `file:///c:/Users/kenot/Desktop/ethioshop/frontend/dashboard.html`
- Request: `file:///c:/Users/kenot/Desktop/ethioshop/frontend/request.html`
- Status: `file:///c:/Users/kenot/Desktop/ethioshop/frontend/status.html`

### Admin Panel
- Login: `file:///c:/Users/kenot/Desktop/ethioshop/admin-panel/index.html`
- Dashboard: `file:///c:/Users/kenot/Desktop/ethioshop/admin-panel/dashboard.html`
- Orders: `file:///c:/Users/kenot/Desktop/ethioshop/admin-panel/orders.html`
- Products: `file:///c:/Users/kenot/Desktop/ethioshop/admin-panel/products.html`
- Admins: `file:///c:/Users/kenot/Desktop/ethioshop/admin-panel/admins.html`

### API Endpoints
- Health: `http://localhost:5000/health`
- Products: `http://localhost:5000/api/products`
- Orders: `http://localhost:5000/api/orders`
- Users: `http://localhost:5000/api/users`
- Admin: `http://localhost:5000/api/admin`

---

## 🆘 TROUBLESHOOTING

### Backend won't start
- **Error:** "No module named 'psycopg2'"
  - **Fix:** `cd backend && venv\Scripts\pip.exe install psycopg2-binary`

- **Error:** "Connection refused"
  - **Fix:** Check if PostgreSQL is running, verify .env credentials

- **Error:** "Port 5000 already in use"
  - **Fix:** Kill the process using port 5000 or change port in app.py

### Frontend can't connect to backend
- **Error:** "Failed to fetch" or CORS error
  - **Fix:** Make sure backend is running on port 5000
  - **Fix:** Check `frontend/config.js` has correct API_BASE_URL

### Admin login fails
- **Error:** "Invalid credentials"
  - **Fix:** Make sure you're entering ALL THREE fields (username + phone + password)
  - **Fix:** Check if admin exists in database (run init_db.py if needed)

### Images won't upload
- **Error:** "Cloudinary not configured"
  - **Fix:** Check backend/.env has CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
  - **Fix:** Verify credentials are correct

### Orders fail with "Insufficient stock"
- **Fix:** Check product stock in database
- **Fix:** Run init_db.py to reset database with sample products

---

## 📝 TESTING NOTES

- **Test data:** All sample products have stock=50, price=2600 ETB
- **Admin credentials:** KenoEthioShop / 0965806907 / Wisdomlife1@9
- **Test phone numbers:** Use 09XXXXXXXX format (Ethiopian)
- **Referral reward:** 50 ETB (triggered on first confirmed order)
- **Credit limits:** Max 50% of subtotal, max 500 ETB, max balance
- **Minimum order:** 500 ETB

---

**End of testing guide. Report any bugs or issues found during testing.**
