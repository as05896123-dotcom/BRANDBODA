import random
from pyrogram import Client
from pyrogram.types import Message
from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)
from config import LOGGER_ID as LOG_GROUP_ID
from BrandrdXMusic import app
from BrandrdXMusic.core.userbot import Userbot
from BrandrdXMusic.utils.database import delete_served_chat
from BrandrdXMusic.utils.database import get_assistant

# الروابط الجديدة للصور
photo = [
    "https://files.catbox.moe/wqipfn.jpg",
    "https://files.catbox.moe/4qhfqw.jpg",
    "https://files.catbox.moe/b6533n.jpg",
    "https://files.catbox.moe/b91yyd.jpg",
    "https://files.catbox.moe/xi3mb1.jpg",
]


@app.on_message(filters.new_chat_members, group=2)
async def join_watcher(_, message):
    try:
        userbot = await get_assistant(message.chat.id)
        chat = message.chat
        for members in message.new_chat_members:
            if members.id == app.id:
                count = await app.get_chat_members_count(chat.id)
                username = (
                    message.chat.username if message.chat.username else "مـجـمـوعـة خـاصـة"
                )
                msg = (
                    f"**🥀 تـم تـفـعـيـل الـبـوت فـي مـجـمـوعـة** 🧚‍♀️\n\n"
                    f"**🤍 الـمـجـمـوعـة :** {message.chat.title}\n"
                    f"**🤎 الآيـدي :** `{message.chat.id}`\n"
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
                                    f"🦋 الـشـخـص الـذي أضـافـنـي 🦋",
                                    url=f"tg://openmessage?user_id={message.from_user.id}",
                                )
                            ]
                        ]
                    ),
                )
                # محاولة انضمام المساعد (إذا كان الجروب عاماً ولديه يوزر)
                if message.chat.username:
                    await userbot.join_chat(f"{message.chat.username}")
    except Exception as e:
        print(f"Error: {e}")
