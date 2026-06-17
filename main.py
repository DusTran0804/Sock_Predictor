import os
import time
import threading
from datetime import datetime
import pytz
from dotenv import load_dotenv

# Import our modular components
from agent import run_analysis
from bot import run_chatbot

# Load environment variables from .env
load_dotenv()

def main():
    print("====================================================")
    print("VIETNAM STOCK PREDICTION & CHATBOT SYSTEM")
    print("====================================================")
    
    import sys
    ticker = ""

    # 1. Check command-line arguments (e.g. python main.py HPG)
    if len(sys.argv) > 1:
        ticker = sys.argv[1].strip().upper()

    # 2. Check environment variable
    if not ticker:
        ticker = os.environ.get("DEFAULT_TICKER", "").strip().upper()

    # 3. Check interactive input if in a terminal
    if not ticker and sys.stdin.isatty():
        try:
            ticker = input("Nhập mã cổ phiếu muốn theo dõi hàng ngày: ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            pass

    print(f"System configured for daily reports at 07:00 AM (Vietnam Time) for ticker: {ticker}")
    print("Starting Telegram chatbot and scheduler threads...")

    # Start the conversational chatbot in a background thread
    chatbot_thread = threading.Thread(target=run_chatbot, daemon=True)
    chatbot_thread.start()
    print("Chatbot thread running in background.")

    # Timezone configuration
    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    print(f"Scheduler active. Checking every 30s. Target: 07:00 AM ({vn_tz.zone})")
    print("Press Ctrl+C to stop the system.\n")

    # Scheduler loop
    try:
        while True:
            now_vn = datetime.now(vn_tz)
            # Check if it is exactly 7:00 AM
            if now_vn.hour == 7 and now_vn.minute == 0:
                print(f"Scheduled Time reached! Running daily report for {ticker}...")
                run_analysis(ticker)
                # Sleep for 61 seconds to prevent triggering multiple times in the same minute
                time.sleep(61)
            else:
                time.sleep(30)
    except KeyboardInterrupt:
        print("\nSystem stopped by user. Goodbye!")

if __name__ == "__main__":
    main()
