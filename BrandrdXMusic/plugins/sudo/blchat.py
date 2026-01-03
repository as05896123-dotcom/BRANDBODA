from pyrogram import filters
from pyrogram.types import Message

from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS

# [CORE MIGRATION] استيراد دوال قاعدة البيانات من المسار الجديد
from BrandrdXMusic.core.database import blacklist_chat, blacklisted_chats, whitelist_chat
from config import BANNED_USERS

# --- دالة مساعدة لاستخراج الآيدي من النص ---
def extract_chat_id(text):
    if not text:
        return None
    for word in text.split():
        try:
            # نحاول تحويل الكلمة لرقم (نتجاوز الكلمات العادية)
            # الآيدي غالباً يبدأ بـ -100 للمجموعات
            return int(word)
        except ValueError:
            continue
    return None

# ==========================================================
# 1. حظر مجموعة
# ==========================================================
@app.on_message(filters.command(["blchat", "blacklistchat", "حظر"], prefixes=["", "/", "!", "."]) & SUDOERS)
async def blacklist_chat_func(client, message: Message):
    # نحاول استخراج الآيدي من الرسالة
    chat_id = extract_chat_id(message.text)

    # إذا لم يجد آيدي، نرسل رسالة التوضيح
    if not chat_id:
        return await message.reply_text(
            "🥀 **طـريـقـة الاسـتـخـدام :**\n\n"
            "يـجـب وضـع آيـدي الـمـجـمـوعـة بـجـانـب الأمـر.\n\n"
            "**مـثـال:**\n"
            "<code>حظر مجموعة -100123456789</code>\n"
            "**أو:**\n"
            "<code>blchat -100123456789</code>"
        )
    
    # التحقق هل هي محظورة مسبقاً
    if chat_id in await blacklisted_chats():
        return await message.reply_text("🧚 **هـذه الـمـجـمـوعـة مـحـظـورة بـالـفـعـل.**")
    
    # تنفيذ الحظر
    blacklisted = await blacklist_chat(chat_id)
    if blacklisted:
        await message.reply_text(
            f"♥️ **تـم حـظـر الـمـجـمـوعـة ({chat_id}) مـن اسـتـخـدام الـبـوت بـنـجـاح.**"
        )
        try:
            # محاولة مغادرة المجموعة بعد حظرها
            await app.leave_chat(chat_id)
        except:
            pass
    else:
        await message.reply_text("🥀 **حـدث خـطـأ أثـنـاء حـظـر الـمـجـمـوعـة.**")


# ==========================================================
# 2. رفع الحظر عن مجموعة
# ==========================================================
@app.on_message(filters.command(["whitelistchat", "unblchat", "رفع"], prefixes=["", "/", "!", "."]) & SUDOERS)
async def white_funciton(client, message: Message):
    # التأكد أن الأمر هو لرفع الحظر (لتجنب التداخل مع أوامر رفع أخرى)
    if "حظر" not in message.text and "whitelist" not in message.text and "unbl" not in message.text:
        # إذا كتب "رفع" فقط بدون سياق الحظر، نتجاهل الأمر (قد يكون رفع مشرف)
        return

    chat_id = extract_chat_id(message.text)

    if not chat_id:
        return await message.reply_text(
            "🥀 **طـريـقـة الاسـتـخـدام :**\n\n"
            "يـجـب وضـع آيـدي الـمـجـمـوعـة بـجـانـب الأمـر.\n\n"
            "**مـثـال:**\n"
            "<code>رفع حظر -100123456789</code>\n"
            "**أو:**\n"
            "<code>unblchat -100123456789</code>"
        )

    if chat_id not in await blacklisted_chats():
        return await message.reply_text("🧚 **هـذه الـمـجـمـوعـة لـيـسـت مـحـظـورة أصـلاً.**")
    
    whitelisted = await whitelist_chat(chat_id)
    if whitelisted:
        return await message.reply_text(
            f"💝 **تـم رفـع الـحـظـر عـن الـمـجـمـوعـة ({chat_id}) بـنـجـاح.**"
        )
    
    await message.reply_text("🥀 **حـدث خـطـأ أثـنـاء رفـع الـحـظـر.**")


# ==========================================================
# 3. عرض القائمة
# ==========================================================
@app.on_message(filters.command(["blchats", "المجموعات", "قائمة"], prefixes=["", "/", "!", "."]) & ~BANNED_USERS)
async def all_chats(client, message: Message):
    # التحقق من سياق الأمر (المجموعات المحظورة)
    if "المجموعات" in message.text and "المحظورة" not in message.text:
        return # تجاهل لو كتب "المجموعات" فقط
    
    if "قائمة" in message.text and "المحظورة" not in message.text and "bl" not in message.text:
        return

    text = "🥀 **قـائـمـة الـمـجـمـوعـات الـمـحـظـورة :**\n\n"
    j = 0
    blacklisted = await blacklisted_chats()
    
    for count, chat_id in enumerate(blacklisted, 1):
        try:
            title = (await app.get_chat(chat_id)).title
        except:
            title = "مـجـمـوعـة خـاصـة/مـحـذوفـة"
        j = 1
        text += f"**{count}. {title}** [`{chat_id}`]\n"
    
    if j == 0:
        await message.reply_text("💕 **لا تـوجـد مـجـمـوعـات مـحـظـورة حـالـيـاً.**")
    else:
        await message.reply_text(text)
