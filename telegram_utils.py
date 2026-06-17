import os
import re
import requests

def send_telegram_report(message: str, ticker: str = "", chat_id: str = None):
    """Send report directly to Telegram with HTML sanitization"""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not chat_id:
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        
    if not bot_token or not chat_id:
        print("⚠️ Telegram not configured (missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID)")
        return
        
    # Translate markdown bold/italic to HTML
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', message, flags=re.DOTALL)
    text = re.sub(r'\*([^*\n]+?)\*', r'<i>\1</i>', text)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    
    # HTML Sanitization
    allowed = {'b', 'i', 'code', 'pre', 'a', 's', 'u'}
    def clean_tag(m):
        tag = re.sub(r'[^a-zA-Z]', '', m.group(1)).lower()
        return '' if tag not in allowed else m.group(0)
        
    text = re.sub(r'<(/?[\w]+)[^>]*>', clean_tag, text)
    text = text[:4090].strip()
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            print(f"✅ Report sent to Telegram chat {chat_id} successfully!")
        else:
            print(f"⚠️ HTML formatting failed ({resp.json().get('description', '')}), attempting plain text...")
            # Fallback to plain text
            plain = re.sub(r'<[^>]+>', '', text)
            payload_plain = {
                "chat_id": chat_id,
                "text": plain
            }
            resp2 = requests.post(url, json=payload_plain, timeout=15)
            if resp2.status_code == 200:
                print(f"✅ Plain text fallback report sent to Telegram chat {chat_id} successfully!")
            else:
                print(f"❌ Telegram API send failed: {resp2.text}")
    except Exception as e:
        print(f"❌ Exception sending telegram message: {e}")

def send_telegram_photo(photo_path: str, caption: str = "", chat_id: str = None):
    """Send a photo to Telegram, with a fallback to text report if it fails."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not chat_id:
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        
    if not bot_token or not chat_id:
        print("⚠️ Telegram not configured (missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID)")
        return
        
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    
    # If the report is too long for a Telegram caption (max 1024 chars),
    # we send the photo with a short title, then send the full report text separately.
    send_separately = len(caption) > 1000
    
    if send_separately:
        # Extract ticker from caption if possible (e.g. BÁO CÁO CHỨNG KHOÁN - FPT)
        ticker_match = re.search(r'BÁO CÁO CHỨNG KHOÁN - ([A-Z0-9]+)', caption)
        ticker = ticker_match.group(1) if ticker_match else ""
        ticker_label = f" - {ticker}" if ticker else ""
        short_caption = f"📈 <b>Biểu đồ kỹ thuật phân tích{ticker_label}</b>"
    else:
        # Translate markdown styles for caption
        short_caption = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', caption, flags=re.DOTALL)
        short_caption = re.sub(r'\*([^*\n]+?)\*', r'<i>\1</i>', short_caption)
        
    payload = {
        "chat_id": chat_id,
        "caption": short_caption,
        "parse_mode": "HTML"
    }
    
    try:
        if not os.path.exists(photo_path):
            raise FileNotFoundError(f"Chart photo file not found at {photo_path}")
            
        with open(photo_path, 'rb') as photo_file:
            files = {"photo": photo_file}
            resp = requests.post(url, data=payload, files=files, timeout=30)
            
        if resp.status_code == 200:
            print(f"✅ Chart photo sent to Telegram chat {chat_id} successfully!")
            if send_separately:
                # Send the full report message as a follow-up text message
                send_telegram_report(caption, chat_id=chat_id)
        else:
            print(f"⚠️ Telegram photo send failed ({resp.json().get('description', '')}), falling back to text-only...")
            send_telegram_report(caption, chat_id=chat_id)
            
    except Exception as e:
        print(f"❌ Exception sending telegram photo: {e}, falling back to text-only...")
        send_telegram_report(caption, chat_id=chat_id)
