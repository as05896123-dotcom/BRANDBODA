from pyrogram import filters
from pyrogram.types import Message

from BrandrdXMusic import app
from BrandrdXMusic.core.call import Hotty
from BrandrdXMusic.core.database import set_loop, get_cmode
from BrandrdXMusic.core.decorators import AdminRightsCheck
from BrandrdXMusic.utils.inline import close_markup
from config import BANNED_USERS


@app.on_message(
    filters.command(
        [
            "end", "stop", "cend", "cstop",
            "وقف", "ايقاف", "بس", "اقف"
        ],
        prefixes=["/", "@", ".", "#", ""]
    )
    & filters.group
    & ~BANNED_USERS
)
@AdminRightsCheck
async def stop_music(client, message: Message, _, chat_id):
    cmd = message.command[0]

    # --- دعم القناة المرتبطة ---
    if cmd.startswith("c"):
        linked = await get_cmode(chat_id)
        if not linked:
            return await message.reply_text(_["cplay_4"])
        chat_id = linked

    # --- إيقاف التشغيل ---
    await Hotty.stop_stream(chat_id)
    await set_loop(chat_id, 0)

    await message.reply_text(
        _["admin_5"].format(message.from_user.mention),
        reply_markup=close_markup(_),
    )
