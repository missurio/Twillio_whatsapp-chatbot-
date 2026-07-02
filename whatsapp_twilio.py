import os
import traceback
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

from rag_engine import get_rag_chain

load_dotenv()

app = Flask(__name__)

# ── Load RAG chain ─────────────────────────
print("⏳ Loading RAG chain...")
rag_chain = None

try:
    rag_chain = get_rag_chain()
except Exception as e:
    print("❌ Failed to load RAG chain:", e)

if rag_chain is None:
    print("❌ RAG chain NOT loaded — check FAISS index / OpenAI / path")
else:
    print("✅ RAG chain loaded successfully!")


# ── Memory store ───────────────────────────
chat_histories = {}
MAX_HISTORY = 10


def update_history(user, role, message):
    if not user:
        return

    chat_histories.setdefault(user, [])
    chat_histories[user].append((role, message))
    chat_histories[user] = chat_histories[user][-MAX_HISTORY:]


# ── HEALTH CHECK (IMPORTANT FOR RENDER) ────
@app.route("/", methods=["GET"])
def home():
    return "WhatsApp Bot is running ✔"


# ── WHATSAPP WEBHOOK ───────────────────────
@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():

    incoming_msg = request.values.get("Body")
    user_number = request.values.get("From")

    if not incoming_msg:
        incoming_msg = ""

    print(f"\n📩 Message from {user_number}: {incoming_msg}")

    update_history(user_number, "human", incoming_msg)

    try:
        if rag_chain is None:
            raise Exception("RAG chain not initialized")

        # ✔ FIX: correct input format
        result = rag_chain.invoke({
            "input": incoming_msg,
            "chat_history": chat_histories.get(user_number, [])
        })

        # handle different LangChain outputs
        response = result.content if hasattr(result, "content") else result

        print("🤖 Response:", response)

    except Exception as e:
        print("\n❌ FULL ERROR TRACE:")
        traceback.print_exc()
        response = f"⚠️ Bot Error: {str(e)}"

    update_history(user_number, "ai", response)

    twilio_resp = MessagingResponse()
    twilio_resp.message(str(response))

    return str(twilio_resp)


# ── RUN APP (RENDER READY) ─────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)