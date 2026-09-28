import os
import asyncio
from flask import Flask
from threading import Thread

# === Fix event loop for Python 3.12 on Render ===
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# === 1. افتح البورت فوراً ===
app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "Bot is alive - Step 1 OK", 200
@app_flask.route('/health')
def health(): return "OK", 200

def keep_alive():
    port = int(os.getenv("PORT", 10000))
    Thread(target=lambda: app_flask.run(host='0.0.0.0', port=port, debug=False, use_reloader=False), daemon=True).start()
    print(f"==> Keep alive on {port}", flush=True)

keep_alive()

# === 2. البوت - نسخة مصغرة ===
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN") or "8124480552:AAHLPnKnH2_kuD58HI7SrhYrp3uEPdrrIcU"
ADMIN_IDS = [424589091]

print(f"BOT_TOKEN len: {len(BOT_TOKEN)}", flush=True)

def is_admin(uid): return uid in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔧 لوحة التحكم", callback_data="go_admin")],
        [InlineKeyboardButton("ℹ️ عن البوت", callback_data="about")]
    ])
    await update.message.reply_text(
        f"أهلاً {update.effective_user.first_name} 👋\n\n"
        f"هذه نسخة تجريبية - خطوة 1\n"
        f"البوت شغال تمام ✅\n\n"
        f"جرب /admin",
        reply_markup=kb
    )

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(f"❌ مش أدمن\nID: {update.effective_user.id}")
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 احصائيات", callback_data="stats")],
        [InlineKeyboardButton("✅ اختبار الرفع", callback_data="test_upload")]
    ])
    await update.message.reply_text("🔧 لوحة تحكم الأدمن - خطوة 1\n\nالبوت شغال 100% ✅", reply_markup=kb)

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "go_admin":
        if not is_admin(q.from_user.id):
            await q.edit_message_text(f"❌ مش أدمن\nID: {q.from_user.id}")
            return
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 احصائيات", callback_data="stats")],
            [InlineKeyboardButton("✅ اختبار", callback_data="test_upload")]
        ])
        await q.edit_message_text("🔧 لوحة التحكم - شغالة!", reply_markup=kb)
    elif q.data == "stats":
        await q.edit_message_text(f"📊 احصائيات:\n• البوت: شغال ✅\n• الأدمن: {q.from_user.id}\n\nالخطوة 1 نجحت!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="go_admin")]]))
    elif q.data == "test_upload":
        await q.edit_message_text("✅ الأزرار شغالة!\n\nالخطوة الجاية بنضيف رفع ملفات.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="go_admin")]]))
    elif q.data == "about":
        await q.edit_message_text("🩺 بوت طبي - خطوة 1", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="main")]]))
    elif q.data == "main":
        await q.edit_message_text("القائمة", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔧 لوحة التحكم", callback_data="go_admin")]]))

def main():
    print("🚀 Starting minimal bot - Step 1 FIXED", flush=True)
    # Create loop explicitly
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CallbackQueryHandler(buttons))
    print("🚀 Bot polling started - waiting for /start", flush=True)
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
