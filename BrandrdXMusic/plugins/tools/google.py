import logging
from googlesearch import search
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from BrandrdXMusic import app
from SafoneAPI import SafoneAPI

# --- دالة مساعدة لتجنب الأخطاء عند جلب البيانات ---
def safe_get(dictionary, key, default="غير متوفر"):
    return dictionary.get(key, default) if dictionary else default

# --- أوامر بحث جوجل ---
@app.on_message(filters.command(["google", "gle", "جوجل", "بحث"]))
async def google_search(bot, message):
    try:
        # التحقق من المدخلات بذكاء
        if len(message.command) < 2 and not message.reply_to_message:
            # تم تعديل التوجيه ليكون بالعربي وبدون سلاش
            await message.reply_text("**🧚 طـريـقـة الاسـتـخـدام :**\n\nجوجل + كـلـمـة الـبـحـث")
            return

        if message.reply_to_message and message.reply_to_message.text:
            user_input = message.reply_to_message.text
        elif len(message.command) > 1:
            user_input = " ".join(message.command[1:])
        else:
            await message.reply_text("**🥀 يـرجـى كـتـابـة شـيء لـلـبـحـث عـنـه.**")
            return

        m = await message.reply_text("🧚 **جـاري الـبـحـث فـي جـوجـل...**")

        # إجراء البحث
        try:
            results = search(user_input, advanced=True, num_results=5, sleep_interval=0)
        except Exception:
            await m.edit("🥀 **تـعـذر الاتـصـال بـخـدمـة الـبـحـث حـالـيـاً.**")
            return

        txt = f"🤎 **نـتـائـج الـبـحـث عـن :** `{user_input}`\n\n"
        count = 0
        
        for result in results:
            if count >= 5:
                break
            
            title = result.title if result.title else "بدون عنوان"
            url = result.url if result.url else "https://google.com"
            description = result.description if result.description else "لا يوجد وصف متاح."
            
            # تجميع النص وتنسيقه
            txt += f"💕 **[{title}]({url})**\n🤍 `{description[:150]}...`\n\n"
            count += 1
            
        if count == 0:
            await m.edit("🥀 **لـم يـتـم الـعـثـور عـلى أي نـتـائـج.**")
        else:
            await m.edit(txt, disable_web_page_preview=True)

    except Exception as e:
        logging.exception(e)
        try:
            await m.edit("**🥀 حـدث خـطـأ غـيـر مـتـوقـع.**")
        except:
            pass


# --- أوامر بحث التطبيقات ---
@app.on_message(filters.command(["app", "apps", "تطبيق", "برنامج"]))
async def app_search(bot, message):
    try:
        if len(message.command) < 2 and not message.reply_to_message:
            # تم تعديل التوجيه ليكون بالعربي وبدون سلاش
            await message.reply_text("**🧚 طـريـقـة الاسـتـخـدام :**\n\nتطبيق + اسـم الـتـطـبـيـق")
            return

        if message.reply_to_message and message.reply_to_message.text:
            user_input = message.reply_to_message.text
        else:
            user_input = " ".join(message.command[1:])

        cbb = await message.reply_text("🤎 **جـاري الـبـحـث فـي الـمـتـجـر...**")

        try:
            a = await SafoneAPI().apps(user_input, 1)
        except Exception:
            await cbb.edit("🥀 **خـطـأ فـي الاتـصـال بـالـخـادم.**")
            return
        
        # التحقق من وجود نتائج
        if not a or "results" not in a or not a["results"]:
            await cbb.edit("🥀 **لـم يـتـم الـعـثـور عـلى الـتـطـبـيـق.**")
            return

        # استخراج البيانات بأمان تام
        b = a["results"][0]
        
        icon = safe_get(b, "icon", None)
        app_id = safe_get(b, "id", "Unknown")
        link = safe_get(b, "link", "https://play.google.com")
        desc = safe_get(b, "description", "لا يوجد وصف")[:300]
        title = safe_get(b, "title", "تطبيق")
        dev = safe_get(b, "developer", "غير معروف")

        info = (
            f"💕 **الاسـم :** `{title}`\n"
            f"🤍 **الآيـدي :** `{app_id}`\n"
            f"🧚 **الـمـطـور :** {dev}\n\n"
            f"💞 **الـوصـف :**\n{desc}..."
        )
        
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("♥️ رابـط الـتـطـبـيـق", url=link)]]
        )

        try:
            if icon:
                await message.reply_photo(icon, caption=info, reply_markup=keyboard)
            else:
                await message.reply_text(info, reply_markup=keyboard)
        except Exception:
            await message.reply_text(info, reply_markup=keyboard)
            
        await cbb.delete()

    except Exception as e:
        logging.exception(e)
        try:
            await cbb.edit(f"**🥀 حـدث خـطـأ :** {e}")
        except:
            pass
