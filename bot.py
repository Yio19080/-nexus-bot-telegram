import os
import threading
import time
import sqlite3
import datetime
import random
import telebot
from telebot import types
from flask import Flask
import google.generativeai as genai
import PIL.Image

# ==========================================
# 🌐 السيرفر وإعدادات التشغيل
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Nexus Store Engine - Gaming & Points System Fully Active!"

def keep_alive():
    t = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080))
    t.daemon = True
    t.start()

# البيانات الرسمية المفاتيح والروابط
TOKEN = os.getenv("BOT_TOKEN", "8617844634:AAGfD4f-dpgmpPn2Zo0ZPdaGq09Vvm7cL18")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "ضع_مفتاح_GEMINI_هنا")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7899998427"))

CHANNEL_LINK = "https://t.me/NexusStoreAr"
CHANNEL_USERNAME = "@NexusStoreAr"
BOT_LINK = "https://t.me/NexusStoreArBot"

BANKAK_ACCOUNT = "9412190"
BANKAK_NAME = "يوسف إبراهيم الطيب عبد القادر"
BINANCE_PAY_ID = "943209825"
BINANCE_WALLET_ADDRESS = "0x6742c39cb07b9fd6a69281dc4b9b96239cc7850a"

# 🌐 روابط منصات تداول العملات الرقمية الرسمية
CRYPTO_EXCHANGES = {
    "Binance": "https://www.binance.com",
    "OKX": "https://www.okx.com",
    "Bybit": "https://www.bybit.com",
    "KuCoin": "https://www.kucoin.com"
}

genai.configure(api_key=GEMINI_KEY)
ai_model = genai.GenerativeModel('gemini-3.6-flash')
bot = telebot.TeleBot(TOKEN, parse_mode="HTML", threaded=True, num_threads=10)

admin_states = {}
pending_orders = {}
handled_receipts = set()
game_states = {}

# ==========================================
# 🗄️ قاعدة البيانات المتقدمة (نقاط + منتجات + إحالة)
# ==========================================
def init_db():
    conn = sqlite3.connect('nexus.db', check_same_thread=False)
    c = conn.cursor()
    
    # جدول المستخدمين والنقاط والإحالة
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            points INTEGER DEFAULT 0,
            referred_by INTEGER DEFAULT 0,
            last_spin TEXT DEFAULT ''
        )
    ''')
    
    # جدول المنتجات بالنقاط والأسعار
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price_sdg REAL,
            price_usd REAL,
            price_points INTEGER DEFAULT 500,
            link TEXT,
            desc TEXT
        )
    ''')
    
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        default_products = [
            ("دليل التداول الرقمي (PDF)", 15000.0, 6.0, 300, "https://t.me/c/link_to_pdf", "دليل إرشادي شامل + فيديو شرح محتوى الكتيب."),
            ("قوالب Canva احترافية", 10000.0, 4.0, 200, "https://www.canva.com/design/XXXXX/view", "حزمة قوالب تصميم جاهزة للتعديل المباشر والسريع."),
            ("مكتبة المصادر البرمجية", 12500.0, 5.0, 250, "https://drive.google.com/your_folder", "أفضل 500 مصدر وموقع تقني موثوق لتعلم البرمجة."),
            ("عضوية مجتمع VIP الخاص", 25000.0, 10.0, 500, "https://t.me/+AbCdEfGhIjKl", "رابط دعوة مباشر للحصول على التحديثات الحصرية."),
            ("حزمة فلاتر Lightroom", 10000.0, 4.0, 200, "https://t.me/your_file_link", "فلاتر جاهزة لتعديل الصور باحترافية بضغطة زر.")
        ]
        c.executemany("INSERT INTO products (name, price_sdg, price_usd, price_points, link, desc) VALUES (?, ?, ?, ?, ?, ?)", default_products)
        conn.commit()
    conn.close()

