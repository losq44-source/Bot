import os
from flask import Flask
from threading import Thread

# افتح البورت فوراً عشان Render ما يعطي خطأ
app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "OK", 200

def keep_alive():
    port = int(os.getenv("PORT", 10000))
    Thread(target=lambda: app_flask.run(host='0.0.0.0', port=port, debug=False, use_reloader=False), daemon=True).start()

keep_alive()

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN") or "8124480552:AAHLPnKnH2_kuD58HI7SrhYrp3uEPdrrIcU"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبا")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Bot started - waiting for /start")
    app.run_polling()

if __name__ == "__main__":
    main()
