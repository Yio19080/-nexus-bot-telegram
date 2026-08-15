import os
import urllib.parse
import sqlite3
import requests
import telebot
from telebot import types
import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ==========================================
# 🔑 الإعدادات والمفاتيح (تم تحديث التوكن)
# ==========================================
TELEGRAM_TOKEN = "8617844634:AAGfD4f-dpgmpPn2Zo0ZPdaGq09Vvm7cL18"
GEMINI_KEY = os.getenv("GEMINI_KEY", "YOUR_GEMINI_API_KEY")
YOUR_USERNAME = os.getenv("YOUR_USERNAME", "@YOUR_USERNAME")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@YOUR_CHANNEL_USERNAME")

ADMIN_ID = 7899998427

if GEMINI_KEY and GEMINI_KEY != "YOUR_GEMINI_API_KEY":
    genai.configure(api_key=GEMINI_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')

bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")

# ==========================================
# 🗄️ قاعدة البيانات (SQLite Storage)
# ==========================================
def init_db():
    conn = sqlite3.connect('nexus_store.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            user_id INTEGER,
            item_name TEXT,
            deliver TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_order(order_id, user_id, item_name, deliver):
    conn = sqlite3.connect('nexus_store.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO orders VALUES (?, ?, ?, ?, 'PENDING')",
        (order_id, user_id, item_name, deliver)
    )
    conn.commit()
    conn.close()

def get_order(order_id):
    conn = sqlite3.connect('nexus_store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, item_name, deliver FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"user_id": row[0], "item_name": row[1], "deliver": row[2]}
    return None

init_db()

# ==========================================
# 🌐 بيانات متجر Nexus Store
# ==========================================
REVIEWS_CHANNEL_URL = "https://t.me/NexusStoreAr"
VIP_CHANNEL_URL = "https://t.me/NexusStoreAr"
TRADING_COURSE_URL = "https://t.me/NexusStoreAr"
PYTHON_COURSE_URL = "https://t.me/NexusStoreAr"
UNIVERSITY_NOTES_URL = "https://t.me/NexusStoreAr"

PAYMENT_INFO = {
    "sdg": (
        "🏦 <b>الدفع بالجنيه السوداني (بنكك):</b>\n"
        "• رقم الحساب: <code>9412190</code>\n"
        "• الاسم: <b>يوسف إبراهيم الطيب عبد القادر</b>"
    ),
    "crypto": (
        "🪙 <b>الدفع بالدولار / USDT (Binance):</b>\n"
        "• المحفظة (ERC20/TRC20):\n<code>0x6742c39cb07b9fd6a69281dc4b9b96239cc7850a</code>\n"
        "• الاسم: <b>يوسف إبراهيم الطيب عبد القادر</b>"
    )
}

CATALOG = {
    "design": {
        "title": "🎨 خدمات تصميم الصور والفيديوهات بالذكاء الاصطناعي",
        "items": {
            "ds1": {
                "name": "🖼️ تصميم صورة احترافية بالذكاء الاصطناعي", 
                "price_usd": 3.0, 
                "price_sdg": 7500, 
                "desc": "توليد صورة عالية الدقة بناءً على وصفك مع روابط إعداد جودة فائقة.", 
                "deliver": f"🎨 <b>أرسل وصف صورتك المفضل للدعم الفني لتوليدها فوراً:</b> {YOUR_USERNAME}"
            },
            "ds2": {
                "name": "🎬 تصميم فيديو تسويقي بالذكاء الاصطناعي", 
                "price_usd": 10.0, 
                "price_sdg": 25000, 
                "desc": "إنشاء مشهد فيديو تسويقي سينمائي متكامل مع كود Prompt مخصص.", 
                "deliver": f"🎬 <b>أرسل تفاصيل وموضوع الفيديو للدعم الفني للبدء في تنفيذه:</b> {YOUR_USERNAME}"
            }
        }
    },
    "crypto": {
        "title": "🪙 عالم العملات الرقمية والتداول",
        "items": {
            "cr1": {"name": "📈 اشتراك VIP القناة الخاصة للتوصيات (شهر)", "price_usd": 30.0, "price_sdg": 75000, "desc": "توصيات يومية فائقة الدقة مع متابعة لحظية وإدارات مخاطر.", "deliver": f"🔗 <b>رابط الانضمام للقناة الخاصة:</b> {VIP_CHANNEL_URL}"},
            "cr2": {"name": "🎓 دورة احتراف التداول والتحليل الفني", "price_usd": 50.0, "price_sdg": 125000, "desc": "شرح شامل من الأساسيات إلى الاحتراف وتحديد المناطق القوية.", "deliver": f"📚 <b>رابط الدورة الشاملة:</b> {TRADING_COURSE_URL}"},
            "cr3": {"name": "💳 شحن/شراء USDT ومحافظ رقمية", "price_usd": 10.0, "price_sdg": 25000, "desc": "خدمة شراء وتبديل رصيد USDT فورية بأمان تام.", "deliver": f"💬 <b>شحن USDT:</b> تواصل فوراً مع الدعم: {YOUR_USERNAME}"},
            "cr4": {"name": "🔍 استشارة وتقييم محفظة استثمارية", "price_usd": 15.0, "price_sdg": 37500, "desc": "جلسة تحليل وتوزيع مخاطر خاصة لمحفظتك الاستثمارية.", "deliver": f"📅 <b>الاستشارة:</b> تواصل مع المحلل مباشرة: {YOUR_USERNAME}"}
        }
    },
    "cv": {
        "title": "📄 خدمات السيرة الذاتية (CV)",
        "items": {
            "cv1": {"name": "📝 تصميم CV احترافي (ATS Compliant)", "price_usd": 10.0, "price_sdg": 25000, "desc": "سيرة ذاتية متوافقة مع خوارزميات الفرز الآلي للشركات.", "deliver": f"📄 <b>طلب CV:</b> أرسل بياناتك للدعم: {YOUR_USERNAME}"},
            "cv2": {"name": "🌐 إنشاء وتحسين حساب LinkedIn", "price_usd": 15.0, "price_sdg": 37500, "desc": "تنسيق ملف احترافي يجذب مسؤولي التوظيف والشركات.", "deliver": f"🌐 <b>تحسين LinkedIn:</b> أرسل رابط حسابك للدعم: {YOUR_USERNAME}"}
        }
    },
    "courses": {
        "title": "📚 الدروس والمحاضرات التعليمية",
        "items": {
            "c1": {"name": "🎓 كورس البرمجة بلغة Python من الصفر", "price_usd": 20.0, "price_sdg": 50000, "desc": "محاضرات مسجلة مع تطبيقات عملية وبناء مشاريع حقيقية.", "deliver": f"🎓 <b>رابط كورس البايثون:</b> {PYTHON_COURSE_URL}"},
            "c2": {"name": "📊 ملخصات ومذكرة جامعية شاملة", "price_usd": 5.0, "price_sdg": 12500, "desc": "حقيبة تعليمية متكاملة تشمل أهم المذكرات والملخصات.", "deliver": f"📂 <b>رابط الحقيبة التعليمية:</b> {UNIVERSITY_NOTES_URL}"}
        }
    },
    "ads": {
        "title": "📢 الإعلانات والرعايات للشركات",
        "items": {
            "a1": {"name": "📣 إعلان فردي مميز لمستخدمي البوت", "price_usd": 15.0, "price_sdg": 37500, "desc": "وصول مباشر لجمهور مهتم بالخدمات الرقمية والتداول.", "deliver": f"📢 <b>حجز إعلان:</b> أرسل محتوى إعلانك إلى: {YOUR_USERNAME}"},
            "a2": {"name": "🌟 بنر إعلاني مثبت داخل البوت (أسبوع)", "price_usd": 35.0, "price_sdg": 87500, "desc": "تثبيت إعلانك في الواجهة الرئيسية لأعلى نسبة مشاهدة.", "deliver": f"🌟 <b>حجز بنر:</b> أرسل التصاميم والرابط إلى: {YOUR_USERNAME}"}
        }
    }
}

user_states = {}
ai_user_mode = {}

# ==========================================
# 🛠️ أدوات مساعدة ونظام الإقناع بالذكاء الاصطناعي
# ==========================================
def generate_persuasive_pitch(service_type, user_text, user_language_code="ar"):
    prompt = f"""
    أنت مستشار مبيعات خبير وودود جداً في متجر Nexus Store.
    طلب العميل يتعلق بـ: ({service_type}).
    النص/الفكرة التي أرسلها العميل: "{user_text}".
    رمز لغة العميل: "{user_language_code}".

    المهام المطلوبة منك:
    1. اكتشف لغة العميل وأجبه بالنفس اللغـة فوراً (سواء كانت عربية، إنجليزية، فرنسية، إلخ).
    2. تحدث بأسلوب راقي، جذاب، مفعم بالحماس، ويظهر الفائدة القوية والتأثير الإيجابي الذي سيحصل عليه العميل عند شراء هذه الخدمة المصممة له بالذكاء الاصطناعي.
    3. وضح له كيف أن الاستثمار في هذه الخدمة بسعر بسيط جداً سيوفر عليه وقتاً وجهداً ويعطيه نتائج سينمائية/احترافية فائقة الجودة.
    4. اختم حديثك بدعوته بلباقة للشراء واختيار الخدمة من القائمة.
    5. حافظ على إيجاز الرسالة وجمال تنسيقها (استخدم إيموجي مناسبة وبدون تكلف).
    """
    try:
        response = ai_model.generate_content(prompt)
        return response.text
    except Exception:
        return (
            "✨ <b>تصميم استثنائي بانتظارك!</b>\n\n"
            "نحرمك من عناء التصميم والتعقيد لنمنحك نتائج سينمائية احترافية تجذب الأنظار وتخدم أهدافك بدقة متناهية.\n\n"
            "🌟 استثمر في حضورك الرقمي الآن واحصل على تصميم فريد ومخصص لك تماماً!"
        )

def create_cv_pdf(name, data, filename):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 50, f"Curriculum Vitae - {name}")
    c.setLineWidth(1)
    c.line(50, height - 60, width - 50, height - 60)

    text = c.beginText(50, height - 90)
    text.setFont("Helvetica", 10)
    text.setLeading(14)

    for line in data.split('\n'):
        if len(line.strip()) > 80:
            words = line.split(' ')
            current_line = ""
            for word in words:
                if len(current_line + word) < 80:
                    current_line += word + " "
                else:
                    text.textLine(current_line)
                    current_line = word + " "
            if current_line:
                text.textLine(current_line)
        else:
            text.textLine(line)

    c.drawText(text)
    c.save()

def process_ai_request(message, command, user_input):
    user_id = message.chat.id
    bot.send_message(user_id, "🧠 <b>جاري صياغة إجابتك بأعلى جودة بوساطة الذكاء الاصطناعي...</b>")

    prompts = {
        'cv': f"انت خبير موارد بشرية HR. اكتب سيرة ذاتية احترافية ومكتملة بالبيانات التالية: {user_input}. رتبها بعناوين: Summary, Experience, Skills, Education",
        'content': f"انت مسوق محترف. اكتب 10 افكار محتوى + كابشنات تسويقية جذابة للموضوع: {user_input}",
        'translate': f"ترجم النص التالي بدقة عالية بين العربية والإنجليزي:\n{user_input}",
        'summarize': f"لخص النص التالي في نقاط رئيسية مركزة ومفصلة:\n{user_input}",
        'code': f"اكتب كود بايثون كامل ونظيف مع شرح لآلية عمله للطلب التالي:\n{user_input}",
        'analyze': f"انت محلل بيانات خبير. حلل البيانات التالية واستخرج منها أرقاماً واستنتاجات دقيقة:\n{user_input}"
    }

    try:
        response = ai_model.generate_content(prompts[command])
        if command == 'cv':
            filename = f"cv_{user_id}.pdf"
            first_name = message.from_user.first_name or "User"
            create_cv_pdf(first_name, response.text, filename)
            with open(filename, 'rb') as pdf:
                bot.send_document(user_id, pdf, caption="✨ <b>تم إنشاء سيرتك الذاتية بنجاح واحترافية عالية!</b>")
            os.remove(filename)
        else:
            bot.reply_to(message, response.text)
    except Exception:
        bot.send_message(user_id, "❌ <b>عذراً، حدث خطأ مؤقت أثناء معالجة الطلب. يرجى إعادة المحاولة لاحقاً.</b>")

# ==========================================
# 🎯 إقناع العميل بالشراء عند استخدام أوامر التصميم
# ==========================================
@bot.message_handler(commands=['صمم_صورة', 'صورة', 'صمم_فيديو', 'فيديو'])
def handle_design_sales_pitch(message):
    user_id = message.chat.id
    lang_code = message.from_user.language_code or "ar"
    user_text = message.text

    service_type = "تصميم صورة احترافية" if "صورة" in message.text else "تصميم فيديو تسويقي"
    
    bot.send_chat_action(user_id, 'typing')
    pitch = generate_persuasive_pitch(service_type, user_text, lang_code)

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🛒 اطلب الخدمة الآن وإبدأ الفخامة", callback_data="cat_design"),
        types.InlineKeyboardButton("💬 الاستفسار مع الدعم الفني", callback_data="support")
    )

    bot.reply_to(message, pitch, reply_markup=markup)

@bot.message_handler(commands=['سعر', 'price'])
def crypto_price_cmd(message):
    args = message.text.split()
    coin_id = args[1].lower() if len(args) > 1 else "bitcoin"
    
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()

        if coin_id in data:
            price = data[coin_id]['usd']
            msg = (
                f"🪙 <b>السعر الحالي لعملة ({coin_id.capitalize()}):</b> <code>${price:,} USD</code>\n\n"
                "📊 <b>منصات موثوقة لشراء وتداول العملة مباشرة:</b>\n"
                f"• <a href='https://www.binance.com/ar/trade/{coin_id.upper()}_USDT'>Binance Exchange</a>\n"
                f"• <a href='https://www.bybit.com/trade/usdt/{coin_id.upper()}'>Bybit Exchange</a>\n"
                f"• <a href='https://www.okx.com/trade-spot/{coin_id}-usdt'>OKX Exchange</a>"
            )
        else:
            msg = f"❌ لم نتمكن من إيجاد العملة <code>{coin_id}</code>. يرجى التأكد من الاسم بالإنجليزية (مثال: bitcoin, ethereum)."
    except requests.exceptions.RequestException:
        msg = "⚠️ <b>تعذر جلب السعر حالياً نتيجة لضغط الخادم. يرجى المحاولة بعد قليل.</b>"
        
    bot.reply_to(message, msg, disable_web_page_preview=True)

@bot.message_handler(commands=['درس_التداول', 'درس'])
def trading_lesson_cmd(message):
    lesson_topic = message.text.replace('/درس_التداول', '').replace('/درس', '').strip()
    if not lesson_topic:
        lesson_topic = "أساسيات التداول والتحليل الفني"

    query_encoded = urllib.parse.quote(f"شرح {lesson_topic}")
    yt_search_url = f"https://www.youtube.com/results?search_query={query_encoded}"

    msg = (
        f"📚 <b>دليل تعليمي: {lesson_topic}</b>\n\n"
        "النجاح في التداول يعتمد على الانضباط وإدارة المخاطر وتحديد نقاط الدخول والخروج بدقة.\n\n"
        "🎥 <b>مصادر وفيديوهات تعليمية مجانية على YouTube:</b>\n"
        f"1️⃣ <a href='{yt_search_url}'>شروحات شاملة لـ {lesson_topic}</a>\n"
        f"2️⃣ <a href='https://www.youtube.com/results?search_query={urllib.parse.quote('إدارة المخاطر في التداول')}'>قواعد إدارة رأس المال والمخاطر</a>\n"
        f"3️⃣ <a href='https://www.youtube.com/results?search_query={urllib.parse.quote('شرح الشموع اليابانية')}'>استراتيجيات قراءة الشموع اليابانية</a>"
    )
    bot.reply_to(message, msg, disable_web_page_preview=True)

@bot.message_handler(commands=['انشر'])
def publish_to_channel(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "🚫 هذا الأمر مخصص للإدارة فقط.")
        return

    content = message.text.replace('/انشر', '').strip()
    if not content:
        bot.reply_to(message, "⚠️ يرجى إضافة نص منشورك.\nمثال: <code>/انشر مرحباً بكم في متجرنا</code>")
        return

    try:
        bot.send_message(CHANNEL_ID, content)
        bot.reply_to(message, "✅ <b>تم نشر منشورك بنجاح في القناة الرسمية!</b>")
    except Exception:
        bot.reply_to(message, f"❌ تعذر النشر في القناة. تأكد من إضافة البوت كـ Admin ورفعه بصلاحية النشر.")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "🚫 غير مسموح لك بالوصول.")
        return

    msg = (
        "⚙️ <b>لوحة التحكم والإدارة:</b>\n\n"
        "• <code>/انشر [النص]</code> - لإرسال منشور مباشر إلى القناة.\n"
        "• جميع إشعارات الدفع والطلبات يتم مراجعتها وتأكيدها أوتوماتيكياً."
    )
    bot.reply_to(message, msg)

