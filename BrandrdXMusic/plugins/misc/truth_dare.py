from pyrogram import filters
import requests
from deep_translator import GoogleTranslator
from BrandrdXMusic import app

# قائمة الكلمات الممنوعة (فلتر القيم)
FORBIDDEN_WORDS = [
    "نبيذ", "بيرة", "كحول", "مشروب", "سكران", "شرب",
    "حبيبتك", "حبيبك", "كراش", "مواعدة", "علاقة", "حب",
    "قبلة", "بوسة", "حضن", "شفاه", "فمك", "رقبة",
    "عاري", "ملابس داخلية", "اخلع", "جسمك", "صدرك", "فخذ",
    "سرير", "نوم", "جنس", "مثير", "ساخن", "شاذ", "مثلي",
    "رقص", "ديسكو", "بار", "حظ", "يانصيب"
]

# دالة لجلب وترجمة وفلترة السؤال
def get_safe_content(api_type):
    url = f"https://api.truthordarebot.xyz/v1/{api_type}?rating=pg"
    
    # محاولة 5 مرات للعثور على سؤال نظيف
    for _ in range(5):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                english_text = response.json()["question"]
                
                # الترجمة
                arabic_text = GoogleTranslator(source='auto', target='ar').translate(english_text)
                
                # الفلترة
                is_safe = True
                for word in FORBIDDEN_WORDS:
                    if word in arabic_text:
                        is_safe = False
                        break 
                
                if is_safe:
                    return arabic_text
        except:
            continue
            
    return "تعذر العثور على سؤال مناسب حالياً، حاول مرة أخرى."

@app.on_message(filters.command(["truth", "صراحه", "صراحة"]))
async def get_truth(client, message):
    try:
        question = get_safe_content("truth")
        # تم إزالة الايموجي من هنا
        await message.reply_text(f"**صراحة:**\n\n{question}")
    except Exception:
        await message.reply_text("حدث خطأ في الاتصال.")

@app.on_message(filters.command(["dare", "جراه", "جرأة"]))
async def get_dare(client, message):
    try:
        dare = get_safe_content("dare")
        # تم إزالة الايموجي من هنا
        await message.reply_text(f"**جرأة:**\n\n{dare}")
    except Exception:
        await message.reply_text("حدث خطأ في الاتصال.")
