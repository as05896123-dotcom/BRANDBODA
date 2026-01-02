import asyncio
from pyrogram import Client
import config
from ..logging import LOGGER

assistants = []
assistantids = []


class Userbot(Client):
    def __init__(self):
        self.one = Client(
            name="BrandrdXMusic1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
            # تم إزالة no_updates=True لأنها تسبب مشاكل في الإصدارات الجديدة
        )
            
        self.two = Client(
            name="BrandrdXMusic2",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING2),
        )
        self.three = Client(
            name="BrandrdXMusic3",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING3),
        )
        self.four = Client(
            name="BrandrdXMusic4",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING4),
        )
        self.five = Client(
            name="BrandrdXMusic5",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING5),
        )

    async def start(self):
        LOGGER(__name__).info(f"جاري تشغيل الحسابات المساعدة...")

        if config.STRING1:
            await self.one.start()
            try:
                await self.one.join_chat(config.LOGGER_ID)
                await self.one.send_message(config.LOGGER_ID, "تم تشغيل الحساب المساعد الأول")
            except:
                LOGGER(__name__).error(
                    "فشل الحساب المساعد 1 في الوصول إلى مجموعة السجل. تأكد من إضافته ورفعه مشرف!"
                )
            
            assistants.append(1)
            try:
                self.one.id = self.one.me.id
                self.one.name = self.one.me.mention
                self.one.username = self.one.me.username
                assistantids.append(self.one.id)
                LOGGER(__name__).info(f"تم تشغيل المساعد الأول باسم {self.one.name}")
            except:
                LOGGER(__name__).error("حدث خطأ في جلب بيانات المساعد الأول")

        if config.STRING2:
            await self.two.start()
            try:
                await self.two.join_chat(config.LOGGER_ID)
                await self.two.send_message(config.LOGGER_ID, "تم تشغيل الحساب المساعد الثاني")
            except:
                LOGGER(__name__).error(
                    "فشل الحساب المساعد 2 في الوصول إلى مجموعة السجل. تأكد من إضافته ورفعه مشرف!"
                )
            
            assistants.append(2)
            try:
                self.two.id = self.two.me.id
                self.two.name = self.two.me.mention
                self.two.username = self.two.me.username
                assistantids.append(self.two.id)
                LOGGER(__name__).info(f"تم تشغيل المساعد الثاني باسم {self.two.name}")
            except:
                 LOGGER(__name__).error("حدث خطأ في جلب بيانات المساعد الثاني")

        if config.STRING3:
            await self.three.start()
            try:
                await self.three.join_chat(config.LOGGER_ID)
                await self.three.send_message(config.LOGGER_ID, "تم تشغيل الحساب المساعد الثالث")
            except:
                LOGGER(__name__).error(
                    "فشل الحساب المساعد 3 في الوصول إلى مجموعة السجل. تأكد من إضافته ورفعه مشرف!"
                )
            
            assistants.append(3)
            try:
                self.three.id = self.three.me.id
                self.three.name = self.three.me.mention
                self.three.username = self.three.me.username
                assistantids.append(self.three.id)
                LOGGER(__name__).info(f"تم تشغيل المساعد الثالث باسم {self.three.name}")
            except:
                LOGGER(__name__).error("حدث خطأ في جلب بيانات المساعد الثالث")

        if config.STRING4:
            await self.four.start()
            try:
                await self.four.join_chat(config.LOGGER_ID)
                await self.four.send_message(config.LOGGER_ID, "تم تشغيل الحساب المساعد الرابع")
            except:
                LOGGER(__name__).error(
                    "فشل الحساب المساعد 4 في الوصول إلى مجموعة السجل. تأكد من إضافته ورفعه مشرف!"
                )
            
            assistants.append(4)
            try:
                self.four.id = self.four.me.id
                self.four.name = self.four.me.mention
                self.four.username = self.four.me.username
                assistantids.append(self.four.id)
                LOGGER(__name__).info(f"تم تشغيل المساعد الرابع باسم {self.four.name}")
            except:
                LOGGER(__name__).error("حدث خطأ في جلب بيانات المساعد الرابع")

        if config.STRING5:
            await self.five.start()
            try:
                await self.five.join_chat(config.LOGGER_ID)
                await self.five.send_message(config.LOGGER_ID, "تم تشغيل الحساب المساعد الخامس")
            except:
                LOGGER(__name__).error(
                    "فشل الحساب المساعد 5 في الوصول إلى مجموعة السجل. تأكد من إضافته ورفعه مشرف!"
                )
            
            assistants.append(5)
            try:
                self.five.id = self.five.me.id
                self.five.name = self.five.me.mention
                self.five.username = self.five.me.username
                assistantids.append(self.five.id)
                LOGGER(__name__).info(f"تم تشغيل المساعد الخامس باسم {self.five.name}")
            except:
                LOGGER(__name__).error("حدث خطأ في جلب بيانات المساعد الخامس")

    async def stop(self):
        LOGGER(__name__).info(f"جاري إيقاف الحسابات المساعدة...")
        try:
            if config.STRING1:
                await self.one.stop()
            if config.STRING2:
                await self.two.stop()
            if config.STRING3:
                await self.three.stop()
            if config.STRING4:
                await self.four.stop()
            if config.STRING5:
                await self.five.stop()
        except:
            pass
