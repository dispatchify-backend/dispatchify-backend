from flask import Flask, request, jsonify
from flask_cors import CORS
import stripe
import os

app = Flask(__name__)
CORS(app)

# ----------------- CONFIG -----------------
# Set your Stripe test secret key here
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_xxxxx")

YOUR_DOMAIN = "https://dispatchify-backend-1.onrender.com"
PRODUCT_ID = os.environ.get("STRIPE_PRODUCT_ID", "prod_xxxxx")

# Temporary in-memory user storage (for testing)
users = {}
# ------------------------------------------


@app.route("/")
def home():
    return jsonify({"message": "✅ Backend is running!"})


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400

    users[email] = {"subscribed": users.get(email, {}).get("subscribed", False)}
    return jsonify({"success": True, "email": email})


@app.route("/check-subscription", methods=["POST"])
def check_subscription():
    data = request.get_json()
    email = data.get("email")

    if not email or email not in users:
        return jsonify({"subscribed": False})

    return jsonify({"subscribed": users[email]["subscribed"]})


@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.get_json()
    email = data.get("email")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{"price": PRODUCT_ID, "quantity": 1}],
            success_url=YOUR_DOMAIN + "/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=YOUR_DOMAIN + "/cancel",
            customer_email=email
        )
        return jsonify({"url": session.url})
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        return str(e), 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        email = session.get("customer_email")
        if email in users:
            users[email]["subscribed"] = True

    elif event["type"] == "customer.subscription.deleted":
        email = event["data"]["object"].get("customer_email")
        if email in users:
            users[email]["subscribed"] = False

    return "", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
