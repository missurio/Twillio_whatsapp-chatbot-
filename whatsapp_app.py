import os
import json
import hashlib
import hmac
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

# ── Your RAG engine ──────────────────────────────────────────
from rag_engine import get_rag_chain
from langchain_core.messages import AIMessage, HumanMessage

load_dotenv()

app = Flask(__name__)

# ── Fix ngrok browser warning (allows Meta webhook to reach Flask) ──
@app.after_request
def add_ngrok_header(response):
    response.headers['ngrok-skip-browser-warning'] = 'true'
    return response

# ── Credentials from environment variables ───────────────────
WHATSAPP_TOKEN  = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN    = os.getenv("VERIFY_TOKEN")
APP_SECRET      = os.getenv("APP_SECRET")

# ── Per-user chat history (in-memory) ────────────────────────
chat_histories = {}
MAX_HISTORY = 10

# ── Load RAG chain once at startup ───────────────────────────
print("⏳ Loading RAG chain...")
rag_chain = get_rag_chain()
if rag_chain:
    print("✅ RAG chain loaded successfully!")
else:
    print("❌ RAG chain failed — check your faiss_index folder")


# ════════════════════════════════════════════════════════════
# 1. WEBHOOK VERIFICATION
# ════════════════════════════════════════════════════════════
@app.route("/webhook", methods=["GET"])
def verify():
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verified by Meta!")
        return challenge, 200
    return "Forbidden", 403


# ════════════════════════════════════════════════════════════
# 2. RECEIVE & REPLY TO MESSAGES
# ════════════════════════════════════════════════════════════
@app.route("/webhook", methods=["POST"])
def webhook():
    if APP_SECRET:
        verify_signature(request)

    data = request.get_json()
    print(f"📨 Incoming: {json.dumps(data, indent=2)}")

    try:
        entry = data["entry"][0]["changes"][0]["value"]

        if "messages" not in entry:
            return jsonify({"status": "ok"}), 200

        message     = entry["messages"][0]
        from_number = message["from"]
        msg_type    = message.get("type")

        if msg_type != "text":
            send_message(from_number,
                "Samahani, ninajibu maswali ya maandishi tu. 🙏\n"
                "Sorry, I can only answer text questions. 🙏")
            return jsonify({"status": "ok"}), 200

        user_text = message["text"]["body"].strip()
        print(f"👤 [{from_number}]: {user_text}")

        if from_number not in chat_histories:
            chat_histories[from_number] = []

        history = chat_histories[from_number]

        if not rag_chain:
            answer = "System is not ready yet. Please try again in a few minutes."
        else:
            answer = rag_chain.invoke({
                "input": user_text,
                "chat_history": history
            })

        print(f"🤖 Bot → [{from_number}]: {answer}")

        history.append(HumanMessage(content=user_text))
        history.append(AIMessage(content=answer))

        if len(history) > MAX_HISTORY * 2:
            chat_histories[from_number] = history[-(MAX_HISTORY * 2):]

        send_message(from_number, answer)

    except (KeyError, IndexError) as e:
        print(f"⚠️  Skipped event: {e}")

    return jsonify({"status": "ok"}), 200


# ════════════════════════════════════════════════════════════
# 3. SEND A WHATSAPP MESSAGE
# ════════════════════════════════════════════════════════════
def send_message(to: str, body: str):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body}
    }
    r = requests.post(url, headers=headers, json=payload)
    print(f"📤 Sent → {to} | Status: {r.status_code}")
    if r.status_code != 200:
        print(f"❌ Error: {r.text}")


# ════════════════════════════════════════════════════════════
# 4. VERIFY REQUEST IS FROM META (security)
# ════════════════════════════════════════════════════════════
def verify_signature(req):
    signature = req.headers.get("X-Hub-Signature-256", "")
    if not signature:
        return
    expected = "sha256=" + hmac.new(
        APP_SECRET.encode(),
        req.data,
        hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        print("⚠️  Invalid signature — possible spoofed request")


# ════════════════════════════════════════════════════════════
# 5. HEALTH CHECK
# ════════════════════════════════════════════════════════════
@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "status": "running",
        "rag_ready": rag_chain is not None,
        "bot": "WhatsApp FAQ Bot"
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)