import asyncio
import random
from pyrogram import filters
from pyrogram.enums import ChatType, ChatMemberStatus
from pyrogram.errors import UserNotParticipant
from pyrogram.types import ChatPermissions

from BrandrdXMusic import app
from BrandrdXMusic.utils.branded_ban import admin_filter

SPAM_CHATS = []


@app.on_message(
    filters.command(
        [
            "all",
            "mention",
            "mentionall",
            "تاك",
            "منشن",
            "الكل",
            "نادي",
            "للجميع",
        ],
        prefixes=["/", ".", "@", "#", ""],  # مع وبدون /
    )
    & admin_filter
)
async def tag_all_users(_, message):
    replied = message.reply_to_message

    if len(message.command) < 2 and not replied:
        return await message.reply_text(
            "اعطني نصاً للمنشن\nمثال: تاك السلام عليكم"
        )

    SPAM_CHATS.append(message.chat.id)

    usernum = 0
    usertxt = ""

    async for m in app.get_chat_members(message.chat.id):
        if message.chat.id not in SPAM_CHATS:
            break

        if not m.user or m.user.is_bot:
            continue

        usernum += 1
        usertxt += f"\n⊚ [{m.user.first_name}](tg://user?id={m.user.id})"

        if usernum == 5:
            if replied:
                await replied.reply_text(usertxt)
            else:
                text = message.text.split(None, 1)[1]
                await app.send_message(
                    message.chat.id,
                    f"{text}\n{usertxt}\n\nللإيقاف ارسل: بس",
                )

            await asyncio.sleep(2)
            usernum = 0
            usertxt = ""

    SPAM_CHATS.remove(message.chat.id)


@app.on_message(
    filters.command(
        [
            "stopmention",
            "offall",
            "cancel",
            "allstop",
            "stopall",
            "cancelmention",
            "offmention",
            "mentionoff",
            "alloff",
            "cancelall",
            "allcancel",
            "بس",
            "ايقاف",
            "إيقاف",
            "الغاء",
            "إلغاء",
            "اسكت",
        ],
        prefixes=["/", ".", "@", "#", ""],  # مع وبدون /
    )
    & admin_filter
)
async def cancelcmd(_, message):
    chat_id = message.chat.id

    if chat_id in SPAM_CHATS:
        SPAM_CHATS.remove(chat_id)
        return await message.reply_text("تم إيقاف المنشن بنجاح")

    return await message.reply_text("لا يوجد منشن شغال حالياً")
