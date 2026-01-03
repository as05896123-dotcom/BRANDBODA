import random
from pyrogram import filters
from pyrogram.types import Message

from BrandrdXMusic import app
from BrandrdXMusic.core.database import get_assistant, delete_served_chat
from config import LOGGER_ID as LOG_GROUP_ID

# =========================
# صور اللوج
# =========================
PHOTOS = [
    "https://files.catbox.moe/wqipfn.jpg",
    "https://files.catbox.moe/4qhfqw.jpg",
    "https://files.catbox.moe/b6533n.jpg",
    "https://files.catbox.moe/b91yyd.jpg",
    "https://files.catbox.moe/xi3mb1.jpg",
]

# كاش بسيط لآيدي البوت
BOT_ID = None


@app.on_message(filters.left_chat_member)
async def on_left_chat_member(_, message: Message):
    global BOT_ID
    try:
        # التأكد إن الخارج هو البوت نفسه
        if not message.left_chat_member:
            return

        if BOT_ID is None:
            me = await app.get_me()
            BOT_ID = me.id

        if message.left_chat_member.id != BOT_ID:
            return

        # جلب المساعد
        userbot = await get_assistant(message.chat.id)

        remove_by = (
            message.from_user.mention
            if message.from_user
            else "مـسـتـخـدم مـجـهـول"
        )

        title = message.chat.title or "بدون اسم"
        chat_id = message.chat.id
        username = (
            f"@{message.chat.username}"
            if message.chat.username
            else "مـجـمـوعـة خـاصـة"
        )

        left_text = (
            f"✫ **خـروج مـن مـجـمـوعـة** 🥀\n\n"
            f"**اسـم الـمـجـمـوعـة :** {title}\n\n"
            f"**آيـدي الـمـجـمـوعـة :** `{chat_id}`\n\n"
            f"**تـم طـردي بـواسـطـة :** {remove_by}\n\n"
            f"**الـبـوت :** @{app.username} 🤍"
        )

        # إرسال اللوج
        await app.send_photo(
            LOG_GROUP_ID,
            photo=random.choice(PHOTOS),
            caption=left_text,
        )

        # تنظيف البيانات
        await delete_served_chat(chat_id)

        # خروج المساعد
        try:
            await userbot.leave_chat(chat_id)
        except:
            pass

    except Exception as e:
        print(f"LeftChat Error: {e}")
