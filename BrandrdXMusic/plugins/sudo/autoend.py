from pyrogram import filters
from pyrogram.types import Message

from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS
from BrandrdXMusic.utils.database import autoend_off, autoend_on

@app.on_message(filters.command(["autoend", "انهاء_تلقائي"]) & SUDOERS)
async def auto_end_stream(client, message: Message):
    # رسالة التوضيح مزخرفة بالكشيدة والايموجي المطلوب
    usage = "🥀 **طـريـقـة الاسـتـخـدام :**\n\n/autoend [enable | disable]\n**أو بـالـعـربـيـة:**\n/انهاء_تلقائي [تفعيل | تعطيل]"
    
    if len(message.command) != 2:
        return await message.reply_text(usage)
    
    state = message.text.split(None, 1)[1].strip().lower()
    
    # حالة التفعيل
    if state in ["enable", "تفعيل"]:
        await autoend_on()
        await message.reply_text(
            "♥️ **تـم تـفـعـيـل نـظـام الـمـغـادرة الـتـلـقـائـيـة.**\n\n"
            "🧚 سـيـقـوم الـحـسـاب الـمـسـاعـد بـمـغـادرة الـمـحـادثـة الـصـوتـيـة تـلـقـائـيـاً بـعـد بـضـع دقـائـق "
            "فـي حـال عـدم وجـود مـسـتـمـعـيـن.\n"
            "💕 **هـذا الإعـداد يـسـري عـلـى مـسـتـوى الـبـوت بـالـكـامـل.**"
        )
        
    # حالة التعطيل
    elif state in ["disable", "تعطيل"]:
        await autoend_off()
        await message.reply_text(
            "🥀 **تـم تـعـطـيـل نـظـام الـمـغـادرة الـتـلـقـائـيـة.**\n\n"
            "💝 لـن يـغـادر الـحـسـاب الـمـسـاعـد الـمـحـادثـة أبـداً حـتـى لـو كـانـت فـارغـة."
        )
        
    else:
        await message.reply_text(usage)
