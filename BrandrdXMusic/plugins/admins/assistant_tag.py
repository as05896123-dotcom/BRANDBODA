import asyncio

from pyrogram import filters
from pyrogram.enums import ChatMembersFilter
from pyrogram.errors import FloodWait

from BrandrdXMusic.core.database import get_assistant
from BrandrdXMusic import app
from BrandrdXMusic.utils.branded_ban import admin_filter

SPAM_CHATS = []


@app.on_message(
    filters.command(
        [
            "atag",
            "aall",
            "amention",
            "amentionall",
            "تاك المساعد",
            "منشن المساعد",
            "تاك م",
            "منشن م"
        ],
        prefixes=["/", "@", ".", "#", ""]
    )
    & admin_filter
)
async def atag_all_useres(_, message):
    userbot = await get_assistant(message.chat.id)

    if message.chat.id in SPAM_CHATS:
        return await message.reply_text(
            "عمليـة المنشن شغالـة حاليـاً\nلإيقافهـا ارسـل: ايقاف المساعد"
        )

    replied = message.reply_to_message

    if len(message.command) < 2 and not replied:
        return await message.reply_text(
            "اكتب النص بعد الأمر\nمثال: تاك المساعد اهلاً"
        )

    SPAM_CHATS.append(message.chat.id)
    usernum = 0
    usertxt = ""

    async for m in app.get_chat_members(message.chat.id):
        if message.chat.id not in SPAM_CHATS:
            break

        usernum += 1
        usertxt += f'<a href="tg://openmessage?user_id={m.user.id}">{m.user.first_name}</a>\n'

        if usernum == 14:
            await userbot.send_message(
                message.chat.id,
                f"{replied.text if replied else message.text.split(None,1)[1]}\n\n{usertxt}",
                disable_web_page_preview=True
            )
            await asyncio.sleep(2)
            usernum = 0
            usertxt = ""

    SPAM_CHATS.remove(message.chat.id)


@app.on_message(
    filters.command(
        [
            "acancel",
            "astop",
            "stopatag",
            "ايقاف المساعد",
            "بس يا مساعد",
            "وقف المساعد"
        ],
        prefixes=["/", "@", ".", "#", ""]
    )
    & admin_filter
)
async def cancelcmd(_, message):
    chat_id = message.chat.id

    if chat_id in SPAM_CHATS:
        SPAM_CHATS.remove(chat_id)
        return await message.reply_text("تم إيقاف المنشن بنجاح")

    return await message.reply_text("لا يوجد منشن شغال حالياً")
