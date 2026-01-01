import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from BrandrdXMusic import app
from config import OWNER_ID
from BrandrdXMusic.utils.database import add_served_chat, get_assistant

# إعدادات السورس
REPO_IMG = "https://files.catbox.moe/b6533n.jpg"
REPO_URL = "https://t.me/SourceBoda"
DEV_URL = "https://t.me/S_G0C7"
EXCLUDED_GROUP_ID = -1003339220169

# أمر السورس
@app.on_message(filters.command(["repo", "سورس", "السورس"], prefixes=["/", "!", ".", "", "@"]))
async def repo(client: Client, message: Message):
    await message.reply_photo(
        photo=REPO_IMG,
        caption=f"""
• اهـلاً بـك فـي سـورس 𝐒𝐨𝐮𝐫𝐜𝐞 𝐁𝐨𝐝𝐚 🧚🤍
ـــــــــــــــــــــــــــــــــــــــــــــــــــــــ
• يـقـدم الـسـورس تـجـربـة سـريـعـة ومـمـيـزة 🥀
• لـمـعـرفـة الـمـزيـد اضـغـط عـلـى الازرار ادنـاه 💞
ـــــــــــــــــــــــــــــــــــــــــــــــــــــــ
""",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "• 𝐒𝐨𝐮𝐫𝐜𝐞 𝐁𝐨𝐝𝐚 •", url=REPO_URL
                    ),
                    InlineKeyboardButton(
                        "• 𝐃𝐞𝐯 𝐒𝐨𝐮𝐫𝐜𝐞 •", url=DEV_URL
                    )
                ]
            ]
        ),
    )

# أمر النسخ
@app.on_message(filters.command(["clone", "نسخ", "نسخه"], prefixes=["/", "!", ".", "", "@"]))
async def clones(client: Client, message: Message):
    await message.reply_photo(
        photo=REPO_IMG,
        caption=f"""
• عـذراً يـا حـلـو 🥀
ـــــــــــــــــــــــــــــــــــــــــــــــــــــــ
• الـمـيـزة دي خـاصـة بـصـاحـب الـبـوت بـس 🤍🧚
• كـلـم الـمـطـور لـو عـايـز نـسـخـة مـن الـبـوت 💞
ـــــــــــــــــــــــــــــــــــــــــــــــــــــــ
""",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "• 𝐃𝐞𝐯 𝐒𝐨𝐮𝐫𝐜𝐞 •", url=DEV_URL
                    )
                ]
            ]
        ),
    )


# تجميع المجموعات
@app.on_message(
    filters.command(
        ["hi", "hii", "hello", "hui", "good", "gm", "ok", "bye", "welcome", "thanks", "هلا", "مرحبا", "اهلين", "سلام"],
        prefixes=["/", "!", "%", ",", "", ".", "@", "#"],
    )
    & filters.group
)
async def bot_check(_, message):
    chat_id = message.chat.id
    await add_served_chat(chat_id)


# أمر إضافة البوت (للمطور)
@app.on_message(filters.command(["gadd", "اضف"], prefixes=["/", "!", ".", ""]) & filters.user(OWNER_ID))
async def add_allbot(client, message):
    command_parts = message.text.split(" ")
    if len(command_parts) != 2:
        await message.reply(
            "**• خـطـأ فـي الـصـيـغـة 🥀**\n**• جـرب كـده » اضف @يوزر_البوت 🧚**"
        )
        return

    bot_username = command_parts[1]
    try:
        userbot = await get_assistant(message.chat.id)
        bot = await app.get_users(bot_username)
        app_id = bot.id
        done = 0
        failed = 0
        lol = await message.reply("• جـارِ اضـافـة الـبـوت لـجـمـيـع الـمـجـمـوعـات 🧚🤍 ...")
        
        try:
            await userbot.send_message(bot_username, "/start")
        except:
            pass

        async for dialog in userbot.get_dialogs():
            if dialog.chat.id == EXCLUDED_GROUP_ID:
                continue
            
            try:
                await userbot.add_chat_members(dialog.chat.id, app_id)
                done += 1
                await lol.edit(
                    f"**• جـارِ اضـافـة »** {bot_username} 💞\n\n**• تـمـت الاضـافـة فـي »** {done} 🤍\n**• فـشـل فـي »** {failed} 🥀\n\n**• بـواسـطـة »** @{userbot.username} 🧚"
                )
            except Exception as e:
                failed += 1
                await lol.edit(
                    f"**• جـارِ اضـافـة »** {bot_username} 💞\n\n**• تـمـت الاضـافـة فـي »** {done} 🤍\n**• فـشـل فـي »** {failed} 🥀\n\n**• بـواسـطـة »** @{userbot.username} 🧚"
                )
            await asyncio.sleep(3)

        await lol.edit(
            f"**• تـمـت اضـافـة الـبـوت بـنـجـاح 💞🤍**\n\n**• تـمـت الاضـافـة فـي »** {done} 🤍\n**• فـشـل فـي »** {failed} 🥀\n\n**• بـواسـطـة »** @{userbot.username} 🧚"
        )
    except Exception as e:
        await message.reply(f"حدث خطأ: {str(e)}")


__MODULE__ = "السورس"
__HELP__ = """
**🧚 اوامـر الـسـورس والـمـطـور 🤍**

- سورس : لـعـرض مـعـلـومـات الـسـورس والـمـطـور 🥀
- نسخ : طـلـب نـسـخـة مـن الـبـوت 💞
- اضف [يوزر البوت] : لـنـشـر بـوتـك فـي الـمـجـمـوعـات عـبـر الـمـسـاعـد (لـلـمـطـور فـقـط) 🧚
"""
