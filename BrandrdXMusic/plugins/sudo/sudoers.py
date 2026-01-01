from pyrogram import filters
from pyrogram.types import Message

from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS
from BrandrdXMusic.utils.database import add_sudo, remove_sudo
from BrandrdXMusic.utils.extraction import extract_user
from BrandrdXMusic.utils.inline import close_markup
from config import BANNED_USERS, OWNER_ID


# 1. إضافة مطور (Add Sudo)
@app.on_message(filters.command(["addsudo", "رفع مطور", "رفع_مطور"]) & filters.user(OWNER_ID))
async def useradd(client, message: Message):
    if not message.reply_to_message:
        if len(message.command) != 2:
            return await message.reply_text("🥀 **قـم بـالـرد عـلـى الـعـضـو أو ضـع مـعـرفـه بـعـد الأمـر.**")
            
    user = await extract_user(message)
    if not user:
        return await message.reply_text("🥀 **عـذراً، لـم أسـتـطـع إيـجـاد هـذا الـمـسـتـخـدم.**")
        
    if user.id in SUDOERS:
        return await message.reply_text(f"🧚 **الـعـضـو** {user.mention} **مـطـور بـالـفـعـل.**")
        
    added = await add_sudo(user.id)
    if added:
        SUDOERS.add(user.id)
        await message.reply_text(f"♥️ **تـم رفـع الـعـضـو** {user.mention} **مـطـور فـي الـبـوت.**")
    else:
        await message.reply_text("🥀 **حـدث خـطـأ، تـأكـد مـن قـاعـدة الـبـيـانـات.**")


# 2. حذف مطور (Remove Sudo)
@app.on_message(filters.command(["delsudo", "rmsudo", "تنزيل مطور", "تنزيل_مطور"]) & filters.user(OWNER_ID))
async def userdel(client, message: Message):
    if not message.reply_to_message:
        if len(message.command) != 2:
            return await message.reply_text("🥀 **قـم بـالـرد عـلـى الـعـضـو أو ضـع مـعـرفـه بـعـد الأمـر.**")
            
    user = await extract_user(message)
    if not user:
        return await message.reply_text("🥀 **عـذراً، لـم أسـتـطـع إيـجـاد هـذا الـمـسـتـخـدم.**")

    if user.id not in SUDOERS:
        return await message.reply_text(f"🧚 **الـعـضـو** {user.mention} **لـيـس مـطـوراً أصـلاً.**")
        
    removed = await remove_sudo(user.id)
    if removed:
        SUDOERS.remove(user.id)
        await message.reply_text(f"🧚 **تـم تـنـزيـل الـعـضـو** {user.mention} **مـن الـمـطـوريـن.**")
    else:
        await message.reply_text("🥀 **حـدث خـطـأ، تـأكـد مـن قـاعـدة الـبـيـانـات.**")


# 3. قائمة المطورين (Sudo List)
@app.on_message(filters.command(["sudolist", "listsudo", "sudoers", "المطورين", "قائمة المطورين"]) & ~BANNED_USERS)
async def sudoers_list(client, message: Message):
    # إذا لم يكن المستخدم مطوراً، يظهر المالك (بودا المزخرف)
    if message.from_user.id not in SUDOERS:
        return await message.reply_text(
            "👑 **مـالـك الـبـوت الأسـاسـي :**\n\n"
            "1➤ <a href='https://t.me/S_G0C7'>🇪🇬⛦°𝗕𝗢𝗗𝗔 𓆩🇽𓆪 𝗞𝗜𝗡𝗚🇳</a>",
            disable_web_page_preview=True
        )

    text = "👑 **قـائـمـة مـطـوريـن سـورس بـودا :**\n\n"
    
    # جلب المالك الأساسي من Config
    try:
        user = await app.get_users(OWNER_ID)
        user_name = user.first_name if not user.mention else user.mention
        text += f"1➤ {user_name}\n"
    except:
        text += f"1➤ {OWNER_ID}\n"

    count = 0
    smex = 0
    
    # جلب باقي المطورين من القائمة
    for user_id in SUDOERS:
        if user_id != OWNER_ID:
            try:
                user = await app.get_users(user_id)
                user_name = user.first_name if not user.mention else user.mention
                if smex == 0:
                    smex += 1
                    text += "\n⚡️ **الـمـطـوريـن الـثـانـويـيـن :**\n\n"
                count += 1
                text += f"{count}➤ {user_name}\n"
            except:
                continue
                
    if not text:
        await message.reply_text("🥀 **لا يـوجـد مـطـوريـن حـالـيـاً.**")
    else:
        await message.reply_text(text, disable_web_page_preview=True)
