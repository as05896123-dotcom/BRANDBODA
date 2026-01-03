import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import UserNotParticipant

from BrandrdXMusic import app
from BrandrdXMusic.utils.branded_ban import admin_filter

# ===============================
# متغيرات عامة
# ===============================
SPAM_CHATS = {}

# ===============================
# منشن لانهائي
# ===============================
@app.on_message(
    filters.command(
        ["utag", "uall", "تاك لانهائي", "منشن لانهائي"],
        prefixes=["/", "@", ".", "#", ""]
    )
    & admin_filter
)
async def tag_all_users(_, message):
    chat_id = message.chat.id

    if len(message.text.split()) == 1:
        return await message.reply_text(
            "**اكتب النص الذي تريد نشره مع الأمر، مثال »** `تاك لانهائي هلا والله`"
        )

    text = message.text.split(None, 1)[1]

    await message.reply_text(
        "**بدأت عملية المنشن اللانهائي (5 أعضاء) بنجاح!**\n\n"
        "**๏ الفاصل الزمني: 7 ثواني.**\n\n"
        "**➥ للإيقاف أرسل » /stoputag أو ايقاف المنشن**"
    )

    SPAM_CHATS[chat_id] = True

    while SPAM_CHATS.get(chat_id):
        usernum = 0
        usertxt = ""

        try:
            async for member in app.get_chat_members(chat_id):
                if not SPAM_CHATS.get(chat_id):
                    break

                if member.user.is_bot:
                    continue

                usernum += 1
                usertxt += f"\n⊚ [{member.user.first_name}](tg://user?id={member.user.id})\n"

                if usernum == 5:
                    await app.send_message(
                        chat_id,
                        f"{text}\n{usertxt}\n\n|| ➥ للإيقاف أرسل » /stoputag ||",
                    )
                    usernum = 0
                    usertxt = ""
                    await asyncio.sleep(7)

        except Exception as e:
            print(e)
            break

# ===============================
# إيقاف المنشن اللانهائي
# ===============================
@app.on_message(
    filters.command(
        [
            "stoputag", "stopuall", "offutag", "offuall",
            "utagoff", "ualloff", "ايقاف المنشن",
            "ايقاف التاك", "بس منشن"
        ],
        prefixes=["/", ".", "@", "#", ""],
    )
    & admin_filter
)
async def stop_tagging(_, message):
    chat_id = message.chat.id

    if SPAM_CHATS.get(chat_id):
        SPAM_CHATS[chat_id] = False
        return await message.reply_text(
            "**جاري إيقاف المنشن اللانهائي، يرجى الانتظار...**"
        )

    await message.reply_text(
        "**لا توجد عملية منشن لانهائي شغالة حالياً**"
    )
