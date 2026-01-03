# ==== PATCH for pyrogram GroupcallForbidden ====
import pyrogram.errors

if not hasattr(pyrogram.errors, "GroupcallForbidden"):
    class GroupcallForbidden(Exception):
        pass
    pyrogram.errors.GroupcallForbidden = GroupcallForbidden
# =============================================

import asyncio
import importlib
from pyrogram import idle

import config
from BrandrdXMusic import LOGGER, app, userbot
from BrandrdXMusic.core.call import Hotty
from BrandrdXMusic.misc import sudo
from BrandrdXMusic.plugins import ALL_MODULES
from BrandrdXMusic.core.database import get_banned_users, get_gbanned
from config import BANNED_USERS


async def init():
    # التحقق من وجود أكواد السيشن للحسابات المساعدة
    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        LOGGER(__name__).error("لم يتم العثور على كود سيشن الحساب المساعد... جاري الخروج")
        exit(1)

    # تهيئة المشرفين وقوائم الحظر
    await sudo()
    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)

        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except Exception:
        pass

    # تشغيل البوت الأساسي
    await app.start()

    # استدعاء ملفات البلجنز
    for module_name in ALL_MODULES:
        importlib.import_module(f"BrandrdXMusic.plugins.{module_name}")
    LOGGER("BrandrdXMusic.plugins").info("تم استدعاء ملفات البوت بنجاح")

    # تشغيل الحساب المساعد و PyTgCalls
    await userbot.start()
    await Hotty.start()
    await Hotty.decorators()

    # رسالة تشغيل
    LOGGER("BrandrdXMusic").info(
        "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🤍 تم تشغيل البوت بنجاح\n"
        "🧚 المطور: @S_G0C7\n"
        "♥️ قناة السورس: https://t.me/SourceBoda\n"
        "💝 جروب الدعم: https://t.me/music0587\n"
        "💕 شكرا لاستخدامك سورس بودا\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    await idle()

    await app.stop()
    await userbot.stop()
    LOGGER("BrandrdXMusic").info("تم ايقاف البوت بنجاح")


if __name__ == "__main__":
    asyncio.run(init())
