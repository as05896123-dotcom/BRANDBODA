from pyrogram import filters

from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS
from BrandrdXMusic.utils.database import add_off, add_on

# دالة تفعيل أو تعطيل إرسال السجلات إلى مجموعة اللوج
@app.on_message(filters.command(["logger", "السجل", "سجل"]) & SUDOERS)
async def logger(client, message):
    usage = (
        "🥀 **طـريـقـة الاسـتـخـدام :**\n\n"
        "• logger enable\n"
        "• تفعيل السجل\n\n"
        "• logger disable\n"
        "• تعطيل السجل"
    )
    
    if len(message.command) != 2:
        return await message.reply_text(usage)
    
    # دمج النص للتحقق من الأوامر المركبة مثل "تفعيل السجل"
    text = message.text.strip()
    command_arg = message.text.split(None, 1)[1].strip().lower()

    if command_arg == "enable" or "تفعيل" in text:
        await add_on(2)
        await message.reply_text("♥️ **تـم تـفـعـيـل سـجـل الـبـوت (Logger) بـنـجـاح.**")
    elif command_arg == "disable" or "تعطيل" in text:
        await add_off(2)
        await message.reply_text("💕 **تـم تـعـطـيـل سـجـل الـبـوت (Logger) بـنـجـاح.**")
    else:
        await message.reply_text(usage)

# دالة سحب ملف السجلات
@app.on_message(filters.command(["cookies", "logs", "ملف_السجل", "السجلات"]) & SUDOERS)
async def get_cookies_logs(client, message):
    try:
        await message.reply_document(
            "cookies/logs.csv",
            caption="🧚 **تـفـضـل مـلـف سـجـلات الـبـوت (Logs/Cookies)...**"
        )
    except:
        await message.reply_text("🥀 **عـذراً، لـم يـتـم الـعـثـور عـلـى مـلـف الـسـجـلات.**")
