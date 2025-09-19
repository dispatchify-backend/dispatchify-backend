import os
from flask import Flask, request, jsonify
import stripe

app = Flask(__name__)

# ===== Stripe Setup =====
# Make sure you set this in your Render environment (Dashboard → Environment → STRIPE_SECRET_KEY)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# If you use sandbox/test mode, use your test secret key here:
# stripe.api_key = "sk_test_xxxxxxxxxxxxxxxxxxxxx"

# Example: fixed price ID for subscription (from your Stripe dashboard)
PRICE_ID = os.getenv("STRIPE_PRICE_ID", "price_xxxxxxxxxxxxx")

# ===== Routes =====

@app.route("/", methods=["GET"])
def home():
    return "✅ Backend is running", 200


@app.route("/login", methods=["POST"])
def login():
    """Basic fake login (just demo)."""
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email required"}), 400

    # In real case you’d check DB for the user
    return jsonify({"message": "Login successful", "email": email}), 200


@app.route("/check-subscription", methods=["POST"])
def check_subscription():
    """Check if a user has an active subscription."""
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email required"}), 400

    # Demo: always return False for now
    return jsonify({"active": False}), 200


@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    """Create a Stripe Checkout session."""
    try:
        YOUR_DOMAIN = "https://dispatchify-frontend.onrender.com"  # update to your frontend URL

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{"price": PRICE_ID, "quantity": 1}],
            success_url=f"{YOUR_DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{YOUR_DOMAIN}/cancel",
        )
        return jsonify({"url": session.url})

    except Exception as e:
        # Print full error for debugging
        print("❌ Error in /create-checkout-session:", str(e))
        return jsonify({"error": str(e)}), 500


# ===== Error Handlers =====

@app.errorhandler(404)
def page_not_found(e):
    print("❌ 404 Not Found:", request.path)
    return jsonify({"error": "Route not found", "path": request.path}), 404


@app.errorhandler(500)
def internal_error(e):
    print("❌ 500 Internal Server Error:", str(e))
    return jsonify({"error": "Internal server error"}), 500


# ===== Run (for local only, Render uses gunicorn) =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


