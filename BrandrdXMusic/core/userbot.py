import sys
import asyncio
from pyrogram import Client
import config
from ..logging import LOGGER

assistants = []
assistantids = []

class Userbot(Client):
    def __init__(self):
        self.one = Client(
            "BrandrdXMusic1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
            no_updates=True, # بيمنع استلام تحديثات الشات لتخفيف الضغط
        )
        self.two = Client(
            "BrandrdXMusic2",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING2),
            no_updates=True,
        )
        self.three = Client(
            "BrandrdXMusic3",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING3),
            no_updates=True,
        )
        self.four = Client(
            "BrandrdXMusic4",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING4),
            no_updates=True,
        )
        self.five = Client(
            "BrandrdXMusic5",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING5),
            no_updates=True,
        )

    async def start(self):
        LOGGER(__name__).info("⚡ جاري إقلاع كتيبة المساعدين (الوضع السريع)...")
        
        clients = [
            (self.one, config.STRING1, 1, "☔"),
            (self.two, config.STRING2, 2, "🤍"),
            (self.three, config.STRING3, 3, "🧚"),
            (self.four, config.STRING4, 4, "✨"),
            (self.five, config.STRING5, 5, "🎸")
        ]

        for client, session, index, emoji in clients:
            if not session:
                continue

            try:
                await client.start()
                
                # جلب البيانات
                me = await client.get_me()
                client.id = me.id
                client.name = me.first_name
                client.username = me.username
                client.mention = me.mention
                
                assistants.append(index)
                assistantids.append(me.id)

                # محاولة إرسال رسالة لجروب السجل (بدون إجبار)
                try:
                    await client.send_message(
                        config.LOGGER_ID, 
                        f"🚀 تم تفعيل الـمـسـاعـد {index} يا عزيزي {emoji}\n👤 الاسم: {me.mention}"
                    )
                except Exception:
                    LOGGER(__name__).warning(f"⚠️ المساعد {index} شغال بس مش عارف يبعت في جروب السجل (تأكد إنه مشرف).")

                LOGGER(__name__).info(f"🚀 تم تفعيل الـمـسـاعـد {index} باسم: {client.name}")

            except Exception as e:
                LOGGER(__name__).error(f"❌ فشل تشغيل المساعد {index}: {e}")
                # هنا شلت sys.exit عشان لو مساعد واحد بايظ الباقي يكمل شغل

        LOGGER(__name__).info("✅ تم تشغيل جميع المساعدين المتاحين.")

    async def stop(self):
        LOGGER(__name__).info("🛑 جاري إيقاف المساعدين...")
        clients = [self.one, self.two, self.three, self.four, self.five]
        try:
            await asyncio.gather(
                *[c.stop() for c in clients if c.is_connected]
            )
        except:
            pass
