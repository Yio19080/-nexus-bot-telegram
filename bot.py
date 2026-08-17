import os
import threading
import time
import sqlite3
import datetime
import re
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
    return "Nexus Store Engine with Strict Receipt Check is Online!"

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

# تفعيل متعدد المسارات لسرعة فائقة
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML", threaded=True, num_threads=10)

admin_states = {}
user_states = {}
handled_receipts = set()

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
    
    default_products = [
        ("حزمة المونتاج الشاملة 🎬", 8.0, 15000.0, "https://t.me/NexusStoreAr", "https://www.youtube.com/results?search_query=video+editing+pack", "حزمة ملحقات وقوالب احترافية لمصممي الفيديوهات والمونتاج."),
        ("منشئ الـ CV الذكي 📝", 5.0, 10000.0, "https://t.me/NexusStoreAr", "https://www.youtube.com/results?search_query=smart+cv+builder", "أداة وقوالب سريعة لإنشاء سيرة ذاتية احترافية توافق معايير الشركات."),
        ("كتاب أساسيات لغة بايثون بالعربي 🐍", 5.0, 10000.0, "https://t.me/NexusStoreAr", "https://www.youtube.com/results?search_query=python+for+beginners+arabic", "كتاب مبسط لشرح لغة بايثون وأساسيات البرمجة باللغة العربية."),
        ("حزمة أيقونات وأزرار للمطورين والمصممين 🎨", 4.0, 8000.0, "https://t.me/NexusStoreAr", "https://www.youtube.com/results?search_query=ui+ux+icons+pack", "مجموعة كبيرة من الأيقونات والأزرار عالية الجودة لاستخدامها في التطبيقات والمواقع."),
        ("قالب موقع متجر إلكتروني احترافي 🌐", 15.0, 30000.0, "https://t.me/NexusStoreAr", "https://www.youtube.com/results?search_query=e+commerce+website+template", "قالب متجر إلكتروني متكامل وجاهز للتعديل المباشر."),
        ("دليل أوامر الذكاء الاصطناعي للمطورين 🤖", 6.0, 12000.0, "https://t.me/NexusStoreAr", "https://www.youtube.com/results?search_query=ai+prompts+for+developers", "مجموعة أوامر وموجهات جاهزة للحصول على أفضل نتائج برمجية من الذكاء الاصطناعي."),
        ("كتاب التفكير الكمبيوتري والبرمجة بالعربي 📘", 5.0, 10000.0, "https://t.me/NexusStoreAr", "https://www.youtube.com/results?search_query=computational+thinking+arabic", "دليل مبسط لفهم التفكير البرمجي وحل المشكلات التكنولوجية."),
        ("حزمة كود الخوارزميات وهياكل البيانات 💻", 8.0, 15000.0, "https://t.me/NexusStoreAr", "https://www.youtube.com/results?search_query=data+structures+algorithms", "أكواد مصدريّة وشروحات جاهزة لأهم الخوارزميات وهياكل البيانات."),
        ("كود مصدري لمتجر إلكتروني متكامل جاهز للتعديل 🛒", 20.0, 45000.0, "https://t.me/NexusStoreAr", "https://www.youtube.com/results?search_query=telegram+bot+store+source+code", "سورس كود كامل لبوت متجر تلجرام جاهز للتشغيل مباشرة."),
        ("دليل أدوات الحماية واختبار الاختراق للمطورين 🛡️", 6.0, 12000.0, "https://t.me/NexusStoreAr", "https://www.youtube.com/results?search_query=penetration+testing+tools", "دليل شامل لأهم أدوات واختبارات الأمان وحماية التطبيقات."),
        ("قالب Admin Dashboard جاهز للمطورين 📊", 10.0, 20000.0, "https://t.me/NexusStoreAr", "https://www.youtube.com/results?search_query=admin+dashboard+template", "لوحة تحكم إدارية احترافية لتنظيم وإدارة البيانات بسهولة."),
        ("دليل أوامر ChatGPT المتقدمة للمطورين 💡", 5.0, 10000.0, "https://t.me/NexusStoreAr", "https://www.youtube.com/results?search_query=chatgpt+advanced+prompts", "طرق وموجهات متقدمة للاستفادة القصوى من خدمات ChatGPT.")
    ]
    
    for name, p_usd, p_sdg, link, v_url, desc in default_products:
        cursor.execute('''
            INSERT OR IGNORE INTO products (name, price_usd, price_sdg, link, video_url, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, p_usd, p_sdg, link, v_url, desc))

    conn.commit()
    conn.close()

def add_user(user_id, ref_id=0):
    conn = sqlite3.connect('nexus_store.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, ref_id))
    conn.commit()
    conn.close()

def get_products():
    conn = sqlite3.connect('nexus_store.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price_usd, price_sdg, link, video_url, description FROM products")
    items = cursor.fetchall()
    conn.close()
    return items

def get_product_by_id(p_id):
    conn = sqlite3.connect('nexus_store.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price_usd, price_sdg, video_url, description FROM products WHERE id = ?", (p_id,))
    item = cursor.fetchone()
    conn.close()
    return item

def add_new_product(name, price_usd, price_sdg, desc, video_url):
    conn = sqlite3.connect('nexus_store.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (name, price_usd, price_sdg, description, video_url)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, price_usd, price_sdg, desc, video_url))
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
# 🧠 دالة الفحص الدقيق والمحدث للإشعار (الاسم + الحساب + التاريخ)
# ==========================================
def ai_verify_receipt(receipt_info, image_path=None):
    current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    prompt = f"""
    أنت نظام أمان وفحص آلي لإشعارات التحويل البنكي (مثل تطبيق بنكك - بنك الخرطوم).
    تاريخ ووقت النظام الحالي هو: {current_time_str}

    المطلوب منك فحص الإشعار والتحقق الصارم من الشروط التالية:
    1. **مطابقة الاسم:** يجب أن يكون اسم المرسل إليه هو "يوسف ابراهيم الطيب عبدالقادر" (أو يوسف إبراهيم الطيب عبد القادر مع مراعاة همزات الألف والمسافات).
    2. **مطابقة رقم الحساب:** يجب أن يحتوي الإشعار على رقم الحساب "9412190" (تذكر أن تطبيق بنكك يكتبه بشكل كامل مكون من 16 رقماً مثل 1003 0941 2190 0001 حيث يمثل المقطع الأوسط 0941 2190 الرقم 9412190).
    3. **فحص التاريخ والوقت:** يجب أن يكون تاريخ العملية حديثاً وقريباً جداً من وقت النظام الحالي ({current_time_str}). يمنع تماماً قبول أي إشعارات بتواريخ مستقبليّة أو قديمة جداً.

    إذا تحققت الشروط الثلاثة، ابدأ إجابتك بكلمة: 'APPROVED' ثم اكتب الشرح باختصار.
    إذا اختل أي شرط من الشروط، ابدأ إجابتك بكلمة: 'REJECTED' واذكر السبب بالتفصيل (مثل: عدم تطابق الاسم، الحساب غير صحيح، التاريخ في المستقبل، إلخ).
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

# ==========================================
# ⏱️ خيط المراقبة والفحص بعد دقيقة واحدة
# ==========================================
def process_receipt_after_timeout(receipt_id, user_id, receipt_content, image_path=None):
    time.sleep(60) # الانتظار دقيقة واحدة للمالك
    
    if receipt_id in handled_receipts:
        return # المالك وافق أو رفض يدويًا قبل انتهاء الدقيقة

    handled_receipts.add(receipt_id)
    
    # تنفيذ الفحص بالذكاء الاصطناعي
    ai_result = ai_verify_receipt(receipt_content, image_path)
    
    if image_path and os.path.exists(image_path):
        try:
            os.remove(image_path) # تنظيف الصورة المؤقتة
        except Exception:
            pass

    if ai_result.startswith("APPROVED"):
        explanation = ai_result.replace("APPROVED", "").strip()
        bot.send_message(user_id, f"✅ <b>تم القبول التلقائي للإشعار بنجاح!</b>\n\n🎯 <b>مطابقة البيانات:</b> الاسم ورقم الحساب والتاريخ صحيحة.\n📝 <i>التفاصيل:</i> {explanation}\n\nجاري تسليم الخدمة لك.")
        bot.send_message(ADMIN_ID, f"⚡ <b>قبول آلي لإشعار تحويل (عدم الرد خلال دقيقة):</b>\n👤 الزبون: <code>{user_id}</code>\n📝 {explanation}")
    else:
        explanation = ai_result.replace("REJECTED", "").strip()
        bot.send_message(user_id, f"❌ <b>تم رفض الإشعار تلقائياً!</b>\n\n⚠️ <i>سبب الرفض:</i> {explanation}\n💬 إذا كان هناك خطأ، تواصل مع الدعم.")
        bot.send_message(ADMIN_ID, f"⚠️ <b>رفض آلي لإشعار تحويل غير مطابق:</b>\n👤 الزبون: <code>{user_id}</code>\n📝 {explanation}")

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
        "عند التحويل، يرجى إرسال صورة أو نص إشعار بنكك هنا ليتم التثبت منه فوراً."
    )
    bot.send_message(user_id, welcome_text, reply_markup=markup)

# ==========================================
# 🔘 معالجة الأزرار تفاعلياً
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    data = call.data
    user_id = call.message.chat.id

    # --- أزرار المالك للموافقة/الرفض اليدوي ---
    if data.startswith("appr_rcpt_") and user_id == ADMIN_ID:
        rcpt_id = data.replace("appr_rcpt_", "")
        handled_receipts.add(rcpt_id)
        target_user = int(rcpt_id.split("_")[0])
        try:
            bot.send_message(target_user, "✅ <b>تمت الموافقة على إشعار التحويل يدوياً بواسطة المالك!</b>\nجاري تجهيز وتسليم الطلب.")
            bot.edit_message_text(f"{call.message.text}\n\n✅ <b>تم قبول الإشعار وتأكيده يدويًا بواسطة المالك.</b>", chat_id=ADMIN_ID, message_id=call.message.message_id)
        except Exception:
            bot.send_message(ADMIN_ID, "⚠️ تعذر التواصل مع الزبون.")

    elif data.startswith("reje_rcpt_") and user_id == ADMIN_ID:
        rcpt_id = data.replace("reje_rcpt_", "")
        handled_receipts.add(rcpt_id)
        target_user = int(rcpt_id.split("_")[0])
        try:
            bot.send_message(target_user, "❌ <b>عذراً، تم رفض إشعار التحويل من قبل المالك.</b>\nتأكد من صحة الحساب والتحويل ثم تواصل معنا.")
            bot.edit_message_text(f"{call.message.text}\n\n❌ <b>تم رفض الإشعار يدويًا بواسطة المالك.</b>", chat_id=ADMIN_ID, message_id=call.message.message_id)
        except Exception:
            bot.send_message(ADMIN_ID, "⚠️ تعذر التواصل مع الزبون.")

    # --- لوحة التحكم ---
    elif data == "admin_panel" and user_id == ADMIN_ID:
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
        bot.send_message(user_id, "🤖 <b>وضع الدردشة الذكية مفعل!</b>\nأرسل استفسارك وسأجيبك فوراً:")

    elif data == "start_broadcast" and user_id == ADMIN_ID:
        admin_states[ADMIN_ID] = "WAITING_BROADCAST_TEXT"
        bot.send_message(user_id, "📢 <b>إرسال إذاعة جماعية:</b>\nاكتب النص المطلوب نشره وإرساله لجميع العملاء الآن:")

    elif data == "trigger_add_product" and user_id == ADMIN_ID:
        admin_states[ADMIN_ID] = "WAITING_ADD_PRODUCT_DATA"
        msg = "➕ <b>إضافة منتج جديد:</b>\nأرسل البيانات بفواصل <code>|</code>:\n<code>اسم المنتج | سعر_دولار | سعر_سوداني | الوصف | رابط_الفيديو</code>"
        bot.send_message(user_id, msg)

    # --- الكتالوج والمنتجات ---
    elif data == "show_catalog":
        products = get_products()
        markup = types.InlineKeyboardMarkup(row_width=1)
        for p in products:
            markup.add(types.InlineKeyboardButton(f"{p[1]} - {p[3]:,.0f} SDG / ${p[2]:.0f}", callback_data=f"product_detail_{p[0]}"))
        bot.send_message(user_id, "📦 <b>اختر أي منتج لعرض التفاصيل والفيديو التوضيحي:</b>", reply_markup=markup)

    elif data.startswith("product_detail_"):
        p_id = int(data.replace("product_detail_", ""))
        product = get_product_by_id(p_id)
        desc = product[5] if len(product) > 5 and product[5] else "منتج رقمي مميز جاهز للاستلام والتسليم الفوري."
            
        msg = (
            f"📌 <b>المنتج:</b> {product[1]}\n\n"
            f"💰 <b>السعر:</b> <code>{product[3]:,.0f} SDG</code> / <code>${product[2]:.0f} USD</code>\n\n"
            f"📖 <b>الشرح:</b>\n{desc}"
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🎬 مشاهدة فيديو توضيحي", url=product[4]))
        markup.add(types.InlineKeyboardButton("🛒 طريقة الشراء والدفع", callback_data="show_payment"))
        markup.add(types.InlineKeyboardButton("🔙 العودة للمنتجات", callback_data="show_catalog"))
        
        bot.send_message(user_id, msg, reply_markup=markup)

    elif data == "gen_project_idea":
        bot.send_chat_action(user_id, 'typing')
        try:
            idea = ai_model.generate_content("اقترح فكرة مشروع تقني أو رقمي مربح باختصار شديد.").text
            bot.send_message(user_id, f"💡 <b>فكرة مشروع ممتازة:</b>\n\n{idea}")
        except Exception:
            bot.send_message(user_id, "⚠️ الخدمة مشغولة حالياً!")

    elif data == "daily_free_feature":
        bot.send_chat_action(user_id, 'typing')
        try:
            tip = ai_model.generate_content("اعطني نصيحة تقنية ممتازة وسريعة في البرمجة.").text
            bot.send_message(user_id, f"🎁 <b>جرعتك اليومية:</b>\n\n{tip}")
        except Exception:
            bot.send_message(user_id, "⚠️ متعذر جلب النصيحة الآن.")

    elif data == "ask_ai_assistant":
        user_states[user_id] = "WAITING_CUSTOMER_AI"
        bot.send_message(user_id, "🤖 <b>أهلاً بك!</b> اكتب لي ما الذي تبحث عنه وسأرشح لك الخيار الأفضل:")

    elif data == "show_payment":
        payment_info = (
            "💳 <b>طرق الدفع المتاحة:</b>\n\n"
            f"🇸🇩 <b>بنكك:</b> <code>{BANKAK_ACCOUNT}</code> ({BANKAK_NAME})\n"
            f"💵 <b>Binance Pay ID:</b> <code>{BINANCE_PAY_ID}</code>\n"
            f"🌐 <b>عنوان المحفظة:</b> <code>{BINANCE_WALLET_ADDRESS}</code>\n\n"
            "📌 <i>أرسل نص إشعار التحويل أو صورته هنا مباشرة لتأكيد الطلب!</i>"
        )
        bot.send_message(user_id, payment_info)

    elif data == "open_ticket":
        bot.send_message(user_id, "📩 أرسل استفسارك هنا مباشرة وسيقوم المالك بالرد عليك فوراً.")

# ==========================================
# 🖼️ استقبال صور الإشعارات المالية وقراءتها
# ==========================================
@bot.message_handler(content_types=['photo'])
def handle_photo_receipt(message):
    user_id = message.chat.id
    if user_id == ADMIN_ID:
        return

    rcpt_id = f"{user_id}_{message.message_id}"
    caption = message.caption if message.caption else "صورة إشعار تحويل مالي"

    # حفظ الصورة مؤقتاً لقراءتها وفحصها
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    temp_img_path = f"temp_rcpt_{rcpt_id}.jpg"
    with open(temp_img_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    # تجهيز أزرار المالك
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ موافقة وتأكيد", callback_data=f"appr_rcpt_{rcpt_id}"),
        types.InlineKeyboardButton("❌ رفض الإشعار", callback_data=f"reje_rcpt_{rcpt_id}")
    )
    markup.add(types.InlineKeyboardButton("💬 مراسلة الزبون", url=f"tg://user?id={user_id}"))

    bot.send_photo(
        ADMIN_ID, 
        message.photo[-1].file_id, 
        caption=f"💳 <b>إشعار تحويل مالي جديد (صورة):</b>\n👤 من: {message.from_user.first_name} (<code>{user_id}</code>)\n📝 {caption}", 
        reply_markup=markup
    )
    
    bot.send_message(user_id, "⏳ <b>تم استلام صورة الإشعار!</b>\nجاري الانتظار أو الفحص التلقائي للاسم والبريد والتاريخ خلال دقيقة...")

    # بدء خيط المراقبة والفحص الآلي بعد دقيقة
    t = threading.Thread(target=process_receipt_after_timeout, args=(rcpt_id, user_id, f"صورة إشعار تحويل. نص مرفق: {caption}", temp_img_path))
    t.daemon = True
    t.start()

# ==========================================
# 📥 استقبال الرسائل النصية والإشعارات
# ==========================================
@bot.message_handler(func=lambda msg: True)
def handle_text_messages(message):
    user_id = message.chat.id
    text = message.text
    
    # 1. حالة المالك: دردشة Gemini
    if user_id == ADMIN_ID and admin_states.get(ADMIN_ID) == "WAITING_ADMIN_AI":
        admin_states[ADMIN_ID] = None
        try:
            res = ai_model.generate_content(text)
            bot.send_message(ADMIN_ID, f"🤖 <b>الرد الذكي:</b>\n\n{res.text}")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"⚠️ خطأ: {e}")

    # 2. حالة المالك: الإذاعة الجماعية السريعة
    elif user_id == ADMIN_ID and admin_states.get(ADMIN_ID) == "WAITING_BROADCAST_TEXT":
        admin_states[ADMIN_ID] = None
        users = get_all_users()
        sent_count = 0
        bot.send_message(ADMIN_ID, f"⏳ جاري إرسال الإذاعة إلى <code>{len(users)}</code> مستخدم...")
        
        for u_id in users:
            try:
                bot.send_message(u_id, f"📢 <b>تنبيه من الإدارة:</b>\n\n{text}")
                sent_count += 1
            except Exception:
                pass
        bot.send_message(ADMIN_ID, f"✅ <b>تم الإرسال بنجاح!</b> إلى <code>{sent_count}</code> مستخدم.")

    # 3. حالة المالك: إضافة منتج
    elif user_id == ADMIN_ID and admin_states.get(ADMIN_ID) == "WAITING_ADD_PRODUCT_DATA":
        admin_states[ADMIN_ID] = None
        try:
            parts = [p.strip() for p in text.split("|")]
            add_new_product(parts[0], float(parts[1]), float(parts[2]), parts[3], parts[4])
            bot.send_message(ADMIN_ID, f"✅ تم إضافة المنتج <b>{parts[0]}</b> بنجاح!")
        except Exception:
            bot.send_message(ADMIN_ID, "⚠️ خطأ في التنسيق!")

    # 4. حالة الزبون: المساعد الذكي
    elif user_states.get(user_id) == "WAITING_CUSTOMER_AI":
        user_states[user_id] = None
        products = get_products()
        products_text = "\n".join([f"- {p[1]} ({p[3]} SDG)" for p in products])
        prompt = f"المنتجات المتاحة:\n{products_text}\nطلب الزبون: '{text}'. اقترح عليه الأنسب باختصار."
        try:
            res = ai_model.generate_content(prompt)
            bot.send_message(user_id, f"🤖 <b>المساعد الذكي:</b>\n\n{res.text}")
        except Exception:
            bot.send_message(user_id, "⚠️ متعذر معالجة الطلب حالياً.")

    # 5. استقبال الرسائل وإشعارات التحويل النصية من العملاء
    elif user_id != ADMIN_ID:
        rcpt_id = f"{user_id}_{message.message_id}"
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ موافقة وتأكيد", callback_data=f"appr_rcpt_{rcpt_id}"),
            types.InlineKeyboardButton("❌ رفض الإشعار", callback_data=f"reje_rcpt_{rcpt_id}")
        )
        markup.add(types.InlineKeyboardButton("💬 مراسلة الزبون", url=f"tg://user?id={user_id}"))

        bot.send_message(
            ADMIN_ID, 
            f"🔔 <b>رسالة / إشعار تحويل جديد من زبون:</b>\n👤 من: {message.from_user.first_name} (<code>{user_id}</code>)\n\n💬 <b>النص:</b>\n<i>{text}</i>", 
            reply_markup=markup
        )
        
        bot.send_message(user_id, "⏳ <b>تم استلام الرسالة/الإشعار!</b>\nسيتم التحقق والفحص التلقائي للاسم والحساب خلال دقيقة واحدة.")

        # تشغيل خيط الفحص الآلي بالذكاء الاصطناعي بعد دقيقة
        t = threading.Thread(target=process_receipt_after_timeout, args=(rcpt_id, user_id, text, None))
        t.daemon = True
        t.start()

if __name__ == "__main__":
    keep_alive()
    print("🚀 Nexus Store Engine with Strict Receipt Check Active...")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            time.sleep(2)
