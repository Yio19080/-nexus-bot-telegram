import os
import threading
import time
import sqlite3
import datetime
import telebot
from telebot import types
from flask import Flask
import google.generativeai as genai

# ==========================================
# 🌐 سيرفر الحفاظ على التشغيل 24/7
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Nexus Store Engine is Fully Online & Complete!"

def keep_alive():
    t = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080))
    t.daemon = True
    t.start()

# ==========================================
# 🔑 الإعدادات والمفاتيح الرسمية
# ==========================================
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN", "8617844634:AAGfD4f-dpgmpPn2Zo0ZPdaGq09Vvm7cL18")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "ضع_مفتاح_GEMINI_هنا")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7899998427"))

BANKAK_ACCOUNT = "9412190"
BANKAK_NAME = "يوسف إبراهيم الطيب عبد القادر"
BINANCE_PAY_ID = "943209825"
BINANCE_WALLET_ADDRESS = "0x6742c39cb07b9fd6a69281dc4b9b96239cc7850a"

genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-3.6-flash')

bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML", threaded=True, num_threads=10)

admin_states = {}
user_states = {}
handled_receipts = set()
last_generated_ad = {} # لحفظ آخر إعلان تم توليده

# ==========================================
# 🗄️ قاعدة البيانات
# ==========================================
def init_db():
    conn = sqlite3.connect('nexus_store.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            referred_by INTEGER DEFAULT 0,
            discount_points INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            price_usd REAL,
            price_sdg REAL,
            link TEXT DEFAULT 'https://t.me/NexusStoreAr',
            video_url TEXT DEFAULT 'https://youtube.com',
            description TEXT DEFAULT ''
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect('nexus_store.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('nexus_store.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

init_db()

# ==========================================
# 🎨 مولد الإعلانات والتصاميم المجاني 100%
# ==========================================
def generate_free_ad(topic):
    prompt_text = f"اكتب نص إعلاني ترويجي جذاب جداً وقصير ومناسب للتليجرام عن: {topic}. استخدم الإيموجي والوسوم المناسبة."
    ad_text = ai_model.generate_content(prompt_text).text

    prompt_img_desc = f"Give me a 3-word English search query for an advertising image related to: {topic}."
    img_keyword = ai_model.generate_content(prompt_img_desc).text.strip().replace(" ", "%20")

    image_url = f"https://image.pollinations.ai/prompt/professional%20advertising%20banner%20for%20{img_keyword}?width=800&height=500&nologo=true"
    return ad_text, image_url

# ==========================================
# 🧠 دالة الفحص الآلي للإشعار
# ==========================================
def ai_verify_receipt(receipt_info, image_path=None):
    current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    prompt = f"""
    أنت نظام أمان وفحص آلي لإشعارات التحويل البنكي (مثل تطبيق بنكك - بنك الخرطوم).
    تاريخ ووقت النظام الحالي هو: {current_time_str}

    المطلوب منك فحص الإشعار والتحقق الصارم من الشروط التالية:
    1. **مطابقة الاسم:** يجب أن يكون اسم المرسل إليه هو "يوسف ابراهيم الطيب عبدالقادر".
    2. **مطابقة رقم الحساب:** يجب أن يحتوي الإشعار على رقم الحساب "9412190".
    3. **فحص التاريخ والوقت:** يجب أن يكون تاريخ العملية حديثاً وقريباً جداً من وقت النظام الحالي ({current_time_str}).

    إذا تحققت الشروط، ابدأ بـ: 'APPROVED'.
    إذا اختل أي شرط، ابدأ بـ: 'REJECTED' واذكر السبب بالتفصيل.
    """

    try:
        if image_path and os.path.exists(image_path):
            import PIL.Image
            img = PIL.Image.open(image_path)
            response = ai_model.generate_content([prompt, img, receipt_info]).text.strip()
        else:
            response = ai_model.generate_content(f"{prompt}\n\nبيانات الإشعار النصية:\n{receipt_info}").text.strip()
        return response
    except Exception as e:
        return f"REJECTED\nتعذر فحص الإشعار آلياً: {e}"

def process_receipt_after_timeout(receipt_id, user_id, receipt_content, image_path=None):
    time.sleep(60)
    if receipt_id in handled_receipts:
        return

    handled_receipts.add(receipt_id)
    ai_result = ai_verify_receipt(receipt_content, image_path)
    
    if image_path and os.path.exists(image_path):
        try:
            os.remove(image_path)
        except Exception:
            pass

    if ai_result.startswith("APPROVED"):
        explanation = ai_result.replace("APPROVED", "").strip()
        bot.send_message(user_id, f"✅ <b>تم قبول الإشعار بنجاح!</b>\n\n🎯 الاسم ورقم الحساب والتاريخ متطابقة.\n📝 {explanation}")
        bot.send_message(ADMIN_ID, f"⚡ <b>قبول آلي لإشعار (عدم الرد خلال دقيقة):</b>\n👤 الزبون: <code>{user_id}</code>\n📝 {explanation}")
    else:
        explanation = ai_result.replace("REJECTED", "").strip()
        bot.send_message(user_id, f"❌ <b>تم رفض الإشعار تلقائياً!</b>\n\n⚠️ {explanation}")
        bot.send_message(ADMIN_ID, f"⚠️ <b>رفض آلي لإشعار غير مطابق:</b>\n👤 الزبون: <code>{user_id}</code>\n📝 {explanation}")

# ==========================================
# 🚀 القائمة الرئيسية
# ==========================================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.chat.id
    add_user(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💳 طرق الدفع", callback_data="show_payment")
    )
    
    if user_id == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("👑 لوحة التحكم والمستشار الإعلاني", callback_data="admin_panel"))
        
    bot.send_message(user_id, f"أهلاً بك يا <b>{message.from_user.first_name}</b>!", reply_markup=markup)

# ==========================================
# 🔘 تفاعلات لوحة المالك والإعلانات
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    data = call.data
    user_id = call.message.chat.id

    if data.startswith("appr_rcpt_") and user_id == ADMIN_ID:
        rcpt_id = data.replace("appr_rcpt_", "")
        handled_receipts.add(rcpt_id)
        target_user = int(rcpt_id.split("_")[0])
        bot.send_message(target_user, "✅ <b>تمت الموافقة على إشعار التحويل يدوياً بواسطة المالك!</b>")
        bot.edit_message_text(f"{call.message.text}\n\n✅ <b>تم القبول يدوياً.</b>", chat_id=ADMIN_ID, message_id=call.message.message_id)

    elif data.startswith("reje_rcpt_") and user_id == ADMIN_ID:
        rcpt_id = data.replace("reje_rcpt_", "")
        handled_receipts.add(rcpt_id)
        target_user = int(rcpt_id.split("_")[0])
        bot.send_message(target_user, "❌ <b>عذراً، تم رفض إشعار التحويل من قبل المالك.</b>")
        bot.edit_message_text(f"{call.message.text}\n\n❌ <b>تم الرفض يدوياً.</b>", chat_id=ADMIN_ID, message_id=call.message.message_id)

    elif data == "admin_panel" and user_id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("📢 صانع الإعلانات والصور الفورية", callback_data="create_instant_ad"),
            types.InlineKeyboardButton("💡 اقتراح أفكار إعلانية", callback_data="get_ad_ideas")
        )
        msg = "👑 <b>لوحة المالك والإنتاج الإعلاني:</b>\nاختر الخدمة المطلوبة:"
        bot.send_message(user_id, msg, reply_markup=markup)

    elif data == "create_instant_ad" and user_id == ADMIN_ID:
        admin_states[ADMIN_ID] = "WAITING_AD_TOPIC"
        bot.send_message(user_id, "🎯 أرسل موضوع الإعلان والمطلوب فوراً:")

    elif data == "get_ad_ideas" and user_id == ADMIN_ID:
        bot.send_chat_action(user_id, 'typing')
        try:
            ideas = ai_model.generate_content("اقترح 3 أفكار حملات إعلانية لمتجر تلجرام.").text
            bot.send_message(user_id, f"💡 <b>أفكار إعلانية:</b>\n\n{ideas}")
        except Exception:
            bot.send_message(user_id, "⚠️ متعذر جلب الأفكار حالياً.")

    elif data == "broadcast_last_ad" and user_id == ADMIN_ID:
        if last_generated_ad.get("text") and last_generated_ad.get("image"):
            users = get_all_users()
            sent_count = 0
            for u_id in users:
                try:
                    bot.send_photo(u_id, last_generated_ad["image"], caption=last_generated_ad["text"])
                    sent_count += 1
                except Exception:
                    pass
            bot.send_message(ADMIN_ID, f"✅ <b>تم نشر الإعلان والصورة بنجاح لـ {sent_count} مستخدم!</b>")
        else:
            bot.send_message(ADMIN_ID, "⚠️ لا يوجد إعلان محفوظ للنشر.")

    elif data == "show_payment":
        payment_info = (
            f"🇸🇩 <b>بنكك:</b> <code>{BANKAK_ACCOUNT}</code> ({BANKAK_NAME})\n"
            f"💵 <b>Binance Pay ID:</b> <code>{BINANCE_PAY_ID}</code>\n\n"
            "📌 <i>أرسل نص أو صورة الإشعار هنا مباشرة!</i>"
        )
        bot.send_message(user_id, payment_info)

