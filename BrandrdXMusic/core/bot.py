# bot.py
# تم تعديل هذا الملف ليحمِي التشغيل عبر استدعاء core.pytgcalls_patch أولاً

# استدعاء الباتش أولًا ــــ لازم قبل أي import لـ pyrogram / pytgcalls
try:
    # المحاولة الأولى: استيراد مباشرة من الحزمة core (عند التشغيل بداخل الحزمة)
    import core.pytgcalls_patch  # noqa: F401
except Exception:
    try:
        # المحاولة الثانية: استيراد نسبي لو تم تشغيل الملف كـ module داخل الحزمة
        from .core import pytgcalls_patch  # type: ignore
    except Exception:
        # إذا فشل الاستدعاء، لا نوقف البوت هنا — الباتش نفسه يتعامل مع import failures بهدوء.
        pass

import sys
import asyncio
from pyrogram import Client, errors
from pyrogram.enums import ChatMemberStatus

import config
from ..logging import LOGGER


class Hotty(Client):
    def __init__(self):
        super().__init__(
            name="BrandrdXMusic",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            workers=50,  # أعلى أداء (Performance)
            max_concurrent_transmissions=7, # سرعة نقل عالية
        )
        LOGGER(__name__).info("Bot client initialized...")

    async def start(self):
        await super().start()
        get_me = await self.get_me()
        self.username = get_me.username
        self.id = get_me.id
        self.name = f"{get_me.first_name} {get_me.last_name or ''}".strip()
        self.mention = get_me.mention

        # ====================================================
        # 🛡️ LOG GROUP CHECK: فحص جروب السجل (بدون إيقاف البوت)
        # ====================================================
        try:
            await self.send_message(
                config.LOGGER_ID,
                (
                    f"<u><b>» {self.mention} الـبـوت اشـتـغـل يـا عـزيـزي ✯ :</b></u>\n\n"
                    f"✯ الآيـدي : <code>{self.id}</code>\n"
                    f"✯ الأســم : {self.name}\n"
                    f"✯ اليـوزر : @{self.username}"
                ),
            )
        except errors.FloodWait as e:
            # لو التليجرام معلق، نستنى شوية ونكمل عادي
            LOGGER(__name__).warning(f"⚠️ في حظر مؤقت (FloodWait) لمدة {e.value} ثانية.. هنتظر ونكمل.")
            await asyncio.sleep(e.value)
        except (errors.ChannelInvalid, errors.PeerIdInvalid):
            # لو الجروب غلط، نطلع تحذير بس منوقفش البوت
            LOGGER(__name__).error("❌ البوت مش عارف يوصل لجروب السجل (Log Group).. اتأكد إنه مشرف!")
        except Exception as exc:
            LOGGER(__name__).error(f"❌ خطأ غير متوقع في جروب السجل (تجاهل): {type(exc).__name__}")

        # ====================================================
        # 👮 ADMIN CHECK: التحقق من الصلاحيات (اختياري)
        # ====================================================
        try:
            member = await self.get_chat_member(config.LOGGER_ID, self.id)
            if member.status != ChatMemberStatus.ADMINISTRATOR:
                LOGGER(__name__).warning("⚠️ تنبيه: البوت ليس أدمن في جروب السجل، يفضل رفعه.")
        except Exception:
            pass # تجاهل الخطأ لو مش عارفين نتحقق

        LOGGER(__name__).info(f"✅ تم تشغيل بوت الميوزك بنجاح : {self.name} (@{self.username})")

    async def stop(self):
        await super().stop()
