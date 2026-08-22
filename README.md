# ELROI FAST FOOD — ordering website

A Flask ordering system inspired by the convenience of major fast-food ordering sites. It is **not a copy of McDonald's/KFC branding**. It uses the ELROI FAST FOOD branding and the menu/prices supplied in the poster.

## Included
- 5-second ELROI logo loading screen on the customer home page
- Full menu grouped by category
- Cart with multiple meals
- Quantity controls
- Per-meal remove-ingredient choices
- Per-meal add-on choices with prices
- Special notes
- Cash & collect
- Card-before-collection through a secure external payment checkout URL configured by the Creator
- WhatsApp order confirmation using +27 64 398 1061
- Delivery marked "Coming Soon"
- Order number and CODE128 barcode
- Customer live status page
- Admin statuses: Preparing, Almost Done, Collect Now, Completed, Cancelled
- Admin camera barcode scanner + manual fallback
- Admin meal management
- Admin meal photo uploads (products start without photos)
- Creator dashboard
- Creator maintenance mode
- Creator staff account management
- Creator payment-link settings
- SQLite database for simple deployment
- Render/GitHub files included

## Default staff accounts
**Admin**
- username: `admin`
- password: `ElroiAdmin123!`

**Creator**
- username: `creator`
- password: `ElroiCreator123!`

Change these immediately after first login.

## Run on a computer
```bash
pip install -r requirements.txt
python app.py
```
Open `http://127.0.0.1:5000`

## Pydroid 3
Install Flask and Gunicorn from Pydroid's pip, then run:
```bash
python app.py
```
Open `http://127.0.0.1:5000`

## GitHub + Render
1. Create a GitHub repository.
2. Upload all files in this folder.
3. In Render, create a Web Service from the repository.
4. Render uses `render.yaml`, or use:
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn app:app`
5. Add a strong `SECRET_KEY` environment variable if Render did not generate one.
6. Open the site and log in at `/login`.
7. Go to Creator Dashboard and change the staff credentials.
8. In Creator Dashboard, add a **secure hosted payment checkout URL** for card-before-collection.

### Important Render storage note
This starter uses SQLite because it is the easiest zero-setup deployment. SQLite data can be lost if the hosting service recreates the instance. For a production store, use a persistent Render disk (where available) or migrate the database to PostgreSQL before relying on it for real orders.

## Card payments
Do **not** put a raw bank-card number, CVV, or customer's card details into this application. The Creator Dashboard accepts a hosted payment/checkout URL from a payment provider. The customer is sent to that provider to enter card details securely.

## Security
- Change default usernames/passwords.
- Set a strong `SECRET_KEY`.
- Keep payment processing on a trusted payment provider.
- Use HTTPS in production.
- Back up the database if using SQLite.
