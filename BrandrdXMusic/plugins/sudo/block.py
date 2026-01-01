from pyrogram import filters
from pyrogram.types import Message

from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS
from BrandrdXMusic.utils.database import add_gban_user, remove_gban_user
from BrandrdXMusic.utils.extraction import extract_user
from config import BANNED_USERS


# دالة الحظر العام (منع مستخدم من استخدام البوت في كل المجموعات)
@app.on_message(filters.command(["block", "عام", "حظر_عام"]) & SUDOERS)
async def useradd(client, message: Message):
    if not message.reply_to_message:
        if len(message.command) != 2:
            return await message.reply_text(
                "🥀 **طـريـقـة الاسـتـخـدام :**\n\n"
                "• block [المعرف/الآيدي]\n"
                "• عام [المعرف/الآيدي]"
            )
    
    user = await extract_user(message)
    if user.id in BANNED_USERS:
        return await message.reply_text(f"🧚 **الـعـضـو {user.mention} مـحـظـور عـام بـالـفـعـل.**")
    
    await add_gban_user(user.id)
    BANNED_USERS.add(user.id)
    await message.reply_text(f"♥️ **تـم حـظـر الـعـضـو {user.mention} مـن اسـتـخـدام الـبـوت عـام بـنـجـاح.**")


# دالة رفع الحظر العام
@app.on_message(filters.command(["unblock", "فك_بلوك", "رفع_عام"]) & SUDOERS)
async def userdel(client, message: Message):
    if not message.reply_to_message:
        if len(message.command) != 2:
            return await message.reply_text(
                "🥀 **طـريـقـة الاسـتـخـدام :**\n\n"
                "• unblock [المعرف/الآيدي]\n"
                "• الغاء_عام [المعرف/الآيدي]"
            )
    
    user = await extract_user(message)
    if user.id not in BANNED_USERS:
        return await message.reply_text(f"🧚 **الـعـضـو {user.mention} لـيـس مـحـظـوراً عـام.**")
    
    await remove_gban_user(user.id)
    BANNED_USERS.remove(user.id)
    await message.reply_text(f"💝 **تـم رفـع الـحـظـر الـعـام عـن الـعـضـو {user.mention} بـنـجـاح.**")


# دالة عرض قائمة المحظورين عام
@app.on_message(filters.command(["blocked", "blockedusers", "blusers", "المحظورين_عام", "قائمة_العام"]) & SUDOERS)
async def sudoers_list(client, message: Message):
    if not BANNED_USERS:
        return await message.reply_text("💕 **لا يـوجـد مـسـتـخـدمـيـن مـحـظـوريـن عـام.**")
    
    mystic = await message.reply_text("🧚 **جـارِ جـلـب قـائـمـة الـمـحـظـوريـن عـام...**")
    msg = "🥀 **قـائـمـة الـمـحـظـوريـن مـن الـبـوت عـام :**\n\n"
    count = 0
    for users in BANNED_USERS:
        try:
            user = await app.get_users(users)
            user = user.first_name if not user.mention else user.mention
            count += 1
        except:
            continue
        msg += f"{count}➤ {user}\n"
    
    if count == 0:
        return await mystic.edit_text("💕 **لا يـوجـد مـسـتـخـدمـيـن مـحـظـوريـن عـام.**")
    else:
        return await mystic.edit_text(msg)