# ==========================================
# 🚀 القوائم والتفاعل الرئيسي
# ==========================================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.chat.id
    ai_user_mode.pop(user_id, None)

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎨 خدمات التصميم بالذكاء الاصطناعي (VIP)", callback_data="cat_design"),
        types.InlineKeyboardButton("🪙 عالم العملات الرقمية والتداول", callback_data="cat_crypto"),
        types.InlineKeyboardButton("📄 خدمات السيرة الذاتية الاحترافية (CV)", callback_data="cat_cv"),
        types.InlineKeyboardButton("📚 الدورات والحلول التعليمية", callback_data="cat_courses"),
        types.InlineKeyboardButton("📢 الإعلانات ورعايات الأعمال", callback_data="cat_ads"),
        types.InlineKeyboardButton("🤖 أدوات الذكاء الاصطناعي (Nexus AI)", callback_data="ai_tools"),
        types.InlineKeyboardButton("🛡️ آراء وتقييمات العملاء", url=REVIEWS_CHANNEL_URL),
        types.InlineKeyboardButton("💬 الدعم الفني والاستفسارات", callback_data="support")
    )

    first_name = message.from_user.first_name if message.from_user.first_name else "عزيزنا العميل"
    welcome_text = (
        f"أهلاً وسهلاً بك يا <b>{first_name}</b> في <b>Nexus Store | متجر نكسس</b>! 🌟\n\n"
        "يسعدنا تقديم أفضل الخدمات الرقمية وحلول الذكاء الاصطناعي بأعلى معايير السرعة والأمان.\n\n"
        "👇 <b>اختر الخدمة المطلوبة من القائمة أدناه للبدء فوراً:</b>"
    )
    bot.send_message(user_id, welcome_text, reply_markup=markup, disable_web_page_preview=True)

