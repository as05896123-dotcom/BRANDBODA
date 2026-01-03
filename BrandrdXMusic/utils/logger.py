from pyrogram.enums import ParseMode

from BrandrdXMusic import app
from BrandrdXMusic.core.database import is_on_off
from config import LOGGER_ID


async def play_logs(message, streamtype):
    if await is_on_off(2):
        logger_text = f"""
🥀 <b>{app.mention} سـجـل الـتـشـغـيـل</b>

♥️ <b>آيـدي الـمـجـمـوعـة :</b> <code>{message.chat.id}</code>
🧚 <b>اسـم الـمـجـمـوعـة :</b> {message.chat.title}
💕 <b>يـوزر الـمـجـمـوعـة :</b> @{message.chat.username}

💝 <b>آيـدي الـمـسـتـخـدم :</b> <code>{message.from_user.id}</code>
💘 <b>الاسـم :</b> {message.from_user.mention}
❤️ <b>الـيـوزر :</b> @{message.from_user.username}

🥀 <b>الـبـحـث :</b> {message.text.split(None, 1)[1]}
🧚 <b>نـوع الـتـشـغـيـل :</b> {streamtype}"""
        if message.chat.id != LOGGER_ID:
            try:
                await app.send_message(
                    chat_id=LOGGER_ID,
                    text=logger_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
            except:
                pass
        return
