import os
import sqlite3
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, ConversationHandler

BOT_TOKEN = os.getenv("BOT_TOKEN") or "8124480552:AAHLPnKnH2_kuD58HI7SrhYrp3uEPdrrIcU"
ADMIN_IDS = [424589091]

SELECT_SPEC, SELECT_TYPE, ENTER_TITLE, WAIT_FILE = range(4)
ADD_COURSE_SPEC, ADD_COURSE_TITLE, ADD_COURSE_DATE, ADD_COURSE_LINK = range(4, 8)

logging.basicConfig(level=logging.INFO)

SPECIALTIES = [
    {"code": "anatomy", "ar": "التشريح", "en": "Anatomy", "emoji": "🦴"},
    {"code": "biochem", "ar": "الكيمياء الحيوية", "en": "Biochemistry", "emoji": "🧬"},
    {"code": "physio", "ar": "وظائف الأعضاء", "en": "Physiology", "emoji": "❤️"},
    {"code": "histo", "ar": "الأنسجة", "en": "Histology", "emoji": "🔬"},
    {"code": "embryo", "ar": "الأجنة", "en": "Embryology", "emoji": "👶"},
    {"code": "patho", "ar": "علم الأمراض", "en": "Pathology", "emoji": "🦠"},
    {"code": "pharma", "ar": "الأدوية", "en": "Pharmacology", "emoji": "💊"},
    {"code": "micro", "ar": "الأحياء الدقيقة", "en": "Microbiology", "emoji": "🧫"},
    {"code": "para", "ar": "الطفيليات", "en": "Parasitology", "emoji": "🪱"},
    {"code": "immuno", "ar": "المناعة", "en": "Immunology", "emoji": "🛡️"},
    {"code": "internal", "ar": "الباطنة", "en": "Internal Medicine", "emoji": "🩺"},
    {"code": "surgery", "ar": "الجراحة", "en": "Surgery", "emoji": "🔪"},
    {"code": "peds", "ar": "الأطفال", "en": "Pediatrics", "emoji": "🧒"},
    {"code": "gyn", "ar": "النسائية والتوليد", "en": "Gynecology", "emoji": "🤰"},
    {"code": "ophtha", "ar": "العيون", "en": "Ophthalmology", "emoji": "👁️"},
    {"code": "ent", "ar": "الأنف والأذن والحنجرة", "en": "ENT", "emoji": "👂"},
    {"code": "derma", "ar": "الجلدية", "en": "Dermatology", "emoji": "🧴"},
    {"code": "neuro", "ar": "الأعصاب", "en": "Neurology", "emoji": "🧠"},
    {"code": "psych", "ar": "النفسية", "en": "Psychiatry", "emoji": "💭"},
    {"code": "ortho", "ar": "العظام", "en": "Orthopedics", "emoji": "🦿"},
    {"code": "radio", "ar": "الأشعة", "en": "Radiology", "emoji": "☢️"},
    {"code": "anesth", "ar": "التخدير", "en": "Anesthesia", "emoji": "💉"},
    {"code": "emergency", "ar": "الطوارئ", "en": "Emergency", "emoji": "🚨"},
    {"code": "family", "ar": "طب الأسرة", "en": "Family Medicine", "emoji": "👨‍👩‍👧‍👦"},
]

MATERIAL_TYPES = {
    "summary": "📄 ملخصات",
    "book": "📕 كتب ومراجع",
    "plan": "🗺️ خطط دراسية",
    "questions": "❓ بنك أسئلة",
    "video": "🎥 فيديوهات"
}

def init_db():
    conn = sqlite3.connect("medical_bot.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS specialties (code TEXT PRIMARY KEY, ar_name TEXT, en_name TEXT, emoji TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS materials (id INTEGER PRIMARY KEY AUTOINCREMENT, specialty_code TEXT, type TEXT, title TEXT, file_id TEXT, file_type TEXT, description TEXT, added_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY AUTOINCREMENT, specialty_code TEXT, title TEXT, date TEXT, link TEXT, description TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, joined_at TEXT)""")
    for s in SPECIALTIES:
        c.execute("INSERT OR IGNORE INTO specialties VALUES (?,?,?,?)", (s["code"], s["ar"], s["en"], s["emoji"]))
    conn.commit()
    conn.close()

def is_admin(user_id):
    return user_id in ADMIN_IDS

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 التخصصات الطبية A-Z", callback_data="list_specialties")],
        [InlineKeyboardButton("🗓️ مواعيد الدورات", callback_data="list_courses"), InlineKeyboardButton("🔍 بحث سريع", callback_data="search_info")],
        [InlineKeyboardButton("⭐ مفضلتي", callback_data="favorites"), InlineKeyboardButton("📊 خطتي الدراسية", callback_data="my_plan")],
        [InlineKeyboardButton("ℹ️ عن البوت", callback_data="about")]
    ])