@bot.message_handler(commands=['cv', 'content', 'translate', 'summarize', 'code', 'analyze'])
def handle_ai_commands(message):
    user_id = message.chat.id
    command = message.text.split()[0].replace('/', '')
    user_input = message.text.replace(f"/{command}", "").strip()

    if not user_input:
        ai_user_mode[user_id] = command
        instructions = {
            'cv': "يرجى إرسال بياناتك (الاسم، الخبرات، المهارات، والمستوى التعليمي):",
            'content': "يرجى إرسال فكرة أو موضوع المحتوى المراد صياغته:",
            'translate': "يرجى إرسال النص المراد ترجمته بدقة:",
            'summarize': "يرجى إرسال المقال أو النص المراد تلخيصه:",
            'code': "يرجى إرسال متطلبات البرمجية المطلوبة بـ Python:",
            'analyze': "يرجى إرسال البيانات أو الأرقام المراد تحليلها:"
        }
        bot.reply_to(message, f"📥 <b>أهلاً بك!</b>\n{instructions.get(command, 'أرسل مدخلاتك الآن:')}")
    else:
        process_ai_request(message, command, user_input)

# ==========================================
# 🔘 معالجة الأزرار والطلبات
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.message.chat.id
    data = call.data

    if data == "main_menu":
        start_cmd(call.message)

    elif data == "ai_tools":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📝 إنشاء CV احترافي", callback_data="aismart_cv"),
            types.InlineKeyboardButton("📢 صياغة محتوى", callback_data="aismart_content"),
            types.InlineKeyboardButton("🌐 ترجمة فورية", callback_data="aismart_translate"),
            types.InlineKeyboardButton("📑 تلخيص نصوص", callback_data="aismart_summarize"),
            types.InlineKeyboardButton("💻 كتابة أكواد", callback_data="aismart_code"),
            types.InlineKeyboardButton("📊 تحليل بيانات", callback_data="aismart_analyze"),
            types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")
        )
        msg_text = (
            "🤖 <b>أدوات الذكاء الاصطناعي (Nexus AI):</b>\n\n"
            "اختر الخيار المناسب أو استخدم الأوامر مباشرة:\n"
            "• <code>/cv</code> - إنشاء سيرة ذاتية PDF\n"
            "• <code>/content</code> - كتابة محتوى إعلاني\n"
            "• <code>/translate</code> - ترجمة نصوص\n"
            "• <code>/summarize</code> - تلخيص نصوص ومقالات\n"
            "• <code>/code</code> - كتابة أكواد برمجية\n"
            "• <code>/analyze</code> - تحليل بيانات\n"
            "• <code>/سعر bitcoin</code> - أسعار العملات الرقمية\n"
            "• <code>/درس_التداول</code> - شروحات دروس التداول"
        )
        bot.edit_message_text(msg_text, user_id, call.message.message_id, reply_markup=markup)

    elif data.startswith("aismart_"):
        cmd = data.split("_")[1]
        ai_user_mode[user_id] = cmd
        bot.send_message(user_id, f"📥 <b>تم تفعيل الوضع (/{cmd}) بنجاح!</b>\nيرجى تفضل إرسال النص أو البيانات الآن:")

    elif data.startswith("cat_"):
        cat_key = data.split("_")[1]
        category = CATALOG.get(cat_key)

        if category:
            markup = types.InlineKeyboardMarkup(row_width=1)
            for item_id, item in category["items"].items():
                btn_text = f"{item['name']} | ({item['price_usd']}$ / {item['price_sdg']} ج.س)"
                markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"item_{cat_key}_{item_id}"))

            markup.add(
                types.InlineKeyboardButton("🛡️ آراء وتقييمات العملاء", url=REVIEWS_CHANNEL_URL),
                types.InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")
            )
            bot.edit_message_text(f"<b>{category['title']}</b>\nاختر الخدمة أو المنتج المطلوب:", user_id, call.message.message_id, reply_markup=markup)

    elif data.startswith("item_"):
        _, cat_key, item_id = data.split("_")
        item = CATALOG[cat_key]["items"][item_id]

        user_states[user_id] = {
            "item_name": item['name'],
            "usd": item['price_usd'],
            "sdg": item['price_sdg'],
            "deliver": item['deliver']
        }

        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🏦 الدفع بالجنيه السوداني (بنكك)", callback_data="pay_sdg"),
            types.InlineKeyboardButton("🪙 الدفع بالدولار (USDT)", callback_data="pay_crypto"),
            types.InlineKeyboardButton("🛡️ آراء وتقييمات العملاء", url=REVIEWS_CHANNEL_URL),
            types.InlineKeyboardButton("🔙 العودة للقسم", callback_data=f"cat_{cat_key}")
        )

        desc_text = (
            f"🎯 <b>الخدمة المختارة:</b> {item['name']}\n\n"
            f"📝 <b>المميزات والتفاصيل:</b> {item['desc']}\n\n"
            f"💰 <b>السعر:</b> <code>{item['price_usd']}$</code> أو <code>{item['price_sdg']} جنيه سوداني</code>\n\n"
            "يرجى اختيار طريقة الدفع المفضل لديك:"
        )
        bot.edit_message_text(desc_text, user_id, call.message.message_id, reply_markup=markup)

    elif data.startswith("pay_"):
        method = data.split("_")[1]
        state = user_states.get(user_id)

        if not state:
            bot.send_message(user_id, "⚠️ انتهت الجلسة الحالية، يرجى إعادة البدء عبر /start")
            return

        pay_info = PAYMENT_INFO.get(method, "")
        user_states[user_id]["pay_method"] = method
        user_states[user_id]["waiting_for_proof"] = True

        msg = (
            f"💳 <b>بيانات تحويل المبلغ لـ ({state['item_name']}):</b>\n\n"
            f"{pay_info}\n\n"
            "⚠️ <b>خطوات إكمال الطلب بنجاح:</b>\n"
            "1. قم بتحويل المبلغ المحدد.\n"
            "2. <b>قم بإرسال صورة إشعار التحويل</b> في هذه المحادثة مباشرة.\n"
            "3. سيقوم النظام بمراجعة الدفع وتسليمك المنتج تلقائياً!"
        )
        bot.send_message(user_id, msg, disable_web_page_preview=True)

    elif data.startswith("approve_"):
        order_id = data.replace("approve_", "")
        order = get_order(order_id)

        if order:
            delivery_text = (
                f"🎉 <b>تم تأكيد إشعار الدفع بنجاح! شكراً لثقتك بنا.</b>\n\n"
                f"📦 <b>تفاصيل وتسليم طلبك ({order['item_name']}):</b>\n"
                f"{order['deliver']}\n\n"
                f"يسعدنا جداً تقييمك وتجربتك في قناة التوثيقات:\n{REVIEWS_CHANNEL_URL}"
            )
            bot.send_message(order['user_id'], delivery_text, disable_web_page_preview=True)
            bot.edit_message_caption(f"✅ <b>تم تأكيد الطلب وتسليمه للعميل!</b>\nالعميل: <code>{order['user_id']}</code>", ADMIN_ID, call.message.message_id)

    elif data.startswith("reject_"):
        order_id = data.replace("reject_", "")
        order = get_order(order_id)

        if order:
            bot.send_message(order['user_id'], f"❌ <b>عذراً، لم نتمكن من التأكد من التحويل.</b>\nيرجى التأكد من البيانات أو التواصل مع الدعم: {YOUR_USERNAME}")
            bot.edit_message_caption(f"🔴 <b>تم رفض الطلب.</b>\nالعميل: <code>{order['user_id']}</code>", ADMIN_ID, call.message.message_id)

    elif data == "support":
        bot.send_message(user_id, f"💬 <b>فريق الدعم الفني في خدمتك دائماً:</b>\nلأي استفسار أو مساعدة تواصل معنا مباشرة عبر: {YOUR_USERNAME}")

