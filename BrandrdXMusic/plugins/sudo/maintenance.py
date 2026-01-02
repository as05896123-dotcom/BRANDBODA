import os
from pyrogram import filters
from pyrogram.types import Message
from BrandrdXMusic import app
from config import OWNER_ID
from BrandrdXMusic.utils.database import (
    is_maintenance,
    maintenance_off,
    maintenance_on,
    is_on_off,
    add_on,
    add_off,
)

# --- دالة فحص الصيانة (تعالج مشكلة الـ TypeError تلقائياً) ---
async def check_maint():
    """تتأكد من حالة الصيانة سواء كانت الدالة تطلب رقم 1 أم لا"""
    try:
        # المحاولة 1: استدعاء فارغ
        return await is_maintenance()
    except TypeError:
        # المحاولة 2: استدعاء مع رقم 1 (لأن السورس لديك يستخدم IDs)
        try:
            return await is_maintenance(1)
        except Exception:
            return False
    except Exception:
        return False
# -----------------------------------------------------------

# 1. الحارس (Maintenance Check)
@app.on_message(filters.all & ~filters.user(OWNER_ID), group=-1)
async def maintenance_check(client, message: Message):
    try:
        if not message.text:
            return
            
        if await check_maint():
            await message.reply_text(
                "**الـبـوت فـي وضـع الـصـيـانـة حـالـيـاً**\n\nنـحـن نـعـمـل عـلـى تـحـديـث الـبـوت، يـرجـى الـمـحـاولـة لاحـقـاً."
            )
            message.stop_propagation()
    except Exception:
        pass


# 2. أوامر الصيانة (للمطور فقط)
@app.on_message(filters.command(["maintenance", "الصيانة"], prefixes=["/", "!", ".", ""]) & filters.user(OWNER_ID))
async def maintenance(client, message: Message):
    if len(message.command) != 2:
        return await message.reply_text(
            "**طـريـقـة اسـتـخـدام وضـع الـصـيـانـة:**\n\n"
            "• لـتـفـعـيـل الـصـيـانـة ارسـل: **الصيانة تفعيل**\n"
            "• لـتـعـطـيـل الـصـيـانـة ارسـل: **الصيانة تعطيل**"
        )
        
    state = message.text.split(None, 1)[1].strip().lower()
    
    # نستخدم دالة الفحص الذكية
    is_active = await check_maint()

    if state in ["enable", "تفعيل", "on"]:
        if is_active:
            await message.reply_text("**وضـع الـصـيـانـة مـفـعّـل بـالـفـعـل!**")
        else:
            await maintenance_on()
            await message.reply_text("**تـم تـفـعـيـل وضـع الـصـيـانـة.**\n\nلن يستطيع أحد استخدام البوت غير المطورين.")
            
    elif state in ["disable", "تعطيل", "إيقاف", "off"]:
        if not is_active:
            await message.reply_text("**وضـع الـصـيـانـة مـعـطّـل بـالـفـعـل!**")
        else:
            await maintenance_off()
            await message.reply_text("**تـم تـعـطـيـل وضـع الـصـيـانـة.**\n\nيمكن للجميع استخدام البوت الآن.")
            
    else:
        await message.reply_text("**أمـر غـيـر صـحـيـح.**")


# 3. أوامر السجل (Logger)
@app.on_message(filters.command(["logger", "السجل"], prefixes=["/", "!", ".", ""]) & filters.user(OWNER_ID))
async def logger_toggle(client, message: Message):
    if len(message.command) != 2:
        return await message.reply_text(
            "**طـريـقـة اسـتـخـدام إشـعـارات الـسـجـل:**\n\n"
            "• لـتـفـعـيـل الـسـجـل ارسـل: **السجل تفعيل**\n"
            "• لـتـعـطـيـل الـسـجـل ارسـل: **السجل تعطيل**"
        )

    state = message.text.split(None, 1)[1].strip().lower()
    
    try:
        if state in ["enable", "تفعيل", "on"]:
            if await is_on_off(2):
                await message.reply_text("**إشـعـارات الـسـجـل مـفـعّـلـة بـالـفـعـل!**")
            else:
                await add_on(2)
                await message.reply_text("**تـم تـفـعـيـل إشـعـارات الـسـجـل.**")

        elif state in ["disable", "تعطيل", "off"]:
            if not await is_on_off(2):
                await message.reply_text("**إشـعـارات الـسـجـل مـعـطّـلـة بـالـفـعـل!**")
            else:
                await add_off(2)
                await message.reply_text("**تـم تـعـطـيـل إشـعـارات الـسـجـل.**")
        else:
            await message.reply_text("**أمـر غـيـر صـحـيـح.**")
    except Exception as e:
        await message.reply_text(f"**حدث خطأ:** {e}")


# 4. أمر سحب ملف السجل
@app.on_message(filters.command(["logs", "ملف السجل"], prefixes=["/", "!", ".", ""]) & filters.user(OWNER_ID))
async def get_log_file(client, message: Message):
    try:
        if os.path.exists("log.txt"):
            await message.reply_document(document="log.txt", caption="**سـجـلات الـبـوت**")
        else:
            await message.reply_text("**لا يـوجـد مـلـف سـجـلـات.**")
    except Exception as e:
        await message.reply_text(f"خطأ: {e}")