def specialties_keyboard():
    buttons = []
    row = []
    for s in SPECIALTIES:
        row.append(InlineKeyboardButton(f"{s['emoji']} {s['ar']}", callback_data=f"spec_{s['code']}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

def specialty_content_keyboard(spec_code):
    buttons = []
    for t_code, t_name in MATERIAL_TYPES.items():
        buttons.append([InlineKeyboardButton(t_name, callback_data=f"mat_{spec_code}_{t_code}")])
    buttons.append([InlineKeyboardButton("🗓️ دورات هذا التخصص", callback_data=f"courses_{spec_code}")])
    buttons.append([InlineKeyboardButton("⬅️ رجوع للتخصصات", callback_data="list_specialties")])
    return InlineKeyboardMarkup(buttons)

def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 رفع ملف جديد", callback_data="admin_upload")],
        [InlineKeyboardButton("🗓️ إضافة دورة", callback_data="admin_add_course")],
        [InlineKeyboardButton("📊 إحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton("🗑️ حذف ملف", callback_data="admin_delete_info")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = sqlite3.connect("medical_bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", (user.id, user.username, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    text = f"أهلاً دكتور {user.first_name} 🩺👋\n\nمرحباً بك في **المساعد الطبي الشامل**\n\nمكتبتك الطبية الكاملة من A to Z:\n• 24 تخصص طبي\n• ملخصات وكتب وخطط\n• بنك أسئلة وفيديوهات\n• مواعيد دورات وأنشطة\n\n⚠️ *تنبيه: هذا البوت تعليمي فقط*\n\nاختر من القائمة:"
    await update.message.reply_text(text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "main_menu":
        await query.edit_message_text("القائمة الرئيسية 🩺", reply_markup=main_menu_keyboard())
    elif data == "list_specialties":
        await query.edit_message_text("📚 اختر التخصص:", reply_markup=specialties_keyboard())
    elif data.startswith("spec_"):
        spec_code = data.split("_")[1]
        spec = next((s for s in SPECIALTIES if s["code"] == spec_code), None)
        if not spec:
            await query.edit_message_text("تخصص غير موجود", reply_markup=specialties_keyboard())
            return
        await query.edit_message_text(f"{spec['emoji']} **{spec['ar']} - {spec['en']}**\n\nاختر نوع المادة:", reply_markup=specialty_content_keyboard(spec_code), parse_mode="Markdown")
    elif data.startswith("mat_"):
        _, spec_code, type_code = data.split("_")
        conn = sqlite3.connect("medical_bot.db")
        c = conn.cursor()
        c.execute("SELECT id, title FROM materials WHERE specialty_code=? AND type=? ORDER BY id DESC LIMIT 20", (spec_code, type_code))
        rows = c.fetchall()
        conn.close()
        if not rows:
            await query.edit_message_text("لا يوجد ملفات في هذا القسم حالياً.\nاستخدم /admin لرفع ملفات.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data=f"spec_{spec_code}")]]))
            return
        buttons = []
        for mid, title in rows:
            buttons.append([InlineKeyboardButton(title[:50], callback_data=f"file_{mid}")])
        buttons.append([InlineKeyboardButton("⬅️ رجوع", callback_data=f"spec_{spec_code}")])
        await query.edit_message_text(f"📂 ملفات {type_code}:", reply_markup=InlineKeyboardMarkup(buttons))
    elif data.startswith("file_"):
        fid = int(data.split("_")[1])
        conn = sqlite3.connect("medical_bot.db")
        c = conn.cursor()
        c.execute("SELECT title, file_id, file_type FROM materials WHERE id=?", (fid,))
        row = c.fetchone()
        conn.close()
        if not row:
            await query.edit_message_text("الملف غير موجود")
            return
        title, file_id, ftype = row
        try:
            if ftype == "photo":
                await context.bot.send_photo(chat_id=query.message.chat_id, photo=file_id, caption=title)
            elif ftype == "video":
                await context.bot.send_video(chat_id=query.message.chat_id, video=file_id, caption=title)
            else:
                await context.bot.send_document(chat_id=query.message.chat_id, document=file_id, caption=title)
        except Exception as e:
            await query.message.reply_text(f"خطأ في إرسال الملف: {e}")
    elif data == "about":
        await query.edit_message_text("🤖 **بوت Future Medical Hub**\n\nمطور لطلاب الطب - 24 تخصص\nللدعم: @s_er6j\n\n⚠️ تعليمي فقط", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")]]), parse_mode="Markdown")
    elif data == "search_info":
        await query.edit_message_text("🔍 اكتب اسم المادة اللي بتدور عليها في الشات مباشرة (مثلاً: اناتومي) و راح أبحث لك.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")]]))
    elif data == "list_courses":
        conn = sqlite3.connect("medical_bot.db")
        c = conn.cursor()
        c.execute("SELECT title, date, link FROM courses ORDER BY date DESC LIMIT 10")
        courses = c.fetchall()
        conn.close()
        if not courses:
            txt = "لا يوجد دورات حالياً. تابعنا!"
        else:
            txt = "🗓️ **أقرب الدورات:**\n\n"
            for title, date, link in courses:
                txt += f"• {title} - {date}\n{link}\n\n"
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu")]]), parse_mode="Markdown")

async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text.startswith("/"):
        return
    conn = sqlite3.connect("medical_bot.db")
    c = conn.cursor()
    c.execute("SELECT id, title, specialty_code, type FROM materials WHERE title LIKE ? LIMIT 15", (f"%{text}%",))
    results = c.fetchall()
    conn.close()
    if not results:
        await update.message.reply_text("🔍 ما لقيت نتائج. جرب كلمة ثانية أو ادخل التخصصات.")
        return
    buttons = []
    for mid, title, spec, typ in results:
        buttons.append([InlineKeyboardButton(f"{title} ({spec})", callback_data=f"file_{mid}")])
    await update.message.reply_text(f"🔍 نتائج البحث عن '{text}':", reply_markup=InlineKeyboardMarkup(buttons))

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ هذا الأمر للأدمن فقط.")
        return
    await update.message.reply_text("🔧 **لوحة تحكم الأدمن**", reply_markup=admin_keyboard(), parse_mode="Markdown")

async def admin_upload_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    buttons = []
    row = []
    for s in SPECIALTIES:
        row.append(InlineKeyboardButton(s["ar"], callback_data=f"up_spec_{s['code']}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    await query.edit_message_text("1️⃣ اختر التخصص للملف:", reply_markup=InlineKeyboardMarkup(buttons))
    return SELECT_SPEC

async def admin_upload_spec_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    spec_code = query.data.split("_")[2]
    context.user_data["upload_spec"] = spec_code
    buttons = []
    for t_code, t_name in MATERIAL_TYPES.items():
        buttons.append([InlineKeyboardButton(t_name, callback_data=f"up_type_{t_code}")])
    await query.edit_message_text("2️⃣ اختر نوع الملف:", reply_markup=InlineKeyboardMarkup(buttons))
    return SELECT_TYPE

async def admin_upload_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    type_code = query.data.split("_")[2]
    context.user_data["upload_type"] = type_code
    await query.edit_message_text("3️⃣ أرسل الآن عنوان الملف:\nمثال: ملخص اناتومي شابتر 1 - د. أحمد")
    return ENTER_TITLE

async def admin_upload_title_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["upload_title"] = update.message.text
    await update.message.reply_text("4️⃣ ممتاز، الآن أرسل الملف نفسه (PDF / صورة / فيديو):")
    return WAIT_FILE

async def admin_upload_file_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    spec = context.user_data["upload_spec"]
    typ = context.user_data["upload_type"]
    title = context.user_data["upload_title"]
    file_id = None
    file_type = "document"
    if update.message.document:
        file_id = update.message.document.file_id
        file_type = "document"
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id
        file_type = "photo"
    elif update.message.video:
        file_id = update.message.video.file_id
        file_type = "video"
    if not file_id:
        await update.message.reply_text("أرسل ملف صحيح PDF أو صورة أو فيديو")
        return WAIT_FILE
    conn = sqlite3.connect("medical_bot.db")
    c = conn.cursor()
    c.execute("INSERT INTO materials (specialty_code, type, title, file_id, file_type, description, added_at) VALUES (?,?,?,?,?,?,?)",
              (spec, typ, title, file_id, file_type, f"تمت الإضافة بواسطة الأدمن", datetime.now().isoformat()))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ تم حفظ الملف بنجاح!\n\n📚 {title}\nفي {spec} - {typ}\n\nالطلاب الآن يقدرون يحملوه.")
    return ConversationHandler.END

async def cancel_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم إلغاء الرفع.")
    return ConversationHandler.END

def keep_alive():
    try:
        from flask import Flask
        from threading import Thread
        port = int(os.getenv("PORT", 10000))
        app_flask = Flask(__name__)
        @app_flask.route('/')
        def home(): return "Bot is alive - Medical Bot Working"
        @app_flask.route('/health')
        def health(): return "OK"
        Thread(target=lambda: app_flask.run(host='0.0.0.0', port=port), daemon=True).start()
        print(f"Keep alive server on port {port}")
    except Exception as e:
        print(f"Keep alive error: {e}")

def main():
    init_db()
    keep_alive()
    if BOT_TOKEN == "ضع_التوكن_هنا" or len(BOT_TOKEN) < 20:
        print("التوكن ناقص - البوت في وضع الانتظار")
        import time
        while True:
            time.sleep(60)
    app = Application.builder().token(BOT_TOKEN).build()
    upload_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_upload_start, pattern="^admin_upload$")],
        states={
            SELECT_SPEC: [CallbackQueryHandler(admin_upload_spec_selected, pattern="^up_spec_")],
            SELECT_TYPE: [CallbackQueryHandler(admin_upload_type_selected, pattern="^up_type_")],
            ENTER_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_upload_title_received)],
            WAIT_FILE: [MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, admin_upload_file_received)]
        },
        fallbacks=[CommandHandler("cancel", cancel_upload)],
        per_message=False
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(upload_conv)
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(main_menu|list_specialties|spec_|mat_|file_|about|search_info|list_courses|courses_)"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler))
    print("البوت شغال...")
    app.run_polling()

if __name__ == "__main__":
    main()
