import os
import time
import json
import requests

# âš ï¸ GET A TOKEN FROM @BotFather ON TELEGRAM AND PASTE IT HERE âš ï¸
TOKEN = "8694700404:AAG9xZBjasDRhozAi2jOZA5ug9T0Z_s1oDU"
API_URL = f"https://api.telegram.org/bot{TOKEN}/"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "OUTPUT"))
QUEUE_FILE = os.path.join(OUTPUT_DIR, "scheduled_uploads.json")

def get_updates(offset=None):
    url = API_URL + "getUpdates"
    params = {"timeout": 100, "offset": offset}
    try:
        res = requests.get(url, params=params, timeout=110)
        return res.json()
    except Exception:
        return {"ok": False, "result": []}

def send_message(chat_id, text):
    url = API_URL + "sendMessage"
    params = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=params)

def read_queue():
    if not os.path.exists(QUEUE_FILE): return []
    try:
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return []

def write_queue(q):
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(q, f, indent=4)

def handle_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    
    if text == "/start":
        send_message(chat_id, "ğŸ›¸ *JETBOX Remote Console* ğŸ›¸\n\nGreetings from Earth! Start managing your uploads:\n`/queue` - See what's waiting for schedule\n`/clear` - Delete all scheduled beats\n`/stats` - Quick stats")
    
    elif text == "/queue":
        q = read_queue()
        if not q:
            send_message(chat_id, "ğŸ“­ Queue is empty. No uploads scheduled.")
            return
            
        msg = f"ğŸ“‹ *Scheduled Beats ({len(q)})*\n\n"
        for i, item in enumerate(q):
            schedule_hour = item.get("schedule_hour", 22)
            msg += f"*{i+1}.* {item.get('title')} (Size: {item.get('mp4_path', '').split('/')[-1]}) - [{schedule_hour}:00]\n"
        msg += "\n*These will be uploaded today at their scheduled times.*"
        send_message(chat_id, msg)
        
    elif text == "/clear":
        write_queue([])
        send_message(chat_id, "🗑ï¸ All scheduled beats have been cancelled.")

    elif text == "/stats":
        q = read_queue()
        send_message(chat_id, f"ğŸ“Š *JETBOX Stats*\nPending Queue: {len(q)}\nServer Status: ONLINE")

def main():
    if TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("â- Telegram Bot Token missing! Please edit telegram_bot.py and add your token.")
        print("Steps:")
        print("1. Open Telegram and search for '@BotFather'")
        print("2. Send '/newbot' and name your bot (e.g., JetboxQueueBot)")
        print("3. Copy the HTTP API Token it gives you")
        print("4. Paste it into 'TOKEN' variable in telegram_bot.py")
        return

    print("ğŸ›¸ JETBOX Telegram Bot is Active...")
    print("Waiting for commands from your phone...")
    
    offset = None
    while True:
        updates = get_updates(offset)
        if updates.get("ok"):
            for item in updates["result"]:
                offset = item["update_id"] + 1
                if "message" in item:
                    handle_message(item["message"])
        time.sleep(1)

if __name__ == '__main__':
    main()

