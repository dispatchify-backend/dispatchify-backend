from flask import Flask, request, jsonify
import stripe
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow requests from your Tkinter app

# --- Stripe Setup ---
import os
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

PRICE_ID = "prod_T5BsNO8iW9t0LM"

# Developer access (bypass subscription)
DEVELOPER_EMAILS = ["dispatchifyllc@gmail.com"]

@app.route("/")
def home():
    return jsonify({"message": "Backend is running ✅"}), 200

@app.route("/check-subscription", methods=["POST"])
def check_subscription():
    try:
        data = request.json
        email = data.get("email", "").lower()

        # Developer bypass
        if email in [dev.lower() for dev in DEVELOPER_EMAILS]:
            return jsonify({"subscribed": True})

        # Look up customer by email
        customers = stripe.Customer.list(email=email).data
        if not customers:
            return jsonify({"subscribed": False})

        customer_id = customers[0].id

        # Check active subscriptions
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status='active',
            limit=1
        ).data

        is_active = len(subscriptions) > 0
        return jsonify({"subscribed": is_active})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        data = request.json
        email = data.get("email")

        # Create a Stripe Checkout Session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='subscription',
            line_items=[{
                'price': PRICE_ID,
                'quantity': 1,
            }],
            customer_email=email,
            success_url="https://google.com",  # replace later with real page
            cancel_url="https://google.com",
        )

        return jsonify({"url": session.url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Important: Render will set PORT env variable automatically
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
