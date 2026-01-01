import asyncio
import random

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.raw.functions.messages import DeleteHistory

from BrandrdXMusic import userbot as us, app
from BrandrdXMusic.core.userbot import assistants

# تم تعريب الأمر ليصبح "تاريخ" أو "اسماء" أو "sg"
@app.on_message(filters.command(["sg", "تاريخ", "اسماء", "سجل"]))
async def sg(client: Client, message: Message):
    if len(message.text.split()) < 2 and not message.reply_to_message:
        return await message.reply("عذراً، قم بالرد على العضو أو اكتب المعرف بجانب الأمر.\nمثال: `تاريخ @username`")
    if message.reply_to_message:
        args = message.reply_to_message.from_user.id
    else:
        args = message.text.split()[1]
    
    lol = await message.reply("<code>جارِ جلب سجل الأسماء...</code>")
    
    if args:
        try:
            user = await client.get_users(f"{args}")
        except Exception:
            return await lol.edit("<code>لم أتمكن من العثور على هذا المستخدم!</code>")
    
    bo = ["sangmata_bot", "sangmata_beta_bot"]
    sg = random.choice(bo)
    
    if 1 in assistants:
        ubot = us.one
    
    try:
        a = await ubot.send_message(sg, f"{user.id}")
        await a.delete()
    except Exception as e:
        return await lol.edit(f"حدث خطأ: {e}")
    
    await asyncio.sleep(1)
    
    async for stalk in ubot.search_messages(a.chat.id):
        if stalk.text == None:
            continue
        if not stalk:
            await message.reply("فشل في جلب البيانات من المصدر.")
        elif stalk:
            # هنا يتم إرسال الرسالة التي جلبها من بوت SangMata
            await message.reply(f"{stalk.text}")
            break  
    
    try:
        user_info = await ubot.resolve_peer(sg)
        await ubot.send(DeleteHistory(peer=user_info, max_id=0, revoke=True))
    except Exception:
        pass
    
    await lol.delete()
