import asyncio
import random

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.raw.functions.messages import DeleteHistory

from BrandrdXMusic import userbot as us, app
from BrandrdXMusic.core.userbot import assistants


# الأمر يشتغل بدون / + مع / ! .
@app.on_message(
    filters.command(
        ["sg", "تاريخ", "اسماء", "سجل"],
        prefixes=["", "/", "!", "."],
    )
)
async def sg(client: Client, message: Message):
    if len(message.text.split()) < 2 and not message.reply_to_message:
        return await message.reply(
            "عذراً، قم بالرد على العضو أو اكتب المعرف بجانب الأمر.\n"
            "مثال: `تاريخ @username`"
        )

    if message.reply_to_message:
        args = message.reply_to_message.from_user.id
    else:
        args = message.text.split()[1]

    lol = await message.reply("جارِ جلب سجل الأسماء...")

    try:
        user = await client.get_users(args)
    except Exception:
        return await lol.edit("لم أتمكن من العثور على هذا المستخدم!")

    bots = ["sangmata_bot", "sangmata_beta_bot"]
    sg_bot = random.choice(bots)

    if 1 in assistants:
        ubot = us.one
    else:
        return await lol.edit("لا يوجد مساعد متاح حالياً.")

    try:
        a = await ubot.send_message(sg_bot, f"{user.id}")
        await a.delete()
    except Exception as e:
        return await lol.edit(f"حدث خطأ: {e}")

    await asyncio.sleep(1)

    async for stalk in ubot.search_messages(a.chat.id):
        if not stalk or not stalk.text:
            continue
        await message.reply(stalk.text)
        break

    try:
        user_info = await ubot.resolve_peer(sg_bot)
        await ubot.send(
            DeleteHistory(peer=user_info, max_id=0, revoke=True)
        )
    except Exception:
        pass

    await lol.delete()
