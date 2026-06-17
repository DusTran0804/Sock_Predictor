import os
import re
import threading
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# Import the analysis function to be run in the background
from agent import run_analysis

load_dotenv()

# Initialize the OpenAI client pointing to local Ollama
ollama_base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip('/')
client = OpenAI(
    base_url=f"{ollama_base_url}/v1",
    api_key="ollama"
)

# In-memory dictionaries
session_memories = {}
session_states = {}  # Tracks if a user is in a state like "WAITING_FOR_TICKER"

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Bạn là một trợ lý ảo thông minh, thân thiện và am hiểu về tài chính, chứng khoán Việt Nam. "
        "Hãy luôn trả lời và trò chuyện hoàn toàn bằng tiếng Việt một cách tự nhiên, gần gũi và chính xác."
    )
}

def get_chat_history(chat_id: int) -> list:
    """Retrieve history for a chat session, initializing it if empty"""
    if chat_id not in session_memories:
        session_memories[chat_id] = [SYSTEM_PROMPT]
    return session_memories[chat_id]

def clear_chat_history(chat_id: int):
    """Clear memory for a chat session"""
    session_memories[chat_id] = [SYSTEM_PROMPT]

def run_analysis_in_background(ticker: str, chat_id: str):
    """Run the analysis pipeline in a background thread to prevent blocking the bot."""
    try:
        run_analysis(ticker, chat_id=chat_id)
    except Exception as e:
        print(f"❌ Error in background analysis thread: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    clear_chat_history(chat_id)
    session_states[chat_id] = None
    
    welcome_text = (
        f"Hi {user.mention_html()}! I am your AI Assistant powered by Ollama (Qwen 2.5).\n\n"
        "How to use:\n"
        "1. 💬 **Chat with me** about anything by typing a message.\n"
        "2. 📊 **Analyze a stock**: Type `/analyze` and I will ask you for a stock symbol. "
        "Alternatively, you can type `/analyze FPT` or simply send `FPT` directly!\n\n"
        "Commands:\n"
        "/start - Restart conversation and clear memory\n"
        "/analyze - Start stock analysis\n"
        "/clear - Clear conversation memory"
    )
    await update.message.reply_html(welcome_text)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear conversational memory."""
    chat_id = update.effective_chat.id
    clear_chat_history(chat_id)
    session_states[chat_id] = None
    await update.message.reply_text("🧹 Conversation memory cleared!")

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /analyze command."""
    chat_id = update.effective_chat.id
    args = context.args
    
    if args:
        # User provided a ticker directly, e.g., /analyze FPT
        ticker = args[0].strip().upper()
        if not re.match(r'^[A-Z0-9]{3,6}$', ticker):
            await update.message.reply_text("⚠️ Mã cổ phiếu không hợp lệ. Vui lòng nhập mã từ 3-6 ký tự chữ hoặc số.")
            return
            
        await update.message.reply_text(f"🔍 Nhận yêu cầu phân tích mã <b>{ticker}</b>.\nĐang tiến hành phân tích dữ liệu và chạy AI, vui lòng chờ trong giây lát...", parse_mode="HTML")
        # Start analysis in a background thread
        threading.Thread(target=run_analysis_in_background, args=(ticker, str(chat_id)), daemon=True).start()
    else:
        # Prompt user to input a ticker
        session_states[chat_id] = "WAITING_FOR_TICKER"
        await update.message.reply_text("Bạn muốn phân tích mã cổ phiếu nào? Vui lòng nhập mã cổ phiếu (ví dụ: FPT, HPG, VNM):")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process incoming messages, handle stock requests, or execute general AI chats."""
    chat_id = update.effective_chat.id
    user_message = update.message.text
    
    if not user_message:
        return
 
    # Check if the user is in a state waiting for a stock ticker input
    if session_states.get(chat_id) == "WAITING_FOR_TICKER":
        session_states[chat_id] = None  # Reset state
        ticker = user_message.strip().upper()
        
        if not re.match(r'^[A-Z0-9]{3,6}$', ticker):
            session_states[chat_id] = "WAITING_FOR_TICKER"  # Put back in state
            await update.message.reply_text("⚠️ Mã cổ phiếu không hợp lệ. Vui lòng nhập lại mã cổ phiếu (ví dụ: FPT, HPG):")
            return
            
        await update.message.reply_text(f"🔍 Nhận yêu cầu phân tích mã <b>{ticker}</b>.\nĐang tiến hành phân tích dữ liệu và chạy AI, vui lòng chờ trong giây lát...", parse_mode="HTML")
        threading.Thread(target=run_analysis_in_background, args=(ticker, str(chat_id)), daemon=True).start()
        return

    # Check if the user directly messaged a standard 3-letter ticker symbol (e.g. FPT, HPG)
    cleaned_msg = user_message.strip().upper()
    if re.match(r'^[A-Z]{3}$', cleaned_msg):
        await update.message.reply_text(f"🔍 Nhận yêu cầu phân tích mã <b>{cleaned_msg}</b>.\nĐang tiến hành phân tích dữ liệu và chạy AI, vui lòng chờ trong giây lát...", parse_mode="HTML")
        threading.Thread(target=run_analysis_in_background, args=(cleaned_msg, str(chat_id)), daemon=True).start()
        return

    # Normal Conversational Flow (AI Chatbot)
    await context.bot.send_chat_action(chat_id=chat_id, action='typing')

    history = get_chat_history(chat_id)
    history.append({"role": "user", "content": user_message})

    # Keep conversation length bounded
    if len(history) > 11:
        history = [history[0]] + history[-10:]
        session_memories[chat_id] = history

    try:
        response = client.chat.completions.create(
            model="qwen2.5:3b",
            messages=history,
            temperature=0.7,
            timeout=30.0
        )
        ai_response = response.choices[0].message.content
        
        history.append({"role": "assistant", "content": ai_response})
        session_memories[chat_id] = history
        
        await update.message.reply_text(ai_response)
        
    except Exception as e:
        print(f"❌ Error communicating with Ollama: {e}")
        await update.message.reply_text(
            f"Sorry, I encountered an error connecting to my local brain: {str(e)}"
        )

def run_chatbot():
    """Starts the Telegram bot in polling mode."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token or bot_token == "your_telegram_bot_token_here":
        print("⚠️ TELEGRAM_BOT_TOKEN is not set correctly. Chatbot cannot start.")
        return

    application = Application.builder().token(bot_token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Conversational Telegram Bot is starting (polling mode)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)

if __name__ == "__main__":
    run_chatbot()
