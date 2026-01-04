from pyrogram import Client
from pyrogram.enums import ParseMode
import config
from ..logging import LOGGER


class Hotty(Client):
    def __init__(self):
        LOGGER(__name__).info(f"جاري بدء تشغيل البوت...")
        super().__init__(
            name="BrandrdXMusic",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=True,
            parse_mode=ParseMode.HTML,
        )

    async def start(self):
        await super().start()
        self.id = self.me.id
        self.name = self.me.first_name + " " + (self.me.last_name or "")
        self.username = self.me.username
        self.mention = self.me.mention

        # --- محاولة إرسال رسالة السجل (بدون إيقاف البوت) ---
        try:
            await self.send_message(
                chat_id=config.LOGGER_ID,
                text=f"<u><b>» {self.mention} بـدأ الـعـمـل :</b></u>\n\nالآيـدي : <code>{self.id}</code>\nالاسـم : {self.name}\nالـمـعـرف : @{self.username}",
            )
        except Exception:
            # لو حصل أي خطأ (البوت مش أدمن، القناة مش موجودة.. إلخ)
            # هيتجاهل الأمر ويكمل تشغيل البوت عادي جداً
            pass
        
        # تم إزالة التحقق من صلاحيات الأدمن (get_chat_member) عشان ميضربش

        LOGGER(__name__).info(f"تم بدء تشغيل بوت الميوزك باسم {self.name}")

    async def stop(self):
        await super().stop()
