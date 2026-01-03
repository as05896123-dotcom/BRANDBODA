from pyrogram import filters
from pyrogram.types import Message

from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS

# [CORE MIGRATION] استيراد دوال قاعدة البيانات من المسار الجديد
from BrandrdXMusic.core.database import add_gban_user, remove_gban_user

# استيراد دالة استخراج المستخدم
from BrandrdXMusic.utils.extraction import extract_user
from config import BANNED_USERS

# ==========================================================
# 1. الحظر العام (GBAN)
# ==========================================================
# الأوامر: حظر عام، عام، block
@app.on_message(filters.command(["block", "عام", "حظر"], prefixes=["", "/", "!", "."]) & SUDOERS)
async def useradd(client, message: Message):
    # إذا كتب المستخدم "حظر" فقط، نتأكد أنه يقصد "حظر عام"
    # إلا إذا كان الأمر هو "عام" أو "block" صراحة
    command = message.command[0]
    if command == "حظر" and "عام" not in message.text:
        return # نتجاهل الأمر لأنه قد يقصد حظر من المجموعة وليس عام

    # التحقق من المدخلات
    if not message.reply_to_message:
        if len(message.text.split()) < 2:
            return await message.reply_text(
                "🥀 **طـريـقـة الاسـتـخـدام :**\n\n"
                "يـجـب الـرد عـلـى الـعـضـو أو وضـع الـمـعـرف بـجـانـب الأمـر.\n\n"
                "**مـثـال:**\n"
                "<code>حظر عام @User</code>\n"
                "**أو:**\n"
                "<code>عام @User</code>"
            )
    
    user = await extract_user(message)
    if not user:
        return await message.reply_text("🥀 **عـذراً، لـم أسـتـطـع الـعـثـور عـلـى الـمـسـتـخـدم.**")

    if user.id in BANNED_USERS:
        return await message.reply_text(f"🧚 **الـعـضـو {user.mention} مـحـظـور عـام بـالـفـعـل.**")
    
    await add_gban_user(user.id)
    BANNED_USERS.add(user.id)
    await message.reply_text(f"♥️ **تـم حـظـر الـعـضـو {user.mention} مـن اسـتـخـدام الـبـوت عـام بـنـجـاح.**")


# ==========================================================
# 2. رفع الحظر العام (UNGBAN)
# ==========================================================
# الأوامر: رفع عام، فك عام، الغاء عام، unblock
@app.on_message(filters.command(["unblock", "فك", "رفع", "الغاء"], prefixes=["", "/", "!", "."]) & SUDOERS)
async def userdel(client, message: Message):
    # التأكد من سياق الأمر (يجب وجود كلمة 'عام' إذا كان الأمر عربي)
    command = message.command[0]
    if command in ["فك", "رفع", "الغاء"] and "عام" not in message.text:
        return # نتجاهل الأمر لتجنب التداخل مع أوامر أخرى
        
    if not message.reply_to_message:
        if len(message.text.split()) < 2:
            return await message.reply_text(
                "🥀 **طـريـقـة الاسـتـخـدام :**\n\n"
                "يـجـب الـرد عـلـى الـعـضـو أو وضـع الـمـعـرف بـجـانـب الأمـر.\n\n"
                "**مـثـال:**\n"
                "<code>رفع عام @User</code>\n"
                "**أو:**\n"
                "<code>فك عام @User</code>"
            )
    
    user = await extract_user(message)
    if not user:
        return await message.reply_text("🥀 **عـذراً، لـم أسـتـطـع الـعـثـور عـلـى الـمـسـتـخـدم.**")

    if user.id not in BANNED_USERS:
        return await message.reply_text(f"🧚 **الـعـضـو {user.mention} لـيـس مـحـظـوراً عـام.**")
    
    await remove_gban_user(user.id)
    if user.id in BANNED_USERS:
        BANNED_USERS.remove(user.id)
        
    await message.reply_text(f"💝 **تـم رفـع الـحـظـر الـعـام عـن الـعـضـو {user.mention} بـنـجـاح.**")


# ==========================================================
# 3. عرض قائمة المحظورين
# ==========================================================
# الأوامر: المحظورين عام، قائمة العام، blocked
@app.on_message(filters.command(["blocked", "blockedusers", "المحظورين", "قائمة"], prefixes=["", "/", "!", "."]) & SUDOERS)
async def sudoers_list(client, message: Message):
    # التأكد من السياق
    if "المحظورين" in message.text and "عام" not in message.text:
        return
    if "قائمة" in message.text and "عام" not in message.text:
        return

    if not BANNED_USERS:
        return await message.reply_text("💕 **لا يـوجـد مـسـتـخـدمـيـن مـحـظـوريـن عـام.**")
    
    mystic = await message.reply_text("🧚 **جـارِ جـلـب قـائـمـة الـمـحـظـوريـن عـام...**")
    msg = "🥀 **قـائـمـة الـمـحـظـوريـن مـن الـبـوت عـام :**\n\n"
    count = 0
    
    for users in list(BANNED_USERS):
        try:
            user = await app.get_users(users)
            user_mention = user.first_name if not user.mention else user.mention
            count += 1
            msg += f"{count}➤ {user_mention} (`{user.id}`)\n"
        except:
            continue
    
    if count == 0:
        return await mystic.edit_text("💕 **لا يـوجـد مـسـتـخـدمـيـن مـحـظـوريـن عـام.**")
    else:
        if len(msg) > 4096:
             msg = msg[:4000] + "\n\n...والباقي كثير."
        return await mystic.edit_text(msg)
