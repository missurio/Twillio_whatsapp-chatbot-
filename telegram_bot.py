# telegram_bot.py
import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from langchain_core.messages import AIMessage, HumanMessage
from rag_engine import get_rag_chain
from db_utils import save_chat, update_enrollment
import difflib

# =========================
# ENV & LOGGING
# =========================
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in .env file")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =========================
# CONFIG
# =========================
INACTIVITY_SECONDS = 300  # 5 minutes
MAX_HISTORY_LENGTH = 10
user_sessions = {}  # Stores chat history, enrollment status, last activity
user_timers = {}    # Stores per-user inactivity tasks

# =========================
# RAG ENGINE
# =========================
rag_chain = get_rag_chain()
if not rag_chain:
    logger.warning("⚠️ RAG chain not loaded. Bot will fallback to default messages.")

# =========================
# MESSAGES
# =========================
WELCOME_MESSAGE = """
👋 *Karibu ZHSF Digital Assistant*

Tunasaidia:
• Kujua kuhusu bima ya afya
• Kufahamu faida na michango
• Kujifunza jinsi ya kujiandikisha

📝 Je, tayari umejiunga na ZHSF?
"""

CLOSING_MESSAGE = """
Asante kwa kuzungumza nami! 🙏

Kuwa na bima ya afya ni njia bora zaidi ya kulinda afya yako na familia yako kutokana na gharama za matibabu yasiyotarajiwa.

Unaweza kujiandikisha:

📱 WhatsApp: 0756XXXXXX
🌐 Website: https://www.zhsf.go.tz

Andika chochote kuanza tena. 😊
"""

ENROLLMENT_CONTACT_MESSAGE = """
Ili kupata maelezo kamili au jibu la haraka kuhusu swali hili, tafadhali piga simu kwa huduma kwa wateja:

📱 12345678
"""

# =========================
# PREDEFINED QUESTIONS
# =========================
PREDEFINED_QUESTIONS = {
    "who owns you": "ZHSF",
    "who is your owner": "ZHSF",
    "ni nani mmiliki wako": "ZHSF",
    "nani anakumiliki": "ZHSF",
    "mmiliki wako ni nani": "ZHSF",
    "who created you": "ZHSF Team",
    "who made you": "ZHSF Team",
    "nani alikutengeneza": "ZHSF Team",
    "alikutengeneza nani": "ZHSF Team",
    "what is your name": "ZHSF ChatBot",
    "jina lako": "ZHSF ChatBot",
    "una jina gani": "ZHSF ChatBot",
    "how are you": "Niko sawa, asante! 😊",
    "how do you do": "Niko sawa, asante! 😊",
    "unaendeleaje": "Niko sawa, asante kwa kuuliza! 😊",
    "what do you do": "Ninaweza kukusaidia kujua kuhusu bima ya afya na maswali mengine.",
    "unafanya nini": "Ninaweza kukusaidia kujua kuhusu bima ya afya na maswali mengine.",
    "kwa nini umetengenezwa": "Nimetengenezwa kukusaidia kuhusu bima ya afya na maswali mengine.",
    "thank you": "Karibu! 😊",
    "asante": "Karibu! 😊",
}
FUZZY_THRESHOLD = 0.7  # 70% similarity for fuzzy matching

def match_predefined(user_input: str):
    user_input_clean = user_input.lower().strip()
    matches = difflib.get_close_matches(user_input_clean, PREDEFINED_QUESTIONS.keys(), n=1, cutoff=FUZZY_THRESHOLD)
    if matches:
        return PREDEFINED_QUESTIONS[matches[0]]
    return None

# =========================
# ENROLLMENT BUTTONS
# =========================
def enrollment_buttons():
    keyboard = [
        [InlineKeyboardButton("✅ YES", callback_data="ENROLL_YES")],
        [InlineKeyboardButton("❌ NO", callback_data="ENROLL_NO")]
    ]
    return InlineKeyboardMarkup(keyboard)

# =========================
# START COMMAND
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_sessions[chat_id] = {"history": [], "enrolled": None, "last_activity": datetime.now()}
    await update.message.reply_text(
        WELCOME_MESSAGE,
        parse_mode="Markdown",
        reply_markup=enrollment_buttons()
    )

