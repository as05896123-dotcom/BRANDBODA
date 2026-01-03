import asyncio
from pyrogram import filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message

from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS
from BrandrdXMusic.utils import get_readable_time

# [CORE MIGRATION] استيراد دوال قاعدة البيانات من المسار الجديد
from BrandrdXMusic.core.database import (
    add_banned_user,
    get_banned_count,
    get_banned_users,
    get_served_chats,
    is_banned_user,
    remove_banned_user,
)
from BrandrdXMusic.utils.extraction import extract_user
from config import BANNED_USERS


# ==========================================================
# 1. الحظر العام / التأديب (GBAN)
# ==========================================================
# الأوامر: تأديب، تاديب، gban
@app.on_message(filters.command(["gban", "globalban", "تأديب", "تاديب"], prefixes=["", "/", "!", "."]) & SUDOERS)
async def global_ban(client, message: Message):
    # التحقق من المدخلات (يجب وجود رد أو معرف)
    if not message.reply_to_message:
        if len(message.text.split()) < 2:
            return await message.reply_text(
                "🥀 **طـريـقـة الاسـتـخـدام :**\n\n"
                "يـجـب الـرد عـلـى الـعـضـو أو وضـع الـمـعـرف بـجـانـب الأمـر.\n\n"
                "**مـثـال:**\n"
                "<code>تأديب @User</code>\n"
                "**أو:**\n"
                "<code>gban @User</code>"
            )
            
    user = await extract_user(message)
    if not user:
        return await message.reply_text("🥀 **عـذراً، لـم أسـتـطـع الـعـثـور عـلـى الـمـسـتـخـدم.**")
    
    # حماية المطور والبوت والنفس
    if user.id == message.from_user.id:
        return await message.reply_text("🧚 **لا يـمـكـنـك تـأديب نـفـسـك.**")
    elif user.id == app.id:
        return await message.reply_text("🧚 **لا يـمـكـنـك تـأديب الـبـوت.**")
    elif user.id in SUDOERS:
        return await message.reply_text("🧚 **لا يـمـكـنـك تـأديب الـمـطـور.**")
        
    is_gbanned = await is_banned_user(user.id)
    if is_gbanned:
        return await message.reply_text(f"♥️ **الـعـضـو {user.mention} تـم تـأديـبـه مـسـبـقـاً.**")
        
    if user.id not in BANNED_USERS:
        BANNED_USERS.add(user.id)
        
    # جلب جميع المجموعات التي يعمل بها البوت
    served_chats = []
    chats = await get_served_chats()
    for chat in chats:
        served_chats.append(int(chat["chat_id"]))
        
    time_expected = get_readable_time(len(served_chats))
    
    mystic = await message.reply_text(
        f"🧚 **جـارِ تـأديب {user.mention} وطـرده مـن جـمـيـع الـمـجـمـوعـات...**\n"
        f"💕 **الـوقـت الـمـتـوقـع : {time_expected}**"
    )
    
    number_of_chats = 0
    for chat_id in served_chats:
        try:
            await app.ban_chat_member(chat_id, user.id)
            number_of_chats += 1
        except FloodWait as fw:
            await asyncio.sleep(int(fw.value))
        except:
            continue
            
    await add_banned_user(user.id)
    await message.reply_text(
        f"💝 **تـم تـفـعـيـل الـتـأديب عـلـى {user.mention}**\n\n"
        f"🥀 **بـواسـطـة : {message.from_user.mention}**\n"
        f"♥️ **تـم طـرده مـن : {number_of_chats} مـجـمـوعـة.**"
    )
    await mystic.delete()


# ==========================================================
# 2. رفع الحظر العام / المسامحة (UNGBAN)
# ==========================================================
# الأوامر: سامحه، ungban
@app.on_message(filters.command(["ungban", "سامحه"], prefixes=["", "/", "!", "."]) & SUDOERS)
async def global_un(client, message: Message):
    if not message.reply_to_message:
        if len(message.text.split()) < 2:
            return await message.reply_text(
                "🥀 **طـريـقـة الاسـتـخـدام :**\n\n"
                "يـجـب الـرد عـلـى الـعـضـو أو وضـع الـمـعـرف بـجـانـب الأمـر.\n\n"
                "**مـثـال:**\n"
                "<code>سامحه @User</code>\n"
                "**أو:**\n"
                "<code>ungban @User</code>"
            )
            
    user = await extract_user(message)
    if not user:
        return await message.reply_text("🥀 **عـذراً، لـم أسـتـطـع الـعـثـور عـلـى الـمـسـتـخـدم.**")

    is_gbanned = await is_banned_user(user.id)
    if not is_gbanned:
        return await message.reply_text(f"🧚 **الـعـضـو {user.mention} لـيـس خـاضـعـاً لـلـتـأديب.**")
        
    if user.id in BANNED_USERS:
        BANNED_USERS.remove(user.id)
        
    served_chats = []
    chats = await get_served_chats()
    for chat in chats:
        served_chats.append(int(chat["chat_id"]))
        
    time_expected = get_readable_time(len(served_chats))
    
    mystic = await message.reply_text(
        f"🧚 **جـارِ رفـع الـتـأديب عـن {user.mention} مـن جـمـيـع الـمـجـمـوعـات...**\n"
        f"💕 **الـوقـت الـمـتـوقـع : {time_expected}**"
    )
    
    number_of_chats = 0
    for chat_id in served_chats:
        try:
            await app.unban_chat_member(chat_id, user.id)
            number_of_chats += 1
        except FloodWait as fw:
            await asyncio.sleep(int(fw.value))
        except:
            continue
            
    await remove_banned_user(user.id)
    await message.reply_text(
        f"💝 **تـم رفـع الـتـأديب عـن {user.mention}**\n\n"
        f"🥀 **تـم إلـغـاء الـحـظـر فـي : {number_of_chats} مـجـمـوعـة.**"
    )
    await mystic.delete()


# ==========================================================
# 3. عرض قائمة المؤدبين
# ==========================================================
# الأوامر: قائمة التأديب، المؤدبين، gbanlist
@app.on_message(filters.command(["gbannedusers", "gbanlist", "المؤدبين", "قائمة"], prefixes=["", "/", "!", "."]) & SUDOERS)
async def gbanned_list(client, message: Message):
    # إذا كتب المستخدم "قائمة" فقط، نتأكد أنها "قائمة التأديب"
    # إذا كتب "المؤدبين" أو "gbanlist" سيعمل مباشرة
    if "قائمة" in message.text and "التأديب" not in message.text:
        return 

    counts = await get_banned_count()
    if counts == 0:
        return await message.reply_text("💕 **لا يـوجـد مـسـتـخـدمـيـن تـم تـأديـبـهـم حـالـيـاً.**")
        
    mystic = await message.reply_text("🧚 **جـارِ جـلـب قـائـمـة الـمـؤدبـيـن...**")
    msg = "🥀 **قـائـمـة الـمـحـظـوريـن عـام (التأديب) :**\n\n"
    count = 0
    users = await get_banned_users()
    for user_id in users:
        count += 1
        try:
            user = await app.get_users(user_id)
            user_mention = user.first_name if not user.mention else user.mention
            msg += f"**{count}➤** {user_mention}\n"
        except Exception:
            msg += f"**{count}➤** `{user_id}`\n"
            continue
            
    if count == 0:
        return await mystic.edit_text("💕 **لا يـوجـد مـسـتـخـدمـيـن تـم تـأديـبـهـم حـالـيـاً.**")
    else:
        return await mystic.edit_text(msg)
