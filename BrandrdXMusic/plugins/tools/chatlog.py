import random
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import LOGGER_ID as LOG_GROUP_ID
from BrandrdXMusic import app
from BrandrdXMusic.core.userbot import Userbot
from BrandrdXMusic.core.database import delete_served_chat, get_assistant


# الروابط الجديدة للصور
photo = [
    "https://files.catbox.moe/wqipfn.jpg",
    "https://files.catbox.moe/4qhfqw.jpg",
    "https://files.catbox.moe/b6533n.jpg",
    "https://files.catbox.moe/b91yyd.jpg",
    "https://files.catbox.moe/xi3mb1.jpg",
]


@app.on_message(filters.new_chat_members, group=2)
async def join_watcher(_, message: Message):
    try:
        userbot = await get_assistant(message.chat.id)
        chat = message.chat

        for members in message.new_chat_members:
            if members.id == app.id:
                count = await app.get_chat_members_count(chat.id)
                username = (
                    chat.username if chat.username else "مـجـمـوعـة خـاصـة"
                )

                msg = (
                    f"**🥀 تـم تـفـعـيـل الـبـوت فـي مـجـمـوعـة** 🧚‍♀️\n\n"
                    f"**🤍 الـمـجـمـوعـة :** {chat.title}\n"
                    f"**🤎 الآيـدي :** `{chat.id}`\n"
                    f"**🧚 الـمـعـرف :** @{username}\n"
                    f"**♥️ الأعـضـاء :** {count}\n"
                    f"**⚡ بـواسـطـة :** {message.from_user.mention}"
                )

                await app.send_photo(
                    LOG_GROUP_ID,
                    photo=random.choice(photo),
                    caption=msg,
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "🦋 الـشـخـص الـذي أضـافـنـي 🦋",
                                    url=f"tg://openmessage?user_id={message.from_user.id}",
                                )
                            ]
                        ]
                    ),
                )

                # محاولة انضمام المساعد (لو الجروب عام)
                if chat.username:
                    await userbot.join_chat(chat.username)

    except Exception as e:
        print(f"Join Watcher Error: {e}")
