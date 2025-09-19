import os
import stripe
from flask import Flask, request, jsonify

app = Flask(__name__)

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
PRICE_ID = os.getenv("STRIPE_PRICE_ID")   # e.g. price_12345
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")  # starts with whsec_
YOUR_DOMAIN = "https://dispatchify-backend-2.onrender.com"  # your Render domain

print("🚀 Backend started")
print(f"STRIPE_SECRET_KEY set? {'Yes' if stripe.api_key else 'No'}")
print(f"PRICE_ID = {PRICE_ID}")
print(f"WEBHOOK_SECRET set? {'Yes' if WEBHOOK_SECRET else 'No'}")

# ------------------ Create Checkout Session ------------------
@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        data = request.get_json(silent=True) or {}
        customer_email = data.get("email")

        print(f"👉 /create-checkout-session called, email={customer_email}, price={PRICE_ID}")

        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{
                "price": PRICE_ID,
                "quantity": 1,
            }],
            customer_email=customer_email,
            success_url=f"{YOUR_DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{YOUR_DOMAIN}/cancel",
        )

        print(f"✅ Checkout session created: {session.id}")
        return jsonify({"url": session.url})

    except Exception as e:
        print(f"❌ Error creating checkout session: {str(e)}")  # <-- log exact error
        return jsonify(error=str(e)), 500

# ------------------ Webhook ------------------
@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return f"Webhook error: {e}", 400

    print(f"📩 Received event: {event['type']}")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session.get("customer_details", {}).get("email")
        print(f"✅ New subscription from {customer_email}")

    elif event["type"] == "invoice.payment_succeeded":
        sub = event["data"]["object"]["subscription"]
        print(f"✅ Subscription {sub} payment succeeded.")

    elif event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]["id"]
        print(f"❌ Subscription {sub} canceled or expired.")

    return "Success", 200

# ------------------ Check Subscription ------------------
@app.route("/check-subscription", methods=["POST"])
def check_subscription():
    try:
        data = request.get_json()
        email = data.get("email")

        print(f"👉 /check-subscription called for email={email}")

        if not email:
            return jsonify({"subscribed": False, "error": "Email required"}), 400

        customers = stripe.Customer.list(email=email).data
        if not customers:
            print("ℹ️ No customer found")
            return jsonify({"subscribed": False}), 200

        customer_id = customers[0].id
        subs = stripe.Subscription.list(customer=customer_id, status="active").data

        if subs:
            print("✅ Active subscription found")
            return jsonify({"subscribed": True}), 200
        else:
            print("❌ No active subscriptions")
            return jsonify({"subscribed": False}), 200

    except Exception as e:
        print(f"❌ Error in /check-subscription: {e}")
        return jsonify({"subscribed": False, "error": str(e)}), 400

# ------------------ Success & Cancel ------------------
@app.route("/success")
def success():
    return "✅ Subscription successful! You can now use Dispatchify Dialer."

@app.route("/cancel")
def cancel():
    return "❌ Subscription canceled. Please try again."

# ------------------ Run locally ------------------
if __name__ == "__main__":
    app.run(port=4242, debug=True)