def add_user(user_id, referrer=0):
    conn = sqlite3.connect('nexus.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not c.fetchone():
        c.execute("INSERT INTO users (user_id, points, referred_by) VALUES (?, ?, ?)", (user_id, 20, referrer)) # 20 نقطة هدية تسجيل
        if referrer and referrer != user_id:
            c.execute("UPDATE users SET points = points + 50 WHERE user_id = ?", (referrer,))
            try:
                bot.send_message(referrer, "🎉 <b>قام أحد الأصدقاء بالتسجيل عن طريق رابطك!</b>\nتمت إضافة <b>50 نقطة</b> إلى حسابك!")
            except: pass
        conn.commit()
    conn.close()

def get_user_points(user_id):
    conn = sqlite3.connect('nexus.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def add_user_points(user_id, pts):
    conn = sqlite3.connect('nexus.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (pts, user_id))
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 🎨 النشر التلقائي كل 10 دقائق
# ==========================================
def auto_poster():
    topics = [
        "عروض المنتجات الرقمية المجانية بالنقاط",
        "قسم الألعاب الترفيهية وجمع النقاط في Nexus Store",
        "تداول العملات والوصول الحصري لمجتمع VIP"
    ]
    idx = 0
    while True:
        try:
            time.sleep(600)
            topic = topics[idx % len(topics)]
            idx += 1
            ad_text = ai_model.generate_content(f"اكتب إعلان قصير وجذاب عن: {topic}").text
            img_url = "https://image.pollinations.ai/prompt/digital%20store%20gaming%20banner?width=800&height=500&nologo=true"
            full_ad = f"{ad_text}\n\n📢 <b>القناة الرسمية:</b> {CHANNEL_LINK}\n🤖 <b>للطلب ولعب الألعاب:</b> {BOT_LINK}"
            bot.send_photo(CHANNEL_USERNAME, img_url, caption=full_ad)
        except Exception as e:
            print(f"Auto post error: {e}")

threading.Thread(target=auto_poster, daemon=True).start()

# ==========================================
# 🧠 الفحص الآلي وتسليم الطلبات
# ==========================================
def deliver_product(user_id, product):
    p_id, p_name, p_sdg, p_usd, p_pts, p_link, p_desc = product
    msg = (
        f"🎉 <b>تم تأكيد العملية وتسليم طلبك بنجاح!</b>\n\n"
        f"📦 <b>المنتج:</b> {p_name}\n"
        f"📝 <b>الوصف:</b> {p_desc}\n\n"
        f"🔗 <b>رابط الوصول الخاص بك:</b>\n{p_link}\n\n"
        "شكراً لتسوقك من Nexus Store! ❤️"
    )
    bot.send_message(user_id, msg, disable_web_page_preview=False)

def process_receipt_after_timeout(receipt_id, user_id, receipt_content, image_path=None):
    time.sleep(60)
    if receipt_id in handled_receipts:
        return

    handled_receipts.add(receipt_id)
    current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    prompt = f"فحص إشعار بنكك/بينانس (الاسم: يوسف ابراهيم الطيب عبدالقادر، الحساب: 9412190، الوقت: {current_time_str}). إذا صحيح ابدأ بـ APPROVED وإلا REJECTED."
    
    try:
        if image_path and os.path.exists(image_path):
            img = PIL.Image.open(image_path)
            ai_result = ai_model.generate_content([prompt, img, receipt_content]).text.strip()
            os.remove(image_path)
        else:
            ai_result = ai_model.generate_content(f"{prompt}\n\n{receipt_content}").text.strip()
    except Exception as e:
        ai_result = f"REJECTED\nخطأ: {e}"

    selected_p = pending_orders.get(user_id)

    if ai_result.startswith("APPROVED"):
        if selected_p: deliver_product(user_id, selected_p)
        else: bot.send_message(user_id, "✅ <b>تم قبول الإشعار بنجاح!</b>")
        bot.send_message(ADMIN_ID, f"⚡ <b>قبول آلي للإشعار:</b>\n👤 المستخدم: <code>{user_id}</code>")
    else:
        explanation = ai_result.replace("REJECTED", "").strip()
        bot.send_message(user_id, f"❌ <b>تم رفض الإشعار تلقائياً:</b>\n{explanation}")

# ==========================================
# 🚀 القائمة الرئيسية والترحيـب (/start)
# ==========================================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.chat.id
    text_args = message.text.split()
    referrer = int(text_args[1]) if len(text_args) > 1 and text_args[1].isdigit() else 0
    add_user(user_id, referrer)

    pts = get_user_points(user_id)
    welcome_text = (
        f"👋 <b>مرحباً بك يا {message.from_user.first_name} في متجر Nexus Store!</b>\n\n"
        f"💰 <b>رصيد نقاطك الحالي:</b> <code>{pts} نقطة</code>\n\n"
        "🎯 <b>اختر من الأقسام أدمناه ما يناسبك:</b>"
    )

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🛒 قائمة المنتجات والشراء", callback_data="show_products"),
        types.InlineKeyboardButton("🎮 قسم الألعاب والترفيه", callback_data="show_games"),
        types.InlineKeyboardButton("🎁 جمع النقاط والإحالة", callback_data="show_referral"),
        types.InlineKeyboardButton("📈 تداول العملات والمحافظ", callback_data="show_crypto")
    )
    markup.add(types.InlineKeyboardButton("📢 القناة الرسمية", url=CHANNEL_LINK))
    
    if user_id == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("👑 لوحة التحكم والأسعار", callback_data="admin_panel"))

    bot.send_message(user_id, welcome_text, reply_markup=markup)

# ==========================================
# 🔘 تفاعلات القوائم والأزرار
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    try: bot.answer_callback_query(call.id)
    except: pass

    data = call.data
    user_id = call.message.chat.id

    # 🛒 1. عرض المنتجات الخيارات (دفع أو نقاط)
    if data == "show_products":
        conn = sqlite3.connect('nexus.db', check_same_thread=False)
        products = conn.cursor().execute("SELECT * FROM products").fetchall()
        conn.close()

        markup = types.InlineKeyboardMarkup(row_width=1)
        for p in products:
            p_id, p_name, p_sdg, p_usd, p_pts, _, _ = p
            btn_text = f"📦 {p_name} | {int(p_sdg):,} SDG / ${p_usd:.1f} / ⭐ {p_pts} نقطة"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"select_p_{p_id}"))
        
        markup.add(types.InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_home"))
        bot.send_message(user_id, "🛒 <b>اختر المنتج لعرض خيارات الشراء:</b>", reply_markup=markup)

    # اختيار المنتج وتحديد طريقة الشراء
    elif data.startswith("select_p_"):
        p_id = int(data.replace("select_p_", ""))
        conn = sqlite3.connect('nexus.db', check_same_thread=False)
        product = conn.cursor().execute("SELECT * FROM products WHERE id=?", (p_id,)).fetchone()
        conn.close()

        if product:
            pending_orders[user_id] = product
            _, name, price_sdg, price_usd, price_pts, _, desc = product
            pts = get_user_points(user_id)

            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("💳 الشراء بالمال (بنكك / Binance)", callback_data=f"buy_money_{p_id}"))
            markup.add(types.InlineKeyboardButton(f"⭐ الشراء بالنقاط ({price_pts} نقطة)", callback_data=f"buy_points_{p_id}"))
            markup.add(types.InlineKeyboardButton("🔙 العودة للمنتجات", callback_data="show_products"))

            msg = (
                f"📦 <b>المنتج:</b> {name}\n"
                f"📝 <b>الوصف:</b> {desc}\n\n"
                f"💵 <b>السعر:</b> {int(price_sdg):,} SDG | ${price_usd:.2f}\n"
                f"⭐ <b>السعر بالنقاط:</b> {price_pts} نقطة\n"
                f"🏆 <b>رصيدك الحالي:</b> {pts} نقطة"
            )
            bot.send_message(user_id, msg, reply_markup=markup)

    elif data.startswith("buy_money_"):
        product = pending_orders.get(user_id)
        if product:
            pay_msg = (
                f"💳 <b>بيانات تحويل المبلغ المالي:</b>\n\n"
                f"🇸🇩 <b>بنكك:</b> <code>{BANKAK_ACCOUNT}</code>\n"
                f"👤 <b>الاسم:</b> {BANKAK_NAME}\n"
                f"💵 <b>Binance Pay ID:</b> <code>{BINANCE_PAY_ID}</code>\n"
                f"🌐 <b>USDT TRC20:</b> <code>{BINANCE_WALLET_ADDRESS}</code>\n\n"
                "📌 <b>قم بالتحويل ثم أرسل صورة الإشعار أو النص هنا مباشرة!</b>"
            )
            bot.send_message(user_id, pay_msg)

    elif data.startswith("buy_points_"):
        product = pending_orders.get(user_id)
        if product:
            p_pts = product[4]
            user_pts = get_user_points(user_id)
            if user_pts >= p_pts:
                add_user_points(user_id, -p_pts)
                deliver_product(user_id, product)
            else:
                bot.send_message(user_id, f"❌ <b>نقاطك غير كافية!</b>\nأنت تملك {user_pts} نقطة، والمطلوب {p_pts} نقطة.\nالعَب في قسم الألعاب أو ادعُ أصدقاءك لجمع المزيد من النقاط!")

    # 🎮 2. قسم الألعاب والترفيه
    elif data == "show_games":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🎯 لعبة حدس الرقم (تربح حتى 100 نقطة)", callback_data="game_guess"),
            types.InlineKeyboardButton("🎰 عجلة الحظ اليومية (هدية فورية)", callback_data="game_spin"),
            types.InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_home")
        )
        bot.send_message(user_id, "🎮 <b>مرحباً بك في قسم الألعاب والترفيه!</b>\nالعَب واجمع النقاط واشترِ المنتجات مجاناً:", reply_markup=markup)

    elif data == "game_spin":
        today = str(datetime.date.today())
        conn = sqlite3.connect('nexus.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT last_spin FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        
        if row and row[0] == today:
            bot.send_message(user_id, "⚠️ <b>لقد استخدمت محاولتك اليومية بالفعل!</b> عد غداً للحصول على النقاط مجدداً.")
            conn.close()
        else:
            win_pts = random.choice([10, 20, 30, 50, 100])
            c.execute("UPDATE users SET points = points + ?, last_spin = ? WHERE user_id = ?", (win_pts, today, user_id))
            conn.commit()
            conn.close()
            bot.send_message(user_id, f"🎰 <b>مبروك! لقد أدرت العجلة وحصلت على {win_pts} نقطة مجانية!</b>")

    elif data == "game_guess":
        secret_num = random.randint(1, 5)
        game_states[user_id] = secret_num
        markup = types.InlineKeyboardMarkup(row_width=5)
        btns = [types.InlineKeyboardButton(str(i), callback_data=f"guess_num_{i}") for i in range(1, 6)]
        markup.add(*btns)
        bot.send_message(user_id, "🎯 <b>لقد خمنت رقماً سرياً بين 1 و 5!</b>\nاختر الرقم الصحيح لتربح 30 نقطة:", reply_markup=markup)

    elif data.startswith("guess_num_"):
        guessed = int(data.replace("guess_num_", ""))
        secret = game_states.get(user_id)
        if secret and guessed == secret:
            add_user_points(user_id, 30)
            bot.send_message(user_id, "🎉 <b>إجابة صحيحة! أحسنت، ربحت 30 نقطة مجانية!</b>")
        else:
            bot.send_message(user_id, f"❌ <b>لأسف إجابة خاطئة!</b> الرقم الصحيح كان ({secret}). حاول مرة أخرى لاحقاً!")
        game_states[user_id] = None

    # 🎁 3. نظام الإحالة والدعوات
    elif data == "show_referral":
        ref_link = f"https://t.me/NexusStoreArBot?start={user_id}"
        pts = get_user_points(user_id)
        msg = (
            f"🎁 <b>برنامج كسب النقاط عبر دعوة الأصدقاء:</b>\n\n"
            f"🏆 <b>نقاطك الحالية:</b> {pts} نقطة\n"
            f"⚡ <b>تحصل على 50 نقطة مجانية لكل صديق يدخل البوت عبر رابطك!</b>\n\n"
            f"🔗 <b>رابط الإحالة الخاص بك:</b>\n<code>{ref_link}</code>\n\n"
            "انسخ الرابط وانشره في المجموعات وأصدقائك لجمع النقاط وشراء المنتجات مجاناً!"
        )
        bot.send_message(user_id, msg)

    # 📈 4. جميع روابط تداول العملات الرقمية
    elif data == "show_crypto":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for ex_name, ex_url in CRYPTO_EXCHANGES.items():
            markup.add(types.InlineKeyboardButton(f"🌐 منصة {ex_name}", url=ex_url))
        markup.add(types.InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_home"))

        msg = (
            "📈 <b>منصات وتداول العملات الرقمية المعتمدة:</b>\n\n"
            "يمكنك التسجيل في منصات التداول العالمية الموثوقة أو التحويل المباشر عبر المحفظة:\n\n"
            f"💵 <b>Binance Pay ID:</b> <code>{BINANCE_PAY_ID}</code>\n"
            f"🌐 <b>USDT TRC20:</b> <code>{BINANCE_WALLET_ADDRESS}</code>"
        )
        bot.send_message(user_id, msg, reply_markup=markup)

    # 👑 5. لوحة التحكم والأسعار للمالك
    elif data == "admin_panel" and user_id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("✏️ تعديل سعر منتج", callback_data="admin_edit_price"),
            types.InlineKeyboardButton("➕ إضافة منتج جديد", callback_data="admin_add_prod"),
            types.InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_home")
        )
        bot.send_message(user_id, "👑 <b>لوحة التحكم والأسعار:</b>", reply_markup=markup)

    elif data == "admin_edit_price" and user_id == ADMIN_ID:
        admin_states[ADMIN_ID] = "WAITING_EDIT_PRICE"
        bot.send_message(user_id, "📌 <b>لتعديل سعر منتج أرسل الرسالة بالشكل التالي:</b>\n`معرف_المنتج | السعر_بالجنيه | السعر_بالدولار | السعر_بالنقاط`\n\nمثال:\n`1 | 20000 | 8 | 400`")

    elif data == "admin_add_prod" and user_id == ADMIN_ID:
        admin_states[ADMIN_ID] = "WAITING_NEW_PROD"
        bot.send_message(user_id, "📌 <b>لإضافة منتج أرسل التفاصيل بالصيغة:</b>\n`الاسم | السعر_SDG | السعر_USD | السعر_بالنقاط | الرابط | الوصف`")

    elif data == "back_home":
        start_cmd(call.message)

# ==========================================
# 📥 استقبال الإدخالات والإشعارات
# ==========================================
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.chat.id
    if user_id == ADMIN_ID: return

    rcpt_id = f"{user_id}_{message.message_id}"
    caption = message.caption if message.caption else "إشعار تحويل"

    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    temp_img_path = f"temp_{rcpt_id}.jpg"
    with open(temp_img_path, 'wb') as f: f.write(downloaded_file)

    selected_p = pending_orders.get(user_id)
    p_info = f"المنتج: {selected_p[1]}" if selected_p else "غير محدد"

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ موافقة وتسليم", callback_data=f"appr_rcpt_{rcpt_id}"),
        types.InlineKeyboardButton("❌ رفض", callback_data=f"reje_rcpt_{rcpt_id}")
    )

    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"💳 <b>إشعار جديد:</b>\n👤 من: {user_id}\n📦 {p_info}\n📝 {caption}", reply_markup=markup)
    bot.send_message(user_id, "⏳ <b>تم استلام الإشعار!</b> جاري التأكيد خلال دقيقة واحدة...")

    t = threading.Thread(target=process_receipt_after_timeout, args=(rcpt_id, user_id, caption, temp_img_path))
    t.daemon = True
    t.start()

