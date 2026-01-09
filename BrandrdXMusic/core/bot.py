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
            workers=50,
            max_concurrent_transmissions=7,
        )
        LOGGER(__name__).info("Bot client initialized...")

    async def start(self):
        await super().start()
        me = await self.get_me()
        self.username, self.id = me.username, me.id
        self.name = f"{me.first_name} {me.last_name or ''}".strip()
        self.mention = me.mention

        # 1. محاولة إرسال رسالة الترحيب مع حماية ضد الحظر
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
            # 🛡️ الحماية: لو فيه حظر، استنى وكمل عادي ومتفصلش
            LOGGER(__name__).warning(f"⚠️ في حظر مؤقت (FloodWait) لمدة {e.value} ثانية.. هنتظر ونكمل.")
            await asyncio.sleep(e.value)
        except (errors.ChannelInvalid, errors.PeerIdInvalid):
            LOGGER(__name__).error("❌ البوت مش عارف يوصل لجروب السجل (Log Group).. اتأكد إنه مشرف!")
            # مش هنعمل exit عشان البوت يشتغل حتى لو اللوج بايظ
        except Exception as exc:
            LOGGER(__name__).error(f"❌ خطأ في جروب السجل (تجاهل): {type(exc).__name__}")

        # 2. التأكد من صلاحيات الأدمن (بدون ما نقفل البوت لو فشل)
        try:
            member = await self.get_chat_member(config.LOGGER_ID, self.id)
            if member.status != ChatMemberStatus.ADMINISTRATOR:
                LOGGER(__name__).warning("⚠️ تنبيه: البوت ليس أدمن في جروب السجل، يفضل رفعه.")
        except Exception as e:
            # تجاهل الخطأ وكمل تشغيل
            LOGGER(__name__).warning(f"⚠️ فشل التحقق من صلاحيات الأدمن (تجاهل): {e}")

        LOGGER(__name__).info(f"✅ تم تشغيل بوت الميوزك بنجاح : {self.name} (@{self.username})")

    async def stop(self):
        await super().stop()
