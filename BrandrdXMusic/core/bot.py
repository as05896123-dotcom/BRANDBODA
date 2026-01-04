from pyrogram import Client, filters
import config

app = Client(
    "test-bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
)

@app.on_message(filters.private)
async def all_private(_, message):
    await message.reply_text("✅ أنا شغال وبستقبل رسائل")

@app.on_message(filters.command("ping"))
async def ping(_, message):
    await message.reply_text("🏓 pong")

app.run()
