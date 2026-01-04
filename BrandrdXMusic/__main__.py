import asyncio
from pyrogram import idle, filters
import pyrogram.errors

# ==== PATCH for pyrogram GroupcallForbidden ====
if not hasattr(pyrogram.errors, "GroupcallForbidden"):
    class GroupcallForbidden(Exception):
        pass
    pyrogram.errors.GroupcallForbidden = GroupcallForbidden
# =============================================

import config
from BrandrdXMusic import LOGGER, app, userbot
from BrandrdXMusic.core.call import Hotty
from BrandrdXMusic.misc import sudo
# ❌ شلنا استدعاء ALL_MODULES لأنه كان بيعمل تجميد للبوت
from BrandrdXMusic.core.database import get_banned_users, get_gbanned
from config import BANNED_USERS


async def init():
    # 1. التحقق من المساعدين
    if not any([config.STRING1, config.STRING2, config.STRING3, config.STRING4, config.STRING5]):
        LOGGER(__name__).error("❌ لم يتم العثور على أي كود سيشن للحسابات المساعدة")
        return

    # 2. تحميل البيانات
    await sudo()
    try:
        for user_id in await get_gbanned():
            BANNED_USERS.add(int(user_id))
        for user_id in await get_banned_users():
            BANNED_USERS.add(int(user_id))
    except Exception as e:
        LOGGER(__name__).warning(f"Banned users load skipped: {e}")

    # 3. أمر التست (للتأكد فقط)
    @app.on_message(filters.command(["test", "تست", "alive"], prefixes=["/", "!", ".", ""]), group=-1)
    async def test_command(client, message):
        await message.reply_text("✅ **البوت شغال والملفات اتحملت صح!**\nعظمة يا ريس 🫡")

    # 4. تشغيل البوت (هنا بيتم تحميل الملفات تلقائي من bot.py)
    LOGGER("BrandrdXMusic").info("⏳ جاري تشغيل البوت وتحميل الملفات...")
    await app.start()
    
    # 5. تشغيل المساعدين والمكالمات
    await userbot.start()
    await Hotty.start()
    
    # محاولة تشغيل الديكوريتورز
    try:
        await Hotty.decorators()
    except:
        pass

    LOGGER("BrandrdXMusic").info(
        "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🤍 تم تشغيل البوت بنجاح\n"
        "🧚 المطور: @S_G0C7\n"
        "♥️ قناة السورس: https://t.me/SourceBoda\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    await idle()

    # 6. الإيقاف الآمن
    LOGGER("BrandrdXMusic").info("🛑 جاري إيقاف البوت...")
    try:
        await userbot.stop()
    except: pass
    
    try:
        await app.stop()
    except: pass


if __name__ == "__main__":
    asyncio.run(init())