# ==========================================
# 📥 معالجة الرسائل والإشعارات
# ==========================================
@bot.message_handler(func=lambda msg: msg.content_type == 'text' and not msg.text.startswith('/'))
def handle_text_messages(message):
    user_id = message.chat.id
    mode = ai_user_mode.get(user_id)

    if mode:
        process_ai_request(message, mode, message.text)
        ai_user_mode.pop(user_id, None)
    else:
        bot.send_message(user_id, "💡 <b>لاستكشاف الخدمات والأدوات، تفضل باستعراض القائمة الرئيسية عبر /start</b>")

@bot.message_handler(content_types=['photo'])
def handle_payment_proof(message):
    user_id = message.chat.id
    state = user_states.get(user_id)

    if state and state.get("waiting_for_proof"):
        photo_id = message.photo[-1].file_id
        order_id = f"{user_id}_{message.message_id}"

        save_order(order_id, user_id, state['item_name'], state['deliver'])

        bot.send_message(
            user_id,
            "✅ <b>وصلنا إشعار التحويل الخاص بك بنجاح!</b>\n"
            "جاري التأكد فوراً، وسيتم تسليمك طلبك مباشرة بمجرد الاعتماد."
        )

        admin_markup = types.InlineKeyboardMarkup(row_width=1)
        admin_markup.add(
            types.InlineKeyboardButton("🟢 تأكيد الدفع وتسليم الخدمة تلقائياً", callback_data=f"approve_{order_id}"),
            types.InlineKeyboardButton("🔴 رفض الطلب", callback_data=f"reject_{order_id}")
        )

        username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد"
        first_name = message.from_user.first_name if message.from_user.first_name else "عميل"

        admin_msg = (
            f"📥 <b>إشعار دفع جديد قيد المراجعة!</b>\n\n"
            f"👤 <b>العميل:</b> {first_name} ({username})\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f"📦 <b>الطلب:</b> {state['item_name']}\n"
            f"💳 <b>طريقة الدفع:</b> {state['pay_method']}\n\n"
            "👇 <b>اتخذ إجراًء بشأن الطلب:</b>"
        )

        bot.send_photo(ADMIN_ID, photo_id, caption=admin_msg, reply_markup=admin_markup)
        user_states[user_id] = None
    else:
        bot.send_message(user_id, "💡 <b>طلب جديد؟ تفضل باستعراض الخدمات المتاحة عبر /start</b>")

# ==========================================
# ⚡ تشغيل البوت
# ==========================================
if __name__ == "__main__":
    print("🚀 Nexus Store AI Bot - يعمل بنجاح...")
    bot.infinity_polling()