# ==========================================
# 🖼️ استقبال صور الإشعارات
# ==========================================
@bot.message_handler(content_types=['photo'])
def handle_photo_receipt(message):
    user_id = message.chat.id
    if user_id == ADMIN_ID:
        return

    rcpt_id = f"{user_id}_{message.message_id}"
    caption = message.caption if message.caption else "صورة إشعار تحويل مالي"

    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    temp_img_path = f"temp_rcpt_{rcpt_id}.jpg"
    with open(temp_img_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ موافقة", callback_data=f"appr_rcpt_{rcpt_id}"),
        types.InlineKeyboardButton("❌ رفض", callback_data=f"reje_rcpt_{rcpt_id}")
    )

    bot.send_photo(
        ADMIN_ID, 
        message.photo[-1].file_id, 
        caption=f"💳 <b>إشعار جديد (صورة):</b>\n👤 من: {user_id}\n📝 {caption}", 
        reply_markup=markup
    )
    
    bot.send_message(user_id, "⏳ <b>تم استلام صورة الإشعار!</b> جاري الفحص...")

    t = threading.Thread(target=process_receipt_after_timeout, args=(rcpt_id, user_id, f"صورة إشعار. نص: {caption}", temp_img_path))
    t.daemon = True
    t.start()

# ==========================================
# 📥 استقبال الرسائل النصية
# ==========================================
@bot.message_handler(func=lambda msg: True)
def handle_text_messages(message):
    user_id = message.chat.id
    text = message.text

    if user_id == ADMIN_ID and admin_states.get(ADMIN_ID) == "WAITING_AD_TOPIC":
        admin_states[ADMIN_ID] = None
        bot.send_message(ADMIN_ID, "🚀 <b>جاري تصميم الإعلان وتوليد الصورة...</b>")
        
        try:
            ad_text, img_url = generate_free_ad(text)
            last_generated_ad["text"] = ad_text
            last_generated_ad["image"] = img_url
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📢 نشر هذا الإعلان فوراً لجميع العملاء", callback_data="broadcast_last_ad"))
            
            bot.send_photo(ADMIN_ID, img_url, caption=f"🎯 <b>الإعلان الجاهز:</b>\n\n{ad_text}", reply_markup=markup)
        except Exception as e:
            bot.send_message(ADMIN_ID, f"⚠️ حدث خطأ: {e}")

    elif user_id != ADMIN_ID:
        rcpt_id = f"{user_id}_{message.message_id}"
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ موافقة", callback_data=f"appr_rcpt_{rcpt_id}"),
            types.InlineKeyboardButton("❌ رفض", callback_data=f"reje_rcpt_{rcpt_id}")
        )

        bot.send_message(
            ADMIN_ID, 
            f"🔔 <b>رسالة / إشعار جديد:</b>\n👤 من: <code>{user_id}</code>\n💬 <i>{text}</i>", 
            reply_markup=markup
        )
        
        bot.send_message(user_id, "⏳ <b>تم استلام الرسالة!</b> جاري الفحص الآلي...")

        t = threading.Thread(target=process_receipt_after_timeout, args=(rcpt_id, user_id, text, None))
        t.daemon = True
        t.start()

if __name__ == "__main__":
    keep_alive()
    print("🚀 Nexus Store Fully Online...")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            time.sleep(2)
