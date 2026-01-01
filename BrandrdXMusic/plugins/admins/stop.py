from pyrogram import filters
from pyrogram.types import Message

from BrandrdXMusic import app
from BrandrdXMusic.core.call import Hotty
# قمنا بإضافة get_cmode لجلب القناة المرتبطة
from BrandrdXMusic.utils.database import set_loop, get_cmode
from BrandrdXMusic.utils.decorators import AdminRightsCheck
from BrandrdXMusic.utils.inline import close_markup
from config import BANNED_USERS


@app.on_message(
    filters.command([
        "end", "stop", "cend", "cstop",
        "وقف", "ايقاف", "بس", "اقف"
    ]) & filters.group & ~BANNED_USERS
)
@AdminRightsCheck
async def stop_music(cli, message: Message, _, chat_id):
    # التحقق من النص: هل يحتوي على كلمة "قناة" أو "قناه"؟
    # أو هل الأمر يبدأ بحرف c بالانجليزي (مثل cstop)
    cmd = message.command[0]
    query = message.text.split(None, 1)[1] if len(message.command) > 1 else ""
    
    if cmd.startswith("c") or "قناة" in query or "قناه" in query:
        try:
            # جلب معرف القناة المرتبطة
            chat_id = await get_cmode(chat_id)
            if not chat_id:
                return await message.reply_text("خطأ: لا توجد قناة مرتبطة بهذا الجروب.")
        except:
            return await message.reply_text(_["cplay_4"])
            
    await Hotty.stop_stream(chat_id)
    await set_loop(chat_id, 0)
    await message.reply_text(
        _["admin_5"].format(message.from_user.mention), reply_markup=close_markup(_)
    )