@bot.message_handler(func=lambda msg: True)
def handle_text(message):
    user_id = message.chat.id
    text = message.text

    if user_id == ADMIN_ID and admin_states.get(ADMIN_ID) == "WAITING_EDIT_PRICE":
        try:
            p_id, p_sdg, p_usd, p_pts = [p.strip() for p in text.split("|")]
            conn = sqlite3.connect('nexus.db', check_same_thread=False)
            conn.cursor().execute("UPDATE products SET price_sdg=?, price_usd=?, price_pts=? WHERE id=?", 
                                  (float(p_sdg), float(p_usd), int(p_pts), int(p_id)))
            conn.commit()
            conn.close()
            admin_states[ADMIN_ID] = None
            bot.send_message(ADMIN_ID, "✅ <b>تم تعديل سعر المنتج بنجاح!</b>")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"⚠️ خطأ بالتنسيق: {e}")

    elif user_id == ADMIN_ID and admin_states.get(ADMIN_ID) == "WAITING_NEW_PROD":
        try:
            name, p_sdg, p_usd, p_pts, link, desc = [p.strip() for p in text.split("|")]
            conn = sqlite3.connect('nexus.db', check_same_thread=False)
            conn.cursor().execute("INSERT INTO products (name, price_sdg, price_usd, price_pts, link, desc) VALUES (?,?,?,?,?,?)", 
                                  (name, float(p_sdg), float(p_usd), int(p_pts), link, desc))
            conn.commit()
            conn.close()
            admin_states[ADMIN_ID] = None
            bot.send_message(ADMIN_ID, "✅ <b>تم إضافة المنتج الجديد بنجاح!</b>")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"⚠️ خطأ بالتنسيق: {e}")

    elif user_id != ADMIN_ID:
        rcpt_id = f"{user_id}_{message.message_id}"
        selected_p = pending_orders.get(user_id)
        p_info = f"المنتج: {selected_p[1]}" if selected_p else "غير محدد"

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ موافقة وتسليم", callback_data=f"appr_rcpt_{rcpt_id}"),
            types.InlineKeyboardButton("❌ رفض", callback_data=f"reje_rcpt_{rcpt_id}")
        )

        bot.send_message(ADMIN_ID, f"🔔 <b>إشعار نصي جديد:</b>\n👤 من: <code>{user_id}</code>\n📦 {p_info}\n💬 {text}", reply_markup=markup)
        bot.send_message(user_id, "⏳ <b>تم استلام النص!</b> جاري التأكيد خلال دقيقة واحدة...")

        t = threading.Thread(target=process_receipt_after_timeout, args=(rcpt_id, user_id, text, None))
        t.daemon = True
        t.start()

if __name__ == "__main__":
    keep_alive()
    print("🚀 Nexus Store Master Engine Active...")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            time.sleep(2)
