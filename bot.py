import os
import logging
from flask import Flask
from threading import Thread

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# === Render port fix ===
app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "Bot is running - send /start in Telegram", 200
@app_flask.route('/health')
def health(): return "OK", 200

def keep_alive():
    port = int(os.getenv("PORT", 10000))
    print(f"==> Opening port {port} for Render", flush=True)
    Thread(target=lambda: app_flask.run(host='0.0.0.0', port=port, debug=False, use_reloader=False), daemon=True).start()

keep_alive()

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN") or "8124480552:AAHLPnKnH2_kuD58HI7SrhYrp3uEPdrrIcU"

print(f"BOT_TOKEN exists: {len(BOT_TOKEN) > 20}", flush=True)
print(f"Token starts with: {BOT_TOKEN[:10]}...", flush=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Received /start from {update.effective_user.id}", flush=True)
    await update.message.reply_text("مرحبا")

async def error_handler(update, context):
    print(f"Error: {context.error}", flush=True)

def main():
    print("=== Building bot ===", flush=True)
    try:
        app = Application.builder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_error_handler(error_handler)
        print("=== Starting polling ===", flush=True)
        print("Go to Telegram and send /start", flush=True)
        app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
