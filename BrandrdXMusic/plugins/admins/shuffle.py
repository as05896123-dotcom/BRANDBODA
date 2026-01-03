import random

from pyrogram import filters
from pyrogram.types import Message

from BrandrdXMusic import app
from BrandrdXMusic.misc import db
from BrandrdXMusic.utils.decorators import AdminRightsCheck
from BrandrdXMusic.utils.inline import close_markup
from config import BANNED_USERS


@app.on_message(
    filters.command(
        ["shuffle", "cshuffle", "خلط", "عشوائي", "لخبطة"],
        prefixes=["/", "@", ".", "#", ""]
    )
    & filters.group
    & ~BANNED_USERS
)
@AdminRightsCheck
async def shuffle_queue(client, message: Message, _, chat_id):
    queue = db.get(chat_id)
    if not queue:
        return await message.reply_text(_["queue_2"])

    try:
        current = queue.pop(0)
    except IndexError:
        return await message.reply_text(
            _["admin_15"],
            reply_markup=close_markup(_)
        )

    if not queue:
        queue.insert(0, current)
        return await message.reply_text(
            _["admin_15"],
            reply_markup=close_markup(_)
        )

    random.shuffle(queue)
    queue.insert(0, current)

    await message.reply_text(
        _["admin_16"].format(message.from_user.mention),
        reply_markup=close_markup(_)
    )
