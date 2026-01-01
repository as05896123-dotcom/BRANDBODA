import asyncio

from pyrogram import enums, filters
from pyrogram.errors import FloodWait

from BrandrdXMusic import app


@app.on_message(filters.command(["bots", "البوتات"]) & filters.group)
async def bots(client, message):

    try:
        botList = []
        async for bot in app.get_chat_members(
            message.chat.id, filter=enums.ChatMembersFilter.BOTS
        ):
            botList.append(bot.user)
        lenBotList = len(botList)
        
        text3 = f"**قـائـمـة الـبـوتـات فـي - {message.chat.title}** 🥀\n\n"
        
        while len(botList) > 1:
            bot = botList.pop(0)
            text3 += f"├ @{bot.username}\n"
        else:
            bot = botList.pop(0)
            text3 += f"└ @{bot.username}\n\n"
            text3 += f"**عـدد الـبـوتـات الـكـلـي :** {lenBotList} 🧚"
            
            await app.send_message(message.chat.id, text3)
    except FloodWait as e:
        await asyncio.sleep(e.value)
