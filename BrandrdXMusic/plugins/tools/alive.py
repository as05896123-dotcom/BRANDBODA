from pyrogram import filters, Client
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message
)

from BrandrdXMusic import app
from config import MUSIC_BOT_NAME, BANNED_USERS


@app.on_message(
    filters.command(
        ["alive", "شغال", "بوت", "تست"],
        prefixes=["/", "!", ".", ""]
    )
    & ~BANNED_USERS
)
async def start(client: Client, message: Message):
    try:
        await message.reply_photo(
            photo="https://files.catbox.moe/b6533n.jpg",
            caption=(
                f"اهـلاً بـيـك {message.from_user.mention} 🤍\n\n"
                f"أنـا {MUSIC_BOT_NAME} 🧚\n\n"
                f"بـوت خـدمـي مـتـكـامـل ( حـمـايـة + مـوسـيـقـى ) 🥀\n"
                f"أقـوم بـتـأمـيـن مـجـمـوعـتـك مـن الـتـفـلـيـش والـروابـط،\n"
                f"بـالإضـافـة لـتـشـغـيـل الـصـوتـيـات فـي الـمـكـالـمـات بـدقـة عـالـيـة 💕\n\n"
                f"لـو عـنـدك أي سـؤال انـضـم لـجـروب الـدعـم 🤎..."
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="الـمـطـور",
                            url="https://t.me/S_G0C7"
                        ),
                        InlineKeyboardButton(
                            text="الـدعـم",
                            url="https://t.me/music0587"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="الـقـنـاة",
                            url="https://t.me/SourceBoda"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="إغـلاق",
                            callback_data="close"
                        )
                    ],
                ]
            )
        )
    except Exception as e:
        print(f"Alive Error: {e}")
