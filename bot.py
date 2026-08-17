import os
import threading
import time
import sqlite3
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
    return "Nexus Store Grand Master Engine is Online!"

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
CHANNEL_ID = os.getenv("CHANNEL_ID", "https://t.me/+o4GawlAie10wNGI0")
YOUR_USERNAME = os.getenv("YOUR_USERNAME", "@Nexus_Support_v1_Bot")

# 💳 بيانات الدفع الحقيقية المحدثة
BANKAK_ACCOUNT = "9412190"
BANKAK_NAME = "يوسف إبراهيم الطيب عبد القادر"
BINANCE_PAY_ID = "1054497732"
BINANCE_WALLET_ADDRESS = "0x6742c39cb07b9fd6a69281dc4b9b96239cc7850a"

genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")

pending_orders = {}
admin_states = {}
user_states = {}

# ==========================================
# 🗄️ قاعدة البيانات المتقدمة
# ==========================================
def init_db():
    conn = sqlite3.connect('nexus_store.db')
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
            name TEXT,
            price TEXT,
            link TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            status TEXT DEFAULT 'OPEN'
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO products (name, price, link) VALUES ('🎬 حزمة المونتاج الشاملة', '10,000 SDG / $5', 'https://mixkit.co/')")
        cursor.execute("INSERT INTO products (name, price, link) VALUES ('📝 منشئ الـ CV الذكي', '6,000 SDG / $3', 'https://rxresu.me/')")

    conn.commit()
    conn.close()

def add_user(user_id, ref_id=0):
    conn = sqlite3.connect('nexus_store.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, ref_id))
    if ref_id and ref_id != user_id:
        cursor.execute("UPDATE users SET discount_points = discount_points + 10 WHERE user_id = ?", (ref_id,))
    conn.commit()
    conn.close()

def get_products():
    conn = sqlite3.connect('nexus_store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, link FROM products")
    items = cursor.fetchall()
    conn.close()
    return items

def add_product(name, price, link):
    conn = sqlite3.connect('nexus_store.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (name, price, link) VALUES (?, ?, ?)", (name, price, link))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('nexus_store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

init_db()

# ==========================================
# 🤖 فحص الإشعار بالـ AI بعد 3 دقائق
# ==========================================
def verify_receipt_with_ai(image_path):
    try:
        sample_file = genai.upload_file(path=image_path)
        prompt = (
            "Examine this transfer receipt strictly. "
            "Verify amount, currency (SDG or USD), date, and authenticity. "
            "Respond ONLY with 'APPROVED' if genuine or 'REJECTED' if fake."
        )
        response = ai_model.generate_content([sample_file, prompt])
        return "APPROVED" if "APPROVED" in response.text.strip().upper() else "REJECTED"
    except Exception:
        return "REJECTED"

def auto_process_receipt(order_id, user_id, photo_path, admin_msg_id, item_name, deliver_link):
    time.sleep(180)
    
    if order_id in pending_orders and pending_orders[order_id]['status'] == 'WAITING':
        pending_orders[order_id]['status'] = 'PROCESSING'
        verdict = verify_receipt_with_ai(photo_path)
        
        if verdict == "APPROVED":
            bot.send_message(user_id, f"🎉 <b>تم الفحص والتحقق آلياً!</b>\n\n📦 <b>رابط استلام ({item_name}):</b>\n{deliver_link}")
            bot.edit_message_caption(f"🤖 <b>تم القبول والتسليم أوتوماتيكياً عبر الذكاء الاصطناعي</b>\n🆔 العميل: <code>{user_id}</code>", ADMIN_ID, admin_msg_id)
        else:
            bot.send_message(user_id, f"❌ <b>تعذر التأكد من صحة الإشعار آلياً.</b>\nتواصل مع الدعم: {YOUR_USERNAME}")
            bot.edit_message_caption(f"🔴 <b>تم الرفض أوتوماتيكياً بواسطة الذكاء الاصطناعي (مستند غير واضح)</b>\n🆔 العميل: <code>{user_id}</code>", ADMIN_ID, admin_msg_id)

        if os.path.exists(photo_path):
            os.remove(photo_path)
        del pending_orders[order_id]

# ==========================================
# 🚀 التفاعل القوائم الرئيسية
# ==========================================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.chat.id
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
    
    add_user(user_id, ref_id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📦 المنتجات والخدمات", callback_data="show_catalog"),
        types.InlineKeyboardButton("💳 طرق الدفع (بنكك/دولار)", callback_data="show_payment")
    )
    markup.add(
        types.InlineKeyboardButton("🎁 نقاط الخصم والإحالة", callback_data="show_referral"),
        types.InlineKeyboardButton("📩 تقديم شكوى / استفسار", callback_data="open_ticket")
    )
    
    if user_id == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("👑 لوحة التحكم الإدارية", callback_data="admin_panel"))
        
    bot.send_message(user_id, f"أهلاً بك يا <b>{message.from_user.first_name}</b> في متجر Nexus Store المتكامل! 🌟", reply_markup=markup)

# ==========================================
# 📥 التعامل مع رسائل الشكاوى وإعدادات المالك
# ==========================================
@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id) == "WAITING_TICKET")
def handle_user_ticket(message):
    user_id = message.chat.id
    user_states[user_id] = None
    
    bot.send_message(user_id, "✅ <b>تم إرسال شكواك/استفسارك للمالك بنجاح!</b> سيتم الرد عليك فوراً عبر البوت.")
    
    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.add(types.InlineKeyboardButton("💬 الرد على الشكوى", callback_data=f"reply_ticket_{user_id}"))
    
    msg_to_admin = f"⚠️ <b>شكوى / استفسار جديد من زبون:</b>\n🆔 ID: <code>{user_id}</code>\n👤 الاسم: {message.from_user.first_name}\n\n💬 الرسالة:\n<i>{message.text}</i>"
    bot.send_message(ADMIN_ID, msg_to_admin, reply_markup=admin_markup)

