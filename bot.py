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
CHANNEL_LINK = "https://t.me/NexusStoreAr"

BANKAK_ACCOUNT = "9412190"
BANKAK_NAME = "يوسف إبراهيم الطيب عبد القادر"
BINANCE_PAY_ID = "943209825"
BINANCE_WALLET_ADDRESS = "0x6742c39cb07b9fd6a69281dc4b9b96239cc7850a"

genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")

admin_states = {}
user_states = {}

# ==========================================
# 🗄️ قاعدة البيانات المحدثة (مع روابط الفيديو)
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
            name TEXT UNIQUE,
            price_usd REAL,
            price_sdg REAL,
            link TEXT DEFAULT 'https://t.me/NexusStoreAr',
            video_url TEXT DEFAULT 'https://youtube.com'
        )
    ''')
    
    # المنتجات الافتراضية مع روابط فيديوهات توضيحية من يوتيوب
    default_products = [
        ("حزمة المونتاج الشاملة 🎬", 8.0, 15000.0, "https://www.youtube.com/results?search_query=video+editing+pack"),
        ("منشئ الـ CV الذكي 📝", 5.0, 10000.0, "https://www.youtube.com/results?search_query=smart+cv+builder"),
        ("كتاب أساسيات لغة بايثون بالعربي 🐍", 5.0, 10000.0, "https://www.youtube.com/results?search_query=python+for+beginners+arabic"),
        ("حزمة أيقونات وأزرار للمطورين والمصممين 🎨", 4.0, 8000.0, "https://www.youtube.com/results?search_query=ui+ux+icons+pack"),
        ("قالب موقع متجر إلكتروني احترافي 🌐", 15.0, 30000.0, "https://www.youtube.com/results?search_query=e+commerce+website+template"),
        ("دليل أوامر الذكاء الاصطناعي للمطورين 🤖", 6.0, 12000.0, "https://www.youtube.com/results?search_query=ai+prompts+for+developers"),
        ("كتاب التفكير الكمبيوتري والبرمجة بالعربي 📘", 5.0, 10000.0, "https://www.youtube.com/results?search_query=computational+thinking+arabic"),
        ("حزمة كود الخوارزميات وهياكل البيانات 💻", 8.0, 15000.0, "https://www.youtube.com/results?search_query=data+structures+algorithms"),
        ("كود مصدري لمتجر إلكتروني متكامل جاهز للتعديل 🛒", 20.0, 45000.0, "https://www.youtube.com/results?search_query=telegram+bot+store+source+code"),
        ("دليل أدوات الحماية واختبار الاختراق للمطورين 🛡️", 6.0, 12000.0, "https://www.youtube.com/results?search_query=penetration+testing+tools"),
        ("قالب Admin Dashboard جاهز للمطورين 📊", 10.0, 20000.0, "https://www.youtube.com/results?search_query=admin+dashboard+template"),
        ("دليل أوامر ChatGPT المتقدمة للمطورين 💡", 5.0, 10000.0, "https://www.youtube.com/results?search_query=chatgpt+advanced+prompts")
    ]
    
    for name, p_usd, p_sdg, v_url in default_products:
        cursor.execute('''
            INSERT OR IGNORE INTO products (name, price_usd, price_sdg, video_url)
            VALUES (?, ?, ?, ?)
        ''', (name, p_usd, p_sdg, v_url))

    conn.commit()
    conn.close()

def add_user(user_id, ref_id=0):
    conn = sqlite3.connect('nexus_store.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, ref_id))
    conn.commit()
    conn.close()

def get_products():
    conn = sqlite3.connect('nexus_store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price_usd, price_sdg, link, video_url FROM products")
    items = cursor.fetchall()
    conn.close()
    return items

def get_product_by_id(p_id):
    conn = sqlite3.connect('nexus_store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price_usd, price_sdg, video_url FROM products WHERE id = ?", (p_id,))
    item = cursor.fetchone()
    conn.close()
    return item

def get_all_users():
    conn = sqlite3.connect('nexus_store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

init_db()

# ==========================================
# 👁️ دالة المراقبة الشفافة (إرسال نسخة للمالك)
# ==========================================
def forward_to_admin(user_message, bot_response=None):
    try:
        user_info = f"👤 <b>الزبون:</b> {user_message.from_user.first_name} (<code>{user_message.chat.id}</code>)"
        msg_text = f"👁️ <b>مراقبة محادثة زبون:</b>\n{user_info}\n\n💬 <b>رسالة الزبون:</b>\n<i>{user_message.text}</i>"
        
        if bot_response:
            msg_text += f"\n\n🤖 <b>رد البوت عليه:</b>\n{bot_response}"
            
        bot.send_message(ADMIN_ID, msg_text)
    except Exception:
        pass

# ==========================================
# 🚀 القائمة الرئيسية
# ==========================================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.chat.id
    add_user(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📦 تصفح المتجر والمنتجات", callback_data="show_catalog"),
        types.InlineKeyboardButton("💡 مولد أفكار المشاريع (مجاناً)", callback_data="gen_project_idea")
    )
    markup.add(
        types.InlineKeyboardButton("🎁 جرعة الرفاهية والمعرفة اليومية", callback_data="daily_free_feature"),
        types.InlineKeyboardButton("🤖 المساعد الذكي لاقتراح المنتجات", callback_data="ask_ai_assistant")
    )
    markup.add(
        types.InlineKeyboardButton("💳 طرق الدفع", callback_data="show_payment"),
        types.InlineKeyboardButton("📩 الشكاوى والدعم", callback_data="open_ticket")
    )
    
    if user_id == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("👑 لوحة التحكم الإدارية", callback_data="admin_panel"))
        
    welcome_text = (
        f"أهلاً بك يا <b>{message.from_user.first_name}</b> في متجر Nexus المتطور! 🌟\n\n"
        "استمتع بالخدمات اليومية المجانية بالذكاء الاصطناعي واستكشف أحدث الرقميات لدينا مع الشروحات والفيديوهات التوضيحية."
    )
    bot.send_message(user_id, welcome_text, reply_markup=markup)

# ==========================================
# 🔘 معالجة الأزرار والخدمات
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    data = call.data
    user_id = call.message.chat.id

    # --- لوحة المالك والدردشة مع البوت ---
    if data == "admin_panel" and user_id == ADMIN_ID:
        users_count = len(get_all_users())
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("💬 بدء محادثة ودردشة مع البوت (Gemini)", callback_data="start_admin_chat"),
            types.InlineKeyboardButton("📢 إرسال إذاعة جماعية (Broadcast)", callback_data="start_broadcast"),
            types.InlineKeyboardButton("➕ إضافة منتج جديد للمتجر", callback_data="trigger_add_product")
        )
        msg = f"👑 <b>لوحة تحكم المالك:</b>\n\n👥 <b>عدد العملاء:</b> <code>{users_count}</code>\n⚡ اختر الإجراء المطلوب:"
        bot.send_message(user_id, msg, reply_markup=markup)

    elif data == "start_admin_chat" and user_id == ADMIN_ID:
        admin_states[ADMIN_ID] = "WAITING_ADMIN_AI"
        bot.send_message(user_id, "🤖 <b>وضع الدردشة الذكية مفعل!</b>\nأرسل أي سؤال أو استفسار وسأجيبك فوراً:")

    # --- عرض المنتجات والشرح والفيديو ---
    elif data == "show_catalog":
        products = get_products()
        markup = types.InlineKeyboardMarkup(row_width=1)
        for p in products:
            markup.add(types.InlineKeyboardButton(f"{p[1]} - {p[3]:,.0f} SDG / ${p[2]:.0f}", callback_data=f"product_detail_{p[0]}"))
        bot.send_message(user_id, "📦 <b>اضغط على أي منتج لعرض الشرح الذكي والفيديو التوضيحي:</b>", reply_markup=markup)

    elif data.startswith("product_detail_"):
        p_id = int(data.replace("product_detail_", ""))
        product = get_product_by_id(p_id)
        
        bot.send_chat_action(user_id, 'typing')
        prompt = f"قم بكتابة شرح تسويقي جذاب وتفصيلي للمنتج التالي لتوضيح أهميته وقيمته للزبون: '{product[1]}'."
        try:
            ai_desc = ai_model.generate_content(prompt).text
        except Exception:
            ai_desc = "منتج رقمي مميز جاهز للاستلام والتسليم الفوري."
            
        msg = (
            f"📌 <b>المنتج:</b> {product[1]}\n\n"
            f"💰 <b>السعر:</b> <code>{product[3]:,.0f} SDG</code> / <code>${product[2]:.0f} USD</code>\n\n"
            f"📖 <b>شرح وتفاصيل المنتج:</b>\n{ai_desc}"
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        # إضافة زر مشاهدة الفيديو من يوتيوب/الموقع الخارجي
        markup.add(types.InlineKeyboardButton("🎬 مشاهدة فيديو توضيحي / شرح يوتيوب", url=product[4]))
        markup.add(types.InlineKeyboardButton("🛒 طريقة الشراء والدفع", callback_data="show_payment"))
        markup.add(types.InlineKeyboardButton("🔙 العودة للمنتجات", callback_data="show_catalog"))
        
        bot.send_message(user_id, msg, reply_markup=markup)

    # --- خدمات الرفاهية المضافة ---
    elif data == "gen_project_idea":
        bot.send_chat_action(user_id, 'typing')
        prompt = "اقترح فكرة مشروع تقني أو رقمي مربح وذكية لمطور أو مصمم مبتدئ، مع خطوات التنفيذ باختصار."
        try:
            idea = ai_model.generate_content(prompt).text
            bot.send_message(user_id, f"💡 <b>فكرة مشروع ممتازة لك:</b>\n\n{idea}")
        except Exception:
            bot.send_message(user_id, "⚠️ الخدمة مشغولة حالياً، جرب لاحقاً!")

    elif data == "daily_free_feature":
        bot.send_chat_action(user_id, 'typing')
        prompt = "اعطني معلومة أو نصيحة تقنية رائعة وغير معروفة لكثير من الناس في مجالات البرمجة أو الذكاء الاصطناعي."
        try:
            tip = ai_model.generate_content(prompt).text
            bot.send_message(user_id, f"🎁 <b>جرعتك اليومية المجانية:</b>\n\n{tip}")
        except Exception:
            bot.send_message(user_id, "⚠️ يتعذر الحصول على الجرعة اليومية الآن.")

    elif data == "ask_ai_assistant":
        user_states[user_id] = "WAITING_CUSTOMER_AI"
        bot.send_message(user_id, "🤖 <b>أهلاً بك!</b> اكتب لي ما الذي تبحث عنه أو ميزانيتك، وسأرشح لك الخيار الأفضل من المتجر:")

    elif data == "show_payment":
        payment_info = (
            "💳 <b>طرق الدفع المتاحة:</b>\n\n"
            f"🇸🇩 <b>بنكك:</b> <code>{BANKAK_ACCOUNT}</code> ({BANKAK_NAME})\n"
            f"💵 <b>Binance Pay ID:</b> <code>{BINANCE_PAY_ID}</code>\n\n"
            "📌 <i>أرسل صورة إشعار التحويل في المحادثة مباشرة لتأكيد الطلب واستلامه!</i>"
        )
        bot.send_message(user_id, payment_info)

# ==========================================
# 📥 استقبال الرسائل وتوجيه المراقبة والدردشة
# ==========================================
@bot.message_handler(func=lambda msg: True)
def handle_text_messages(message):
    user_id = message.chat.id
    
    # 1. الدردشة الخاصة بين المالك والبوت
    if user_id == ADMIN_ID and admin_states.get(ADMIN_ID) == "WAITING_ADMIN_AI":
        admin_states[ADMIN_ID] = None  # إعادة تعيين الحالة بعد الإجابة
        try:
            res = ai_model.generate_content(message.text)
            bot.send_message(ADMIN_ID, f"🤖 <b>الرد الذكي للمالك:</b>\n\n{res.text}")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"⚠️ خطأ في معالجة الطلب: {e}")

    # 2. محادثة الزبون مع المساعد الذكي
    elif user_states.get(user_id) == "WAITING_CUSTOMER_AI":
        user_states[user_id] = None
        products = get_products()
        products_text = "\n".join([f"- {p[1]} ({p[3]} SDG)" for p in products])
        prompt = f"أنت مساعد متجر Nexus Store. المنتجات:\n{products_text}\nطلب الزبون: '{message.text}'. اقترح عليه الأنسب."
        try:
            res = ai_model.generate_content(prompt)
            bot.send_message(user_id, f"🤖 <b>المساعد الذكي:</b>\n\n{res.text}")
            
            # توجيه نسخة من المحادثة للمالك للمراقبة
            forward_to_admin(message, res.text)
        except Exception:
            bot.send_message(user_id, "⚠️ متعذر معالجة الطلب حالياً.")

    # 3. توجيه جميع رسائل الزبائن العادية للمالك
    elif user_id != ADMIN_ID:
        forward_to_admin(message, "رسالة عامة (تواصل من زبون)")

if __name__ == "__main__":
    keep_alive()
    print("🚀 Nexus Store Engine Running with Video Embeds & Admin AI Chat...")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            time.sleep(5)
