import os
from pyrogram import filters
from pyrogram.types import Message
from BrandrdXMusic import app
from config import OWNER_ID, LOGGER_ID

# [CORE MIGRATION] استيراد دوال قاعدة البيانات
from BrandrdXMusic.core.database import (
    is_maintenance,
    maintenance_off,
    maintenance_on,
    is_on_off,
    add_on,
    add_off,
)

# --- دالة مساعدة لفحص الصيانة (تم التعديل لمنع التشغيل التلقائي) ---
async def check_maint():
    try:
        # نحاول جلب الحالة
        state = await is_maintenance()
        # إذا كانت الحالة None (غير محددة)، نعتبرها False (معطلة)
        if state is None:
            return False
        return state
    except TypeError:
        # محاولة أخرى لبعض نسخ قواعد البيانات
        try:
            state = await is_maintenance(1)
            if state is None:
                return False
            return state
        except Exception:
            return False
    except Exception:
        # في حال حدوث أي خطأ، نعتبر الصيانة معطلة ليعمل البوت
        return False
# -------------------------


# ==========================================================
# 1. الحارس (Maintenance Check Middleware)
# ==========================================================
@app.on_message(filters.all & ~filters.user(OWNER_ID), group=-1)
async def maintenance_check(client, message: Message):
    try:
        if not message.text:
            return
            
        if await check_maint():
            await message.reply_text(
                "🥀 **الـبـوت فـي وضـع الـصـيـانـة حـالـيـاً**\n\nنـحـن نـعـمـل عـلـى تـحـديـث الـبـوت، يـرجـى الـمـحـاولـة لاحـقـاً."
            )
            message.stop_propagation()
    except Exception:
        pass


# ==========================================================
# 2. أوامر الصيانة (Maintenance)
# ==========================================================
@app.on_message(filters.command(["تفعيل الصيانة", "تعطيل الصيانة", "maintenance", "الصيانة"], prefixes=["", "/", "!", "."]) & filters.user(OWNER_ID))
async def maintenance(client, message: Message):
    full_text = message.text.lower()
    is_active = await check_maint()

    # --- التفعيل ---
    if "تفعيل" in full_text or "enable" in full_text or "on" in full_text.split():
        if is_active:
            await message.reply_text("🧚 **وضـع الـصـيـانـة مـفـعّـل بـالـفـعـل.**")
        else:
            await maintenance_on()
            await message.reply_text("🥀 **تـم تـفـعـيـل وضـع الـصـيـانـة.**\n\nلن يستطيع أحد استخدام البوت غير المطورين.")
            
    # --- التعطيل ---
    elif "تعطيل" in full_text or "disable" in full_text or "off" in full_text.split():
        if not is_active:
            await message.reply_text("🧚 **وضـع الـصـيـانـة مـعـطّـل بـالـفـعـل.**")
        else:
            await maintenance_off()
            await message.reply_text("🥀 **تـم تـعـطـيـل وضـع الـصـيـانـة.**\n\nيمكن للجميع استخدام البوت الآن.")
            
    # --- التوجيه ---
    else:
        await message.reply_text(
            "🥀 **طـريـقـة الاسـتـخـدام :**\n\n"
            "• **تفعيل الصيانة**\n"
            "• **تعطيل الصيانة**"
        )


# ==========================================================
# 3. أوامر السجل (Logger)
# ==========================================================
@app.on_message(filters.command(["تفعيل السجل", "تعطيل السجل", "logger", "السجل"], prefixes=["", "/", "!", "."]) & filters.user(OWNER_ID))
async def logger_toggle(client, message: Message):
    full_text = message.text.lower()
    
    try:
        # --- التفعيل ---
        if "تفعيل" in full_text or "enable" in full_text or "on" in full_text.split():
            if await is_on_off(2):
                await message.reply_text("🧚 **إشـعـارات الـسـجـل مـفـعّـلـة بـالـفـعـل.**")
            else:
                await add_on(2)
                await message.reply_text("🥀 **تـم تـفـعـيـل إشـعـارات الـسـجـل.**")

        # --- التعطيل ---
        elif "تعطيل" in full_text or "disable" in full_text or "off" in full_text.split():
            if not await is_on_off(2):
                await message.reply_text("🧚 **إشـعـارات الـسـجـل مـعـطّـلـة بـالـفـعـل.**")
            else:
                await add_off(2)
                await message.reply_text("🥀 **تـم تـعـطـيـل إشـعـارات الـسـجـل.**")
        
        # --- التوجيه ---
        else:
            await message.reply_text(
                "🥀 **طـريـقـة الاسـتـخـدام :**\n\n"
                "• **تفعيل السجل**\n"
                "• **تعطيل السجل**"
            )
            
    except Exception as e:
        await message.reply_text(f"🥀 **حدث خطأ:** {e}")


# ==========================================================
# 4. أمر سحب ملف السجل
# ==========================================================
@app.on_message(filters.command(["logs", "ملف السجل"], prefixes=["", "/", "!", "."]) & filters.user(OWNER_ID))
async def get_log_file(client, message: Message):
    try:
        if os.path.exists("log.txt"):
            await message.reply_document(document="log.txt", caption="🥀 **سـجـلات الـبـوت (System Logs)**")
        elif os.path.exists("cookies/logs.csv"):
             await message.reply_document(document="cookies/logs.csv", caption="🥀 **سـجـلات الـبـوت (Activity Logs)**")
        else:
            await message.reply_text("🧚 **لا يـوجـد مـلـف سـجـلات حـالـيـاً.**")
    except Exception as e:
        await message.reply_text(f"🥀 **خطأ:** {e}")
