# EthioShop — Quick Start Guide

**Last Updated:** May 28, 2026

---

## 🚀 START THE SYSTEM (3 STEPS)

### Step 1: Start Backend
```cmd
cd c:\Users\kenot\Desktop\ethioshop\backend
venv\Scripts\python.exe app.py
```
✅ **Expected:** Server running on http://127.0.0.1:5000

### Step 2: Open Customer Shop
Open in browser:
```
file:///c:/Users/kenot/Desktop/ethioshop/frontend/index.html
```

### Step 3: Open Admin Panel
Open in browser:
```
file:///c:/Users/kenot/Desktop/ethioshop/admin-panel/index.html
```

**Admin Login:**
- Username: `KenoEthioShop`
- Phone: `0965806907`
- Password: `Wisdomlife1@9`

---

## 🧪 QUICK TEST (5 MINUTES)

### Customer Side
1. **Browse products:** Open `frontend/shop.html`
2. **Add to cart:** Click "Add to Cart" on any product
3. **Checkout:** Click cart icon → "Proceed to Checkout"
4. **Place order:** Enter phone `0912345678`, name, address → "Place Order"
5. **Upload payment proof:** Upload any image on success page

### Admin Side
1. **Login:** Use credentials above
2. **View orders:** Click "Orders" in sidebar
3. **Verify order:** Click "View" → "Verify Order" → "Approve"
4. **Assign delivery:** Click "Assign Delivery" → Enter name/phone
5. **Update status:** Click "In Transit" → "Delivered"

---

## 📚 DOCUMENTATION

- **FINAL_SUMMARY.md** — What was built (15 KB)
- **PROJECT_ANALYSIS.md** — How it works (39 KB, 920 lines)
- **TESTING_GUIDE.md** — How to test (25 KB, 25 scenarios)

---

## 🔗 KEY URLS

### Customer
- Shop: `frontend/shop.html`
- Cart: `frontend/cart.html`
- Checkout: `frontend/checkout.html`
- Dashboard: `frontend/dashboard.html`
- Track Order: `frontend/status.html`
- Request Product: `frontend/request.html`

### Admin
- Login: `admin-panel/index.html`
- Dashboard: `admin-panel/dashboard.html`
- Orders: `admin-panel/orders.html`
- Products: `admin-panel/products.html`
- Admins: `admin-panel/admins.html`

### API
- Health: `http://localhost:5000/health`
- Products: `http://localhost:5000/api/products`
- Orders: `http://localhost:5000/api/orders`

---

## 🐛 TROUBLESHOOTING

### Backend won't start
```cmd
cd backend
venv\Scripts\pip.exe install -r requirements.txt
```

### "Connection refused"
- Check if backend is running on port 5000
- Visit http://localhost:5000/health

### Admin login fails
- Make sure you enter ALL THREE fields
- Username: KenoEthioShop
- Phone: 0965806907
- Password: Wisdomlife1@9

### Images won't upload
- Check backend/.env has Cloudinary credentials
- CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET

---

## 💡 QUICK TIPS

### Reset Database
```cmd
cd backend
venv\Scripts\python.exe init_db.py
```
⚠️ **Warning:** This deletes ALL data!

### Check Database Connection
Visit: http://localhost:5000/health

### View Backend Logs
Check the terminal where you ran `python app.py`

### Test Phone Numbers
Use Ethiopian format: `09XXXXXXXX` or `+251XXXXXXXXX`

### Test Credit System
1. Create user A with referral code
2. Create user B using A's referral code
3. Verify user B's first order
4. User A gets 50 ETB credit

---

## 📊 SYSTEM STATUS

✅ **Backend:** Flask + PostgreSQL (Supabase)  
✅ **Frontend:** Plain HTML/JS (no build step)  
✅ **Admin Panel:** Plain HTML/JS (no build step)  
✅ **Database:** 10 tables, all migrations applied  
✅ **Features:** Orders, Cart, Referrals, Credit, Refunds, Delivery  
✅ **Security:** JWT auth, bcrypt passwords, rate limiting  
✅ **Documentation:** 3 comprehensive guides (80 KB total)  

---

## 🎯 NEXT STEPS

1. **Test everything:** Follow TESTING_GUIDE.md (25 scenarios)
2. **Understand the code:** Read PROJECT_ANALYSIS.md
3. **Deploy:** See FINAL_SUMMARY.md → Deployment Checklist

---

**Need help?** Check the documentation files or backend route files for API details.
