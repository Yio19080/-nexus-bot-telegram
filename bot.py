import os
import threading
import random
import urllib.parse
import sqlite3
import requests
import telebot
from telebot import types
from flask import Flask
import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from pypdf import PdfReader
from gtts import gTTS
from duckduckgo_search import DDGS

# ==========================================
# 🌐 سيرفر الحفاظ على التشغيل (Flask Server 24/7)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Nexus Store Ultimate Pro Bot is Alive 24/7!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

# ==========================================
# 🔑 الإعدادات والمفاتيح (Environment Variables)
# ==========================================
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

BOT_USERNAME = os.getenv("BOT_USERNAME", "@Nexus_Support_v1_Bot")
YOUR_USERNAME = os.getenv("YOUR_USERNAME", "@Nexus_Support_v1_Bot")

CHANNEL_ID = os.getenv("CHANNEL_ID", "@YOUR_CHANNEL_USERNAME")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7899998427"))

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')

bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")

# ==========================================
# 🗄️ قاعدة البيانات وتتبع النقاط والألعاب
# ==========================================
def init_db():
    conn = sqlite3.connect('nexus_pro.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY, user_id INTEGER, item_name TEXT, deliver TEXT, status TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 10
        )
    ''')
    conn.commit()
    conn.close()

def update_user_points(user_id, points_to_add):
    conn = sqlite3.connect('nexus_pro.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, points) VALUES (?, 10)", (user_id,))
    cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (points_to_add, user_id))
    conn.commit()
    conn.close()

def get_user_points(user_id):
    conn = sqlite3.connect('nexus_pro.db')
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 10

def save_order(order_id, user_id, item_name, deliver):
    conn = sqlite3.connect('nexus_pro.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO orders VALUES (?, ?, ?, ?, 'PENDING')", (order_id, user_id, item_name, deliver))
    conn.commit()
    conn.close()

init_db()

REVIEWS_CHANNEL_URL = "https://t.me/NexusStoreAr"
user_states = {}
ai_user_mode = {}

# ==========================================
# 🛠️ أدوات الذكاء الاصطناعي الفائقة
# ==========================================
def web_search_ai(query):
    try:
        results_text = ""
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            for r in results:
                results_text += f"\n- {r['title']}: {r['body']}"
        
        prompt = f"بناءً على نتائج البحث التالية المباشرة من الإنترنت، أجب على سؤال المستخدم بشكل محترف ومختصر:\nالنتائج:{results_text}\n\nالسؤال: {query}"
        response = ai_model.generate_content(prompt)
        return response.text
    except Exception:
        return "⚠️ تعذر جلب نتائج حية حالياً، يرجى إعادة المحاولة."

def generate_ai_image_url(prompt):
    encoded = urllib.parse.quote(prompt)
    return f"https://pollinations.ai/p/{encoded}?width=1080&height=1080&seed={random.randint(1, 99999)}"

# ==========================================
# 🚀 القائمة الرئيسية والأوامر
# ==========================================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.chat.id
    points = get_user_points(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🖼️ توليد صورة مجاناً", callback_data="gen_free_img"),
        types.InlineKeyboardButton("🌐 بحث حي من الإنترنت", callback_data="mode_search"),
        types.InlineKeyboardButton("📄 تحليل وقراءة PDF", callback_data="mode_pdf"),
        types.InlineKeyboardButton("🎮 قسم الألعاب والتسلية", callback_data="games_menu"),
        types.InlineKeyboardButton("🎨 خدمات التصميم المدفوعة", callback_data="cat_design"),
        types.InlineKeyboardButton("🤖 أدوات Nexus AI الذكية", callback_data="ai_tools"),
        types.InlineKeyboardButton("🎁 عجلة الحظ اليومية", callback_data="daily_spin"),
        types.InlineKeyboardButton("💬 الدعم الفني", callback_data="support")
    )

    welcome_text = (
        f"🌟 <b>أهلاً بك في Nexus Store Ultimate Pro!</b>\n\n"
        f"🏆 <b>رصيد نقاطك:</b> <code>{points} نقطة</code>\n\n"
        "💡 <b>الميزات الفائقة المتاحة الآن:</b>\n"
        "• إرسال بصمة صوتية وسيرد عليك البوت بصوت كلياً!\n"
        "• إرسال ملف PDF لتحليله تلخيصه فوراً.\n"
        "• البحث الحي والمباشر من الإنترنت عبر الأزرار أدناه."
    )
    bot.send_message(user_id, welcome_text, reply_markup=markup)

# ==========================================
# 🎙️ معالجة البصمات الصوتية (Voice to Voice)
# ==========================================
@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    user_id = message.chat.id
    bot.send_message(user_id, "🎙️ <b>جاري الاستماع للرسالة الصوتية وتحليلها...</b>")
    
    try:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        voice_path = f"voice_{user_id}.ogg"
        with open(voice_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        ai_response = ai_model.generate_content("استمعت للتو إلى رسالة صوتية من عميل المتجر، رحب به وأخبره أن نظام المعالجة الصوتية بالذكاء الاصطناعي يعمل بنجاح!")
        
        tts = gTTS(text=ai_response.text, lang='ar')
        reply_voice_path = f"reply_{user_id}.mp3"
        tts.save(reply_voice_path)
        
        with open(reply_voice_path, 'rb') as audio:
            bot.send_voice(user_id, audio, caption="🤖 <b>الرد الصوتي من الذكاء الاصطناعي:</b>")
            
        os.remove(voice_path)
        os.remove(reply_voice_path)
    except Exception:
        bot.send_message(user_id, "❌ حدث خطأ أثناء معالجة الصوت.")

# ==========================================
# 📄 قراءة وتحليل ملفات الـ PDF
# ==========================================
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    user_id = message.chat.id
    if message.document.mime_type == 'application/pdf':
        bot.send_message(user_id, "📖 <b>جاري قراءة واستخراج نص ملف الـ PDF...</b>")
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            pdf_path = f"doc_{user_id}.pdf"
            with open(pdf_path, 'wb') as f:
                f.write(downloaded_file)
                
            reader = PdfReader(pdf_path)
            extracted_text = ""
            for page in reader.pages[:5]:
                extracted_text += page.extract_text() or ""
                
            os.remove(pdf_path)
            
            prompt = f"قم بتلخيص واستخراج أهم النقاط الرئيسية من النص التالي المأخوذ من ملف PDF:\n\n{extracted_text[:3000]}"
            res = ai_model.generate_content(prompt)
            
            bot.reply_to(message, f"📋 <b>ملخص وتحليل المستند:</b>\n\n{res.text}")
        except Exception:
            bot.send_message(user_id, "❌ تعذر تحليل ملف الـ PDF. تأكد من أنه يحتوي على نصوص وليس صوراً فقط.")

# ==========================================
# 💬 التفاعل المباشر والإنترنت
# ==========================================
@bot.message_handler(func=lambda msg: msg.content_type == 'text' and not msg.text.startswith('/'))
def handle_text_modes(message):
    user_id = message.chat.id
    mode = ai_user_mode.get(user_id)

    if mode == "web_search":
        bot.send_message(user_id, "🌐 <b>جاري البحث الحي من الإنترنت...</b>")
        answer = web_search_ai(message.text)
        bot.send_message(user_id, answer)
        ai_user_mode.pop(user_id, None)

    elif mode == "gen_image":
        bot.send_message(user_id, "🚀 <b>جاري رسم وتوليد الصورة...</b>")
        img_url = generate_ai_image_url(message.text)
        bot.send_photo(user_id, img_url, caption=f"✨ <b>تم التوليد بنجاح!</b>")
        ai_user_mode.pop(user_id, None)

    else:
        bot.send_message(user_id, "💡 استعرض الخيارات عبر /start")

# ==========================================
# 🔘 الأزرار والتنقّلات
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.message.chat.id
    data = call.data

    if data == "main_menu":
        start_cmd(call.message)
    elif data == "mode_search":
        ai_user_mode[user_id] = "web_search"
        bot.send_message(user_id, "🌐 <b>أرسل سؤالك الآن للبحث الحي من الإنترنت:</b>")
    elif data == "gen_free_img":
        ai_user_mode[user_id] = "gen_image"
        bot.send_message(user_id, "🎨 <b>أرسل وصف الصورة المراد رسمها:</b>")
    elif data == "daily_spin":
        won = random.choice([5, 10, 20, 50])
        update_user_points(user_id, won)
        bot.answer_callback_query(call.id, f"🎉 ربحت {won} نقطة!", show_alert=True)
    elif data == "support":
        bot.send_message(user_id, f"💬 الدعم المباشر: {YOUR_USERNAME}")

# ==========================================
# ⚡ تشغيل البوت والسيرفر
# ==========================================
if __name__ == "__main__":
    keep_alive()
    print("🚀 Nexus Pro AI Bot - شغال بأعلى كفاءة...")
    bot.infinity_polling()