@bot.message_handler(func=lambda msg: msg.chat.id == ADMIN_ID and admin_states.get(ADMIN_ID) is not None)
def handle_admin_inputs(message):
    state = admin_states.get(ADMIN_ID)
    
    if state == "WAITING_BROADCAST":
        admin_states[ADMIN_ID] = None
        users = get_all_users()
        sent = 0
        for u_id in users:
            try:
                bot.copy_message(u_id, ADMIN_ID, message.message_id)
                sent += 1
                time.sleep(0.04)
            except Exception:
                pass
        bot.send_message(ADMIN_ID, f"✅ تم إرسال الإذاعة بنجاح إلى <code>{sent}</code> مستخدم.")

    elif state == "WAITING_ADD_PRODUCT":
        admin_states[ADMIN_ID] = None
        try:
            p_name, p_price, p_link = message.text.split('|')
            add_product(p_name.strip(), p_price.strip(), p_link.strip())
            bot.send_message(ADMIN_ID, f"✅ تم إضافة المنتج <b>{p_name.strip()}</b> بنجاح!")
        except Exception:
            bot.send_message(ADMIN_ID, "❌ صيغة خاطئة. أرسل البيانات هكذا:\n<code>اسم المنتج | السعر | رابط التسليم</code>")

    elif state.startswith("REPLYING_TO_"):
        target_user_id = int(state.replace("REPLYING_TO_", ""))
        admin_states[ADMIN_ID] = None
        bot.send_message(target_user_id, f"📩 <b>رد من إدارة المتجر:</b>\n\n{message.text}")
        bot.send_message(ADMIN_ID, f"✅ تم إرسال الرد إلى الزبون <code>{target_user_id}</code> بنجاح.")