# =========================
# HANDLE ENROLLMENT BUTTON
# =========================
async def handle_enrollment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    enrolled = True if query.data == "ENROLL_YES" else False
    if user_id not in user_sessions:
        user_sessions[user_id] = {"history": [], "enrolled": enrolled, "last_activity": datetime.now()}
    else:
        user_sessions[user_id]["enrolled"] = enrolled
        user_sessions[user_id]["last_activity"] = datetime.now()

    # Save enrollment in DB
    update_enrollment(str(user_id), "Yes" if enrolled else "No")

    # Remove buttons & send friendly message
    msg_text = "Asante! Sasa unaweza kuuliza maswali yote kuhusu bima ya afya 😊" if enrolled else \
               "Sawa! Unaweza kuuliza maswali, lakini fikiria kujiunga ili kupata faida kamili. 😊"
    await query.edit_message_text(msg_text)

    # Start/reset inactivity timer
    if user_id in user_timers:
        user_timers[user_id].cancel()
    user_timers[user_id] = asyncio.create_task(schedule_inactivity(user_id, context))

# =========================
# HANDLE USER MESSAGES
# =========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = datetime.now()
    enrolled_status = user_sessions.get(user_id, {}).get("enrolled")

    # First message OR user not enrolled yet
    if user_id not in user_sessions or enrolled_status is None:
        user_sessions[user_id] = {"history": [], "enrolled": None, "last_activity": now}
        await update.message.reply_text(
            WELCOME_MESSAGE,
            parse_mode="Markdown",
            reply_markup=enrollment_buttons()
        )
        return

    # Update last activity & reset timer
    user_sessions[user_id]["last_activity"] = now
    if user_id in user_timers:
        user_timers[user_id].cancel()
    user_timers[user_id] = asyncio.create_task(schedule_inactivity(user_id, context))

    user_input = update.message.text.strip()
    chat_history = user_sessions[user_id].get("history", [])

    # =========================
    # Predefined questions
    # =========================
    predefined_response = match_predefined(user_input)
    if predefined_response:
        response_text = predefined_response
        await update.message.reply_text(response_text)
        save_chat(
            user_id=str(user_id),
            question=user_input,
            answer=response_text,
            platform="telegram",
            enrollment_status="Yes" if enrolled_status else "No"
        )
        return

    # =========================
    # RAG engine response
    # =========================
    if not rag_chain:
        await update.message.reply_text("⚠️ RAG engine not available.")
        return

    await update.message.reply_chat_action('typing')
    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: rag_chain.invoke({"input": user_input, "chat_history": chat_history})
        )
        response_text = response.get("answer", str(response)) if isinstance(response, dict) else str(response)

        # If RAG returns null, provide customer care contact
        if not response_text or response_text.strip() == "":
            response_text = "📞 Kwa usaidizi zaidi, tafadhali piga simu 12345678."

        await update.message.reply_text(response_text)

        # Update chat history
        chat_history.append(HumanMessage(content=user_input))
        chat_history.append(AIMessage(content=response_text))
        if len(chat_history) > MAX_HISTORY_LENGTH:
            chat_history = chat_history[-MAX_HISTORY_LENGTH:]
        user_sessions[user_id]["history"] = chat_history

        # Save chat in DB
        save_chat(
            user_id=str(user_id),
            question=user_input,
            answer=response_text,
            platform="telegram",
            enrollment_status="Yes" if enrolled_status else "No"
        )

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text("Sorry, I encountered an error processing your request.")

# =========================
# INACTIVITY HANDLER
# =========================
async def schedule_inactivity(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    try:
        await asyncio.sleep(INACTIVITY_SECONDS)
        await context.bot.send_message(chat_id=user_id, text=CLOSING_MESSAGE, parse_mode="Markdown")
        user_sessions.pop(user_id, None)
        user_timers.pop(user_id, None)
    except asyncio.CancelledError:
        return

# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_enrollment, pattern="ENROLL_.*"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("✅ Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