# ==========================================
# 📥 استقبال صور الإشعارات
# ==========================================
@bot.message_handler(content_types=['photo'])
def handle_payment_proof(message):
    user_id = message.chat.id
    photo_id = message.photo[-1].file_id
    order_id = f"{user_id}_{message.message_id}"

    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)
    photo_path = f"receipt_{order_id}.jpg"
    
    with open(photo_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    item_name = "الخدمة الرقمية"
    deliver_link = "https://mixkit.co/"

    bot.send_message(user_id, "✅ <b>تم استلام الإشعار بنجاح!</b>\nسيتم التحقق آلياً وتسليم طلبك خلال 3 دقائق.")

    admin_markup = types.InlineKeyboardMarkup(row_width=1)
    admin_markup.add(
        types.InlineKeyboardButton("🟢 تأكيد الدفع فوراً", callback_data=f"approve_{order_id}"),
        types.InlineKeyboardButton("🔴 رفض الطلب فوراً", callback_data=f"reject_{order_id}")
    )
    admin_msg = f"📥 <b>إشعار دفع جديد!</b>\n🆔 <b>ID:</b> <code>{user_id}</code>\n⏳ <i>ينتظر الفحص اليدوي أو الآلي بالـ AI بعد 3 دقائق...</i>"
    sent_msg = bot.send_photo(ADMIN_ID, photo_id, caption=admin_msg, reply_markup=admin_markup)

    pending_orders[order_id] = {
        "status": "WAITING",
        "user_id": user_id,
        "item_name": item_name,
        "deliver": deliver_link,
        "photo_path": photo_path
    }

    t = threading.Thread(target=auto_process_receipt, args=(order_id, user_id, photo_path, sent_msg.message_id, item_name, deliver_link))
    t.daemon = True
    t.start()

# ==========================================
# 🔘 معالجة الضغط على الأزرار
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    data = call.data
    user_id = call.message.chat.id

    if data == "admin_panel" and user_id == ADMIN_ID:
        users_count = len(get_all_users())
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("📢 إرسال إذاعة جماعية (Broadcast)", callback_data="start_broadcast"),
            types.InlineKeyboardButton("➕ إضافة منتج جديد للمتجر", callback_data="trigger_add_product")
        )
        msg = f"👑 <b>لوحة تحكم المالك:</b>\n\n👥 <b>عدد العملاء:</b> <code>{users_count}</code>\n⚡ اختر الإجراء المطلوب:"
        bot.send_message(user_id, msg, reply_markup=markup)

    elif data == "start_broadcast" and user_id == ADMIN_ID:
        admin_states[ADMIN_ID] = "WAITING_BROADCAST"
        bot.send_message(user_id, "📢 أرسل الرسالة الآن لنشرها لكافة المستخدمين:")

    elif data == "trigger_add_product" and user_id == ADMIN_ID:
        admin_states[ADMIN_ID] = "WAITING_ADD_PRODUCT"
        bot.send_message(user_id, "📝 أرسل بيانات المنتج بالصيغة الآتية:\n<code>اسم المنتج | السعر | رابط التسليم</code>")

    elif data.startswith("reply_ticket_") and user_id == ADMIN_ID:
        target_id = data.replace("reply_ticket_", "")
        admin_states[ADMIN_ID] = f"REPLYING_TO_{target_id}"
        bot.send_message(user_id, f"💬 أرسل الرد المباشر الذي تريد توجيهه للزبون <code>{target_id}</code>:")

    elif data == "open_ticket":
        user_states[user_id] = "WAITING_TICKET"
        bot.send_message(user_id, "📩 <b>يرجى كتابة تفاصيل الشكوى أو الاستفسار في رسالة واحدة الآن:</b>")

    elif data == "show_catalog":
        products = get_products()
        msg = "📦 <b>قائمة المنتجات المتاحة:</b>\n\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for p in products:
            msg += f"• <b>{p[1]}</b> - السعر: <code>{p[2]}</code>\n"
            markup.add(types.InlineKeyboardButton(f"🛒 شراء {p[1]}", callback_data=f"buy_info_{p[0]}"))
        bot.send_message(user_id, msg, reply_markup=markup)

    elif data.startswith("buy_info_"):
        bot.send_message(user_id, "💳 للشراء: قم بالتحويل لأحد الحسابات المتاحة في خيار (طرق الدفع)، ثم أرسل صورة إشعار التحويل هنا مباشرة.")

    elif data == "show_payment":
        payment_info = (
            "💳 <b>طرق الدفع المتاحة للتحويل:</b>\n\n"
            "🇸🇩 <b>بالجنيه السوداني (تطبيق بنكك):</b>\n"
            f"• رقم الحساب: <code>{BANKAK_ACCOUNT}</code>\n"
            f"• باسم: <b>{BANKAK_NAME}</b>\n\n"
            "💵 <b>بالدولار (Binance Pay / Crypto):</b>\n"
            f"• Binance ID: <code>{BINANCE_PAY_ID}</code>\n"
            f"• Web3 Wallet: <code>{BINANCE_WALLET_ADDRESS}</code>\n\n"
            "📌 <i>بعد إتمام التحويل، أرسل صورة إشعار التحويل في المحادثة مباشرة لتأكيد التسليم التلقائي!</i>"
        )
        bot.send_message(user_id, payment_info)

    elif data.startswith("approve_"):
        order_id = data.replace("approve_", "")
        if order_id in pending_orders:
            order = pending_orders[order_id]
            order['status'] = 'MANUAL'
            bot.send_message(order['user_id'], f"🎉 <b>تم تأكيد الدفع وتسليم الخدمة:</b>\n{order['deliver']}")
            bot.edit_message_caption(f"✅ <b>تم التأكيد يدوياً بواسطة المالك</b>", ADMIN_ID, call.message.message_id)
            if os.path.exists(order['photo_path']): os.remove(order['photo_path'])
            del pending_orders[order_id]

    elif data.startswith("reject_"):
        order_id = data.replace("reject_", "")
        if order_id in pending_orders:
            order = pending_orders[order_id]
            order['status'] = 'MANUAL'
            bot.send_message(order['user_id'], f"❌ <b>تعذر التأكد من التحويل.</b> تواصل مع الدعم: {YOUR_USERNAME}")
            bot.edit_message_caption(f"🔴 <b>تم الرفض يدوياً بواسطة المالك</b>", ADMIN_ID, call.message.message_id)
            if os.path.exists(order['photo_path']): os.remove(order['photo_path'])
            del pending_orders[order_id]
@bot.message_handler(commands=['post'])
def post_to_channel(message):
    if message.from_user.id == ADMIN_ID:
        text = message.text.replace('/post', '').strip()
        if not text:
            bot.reply_to(message, "❌ يرجى كتابة النص بعد الأمر.\nمثال:\n`/post مرحباً بكم في المتجر!`", parse_mode="Markdown")
            return
        try:
            bot.send_message(CHANNEL_ID, text)
            bot.reply_to(message, "✅ تم النشر في القناة بنجاح!")
        except Exception as e:
            bot.reply_to(message, f"❌ حدث خطأ أثناء النشر:\n`{e}`", parse_mode="Markdown")

if __name__ == "__main__":
    keep_alive()
    print("🚀 Nexus Store Grand Master Engine Running...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

