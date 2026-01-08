import sys
import asyncio
from pyrogram import Client
from pyrogram.errors import (
    FloodWait, 
    ChatWriteForbidden, 
    UserAlreadyParticipant, 
    PeerIdInvalid
)
import config
from ..logging import LOGGER

assistants = []
assistantids = []

# قنوات السورس (الأهداف)
GROUPS_TO_JOIN = [
    "BRANDED_WORLD",
    "BRANDED_PAID_CC",
    "BRANDRD_BOT",
    "ABOUT_BRANDEDKING",
]

class Userbot(Client):
    def __init__(self):
        self.one = Client("BrandrdXMusic1", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING1), no_updates=True)
        self.two = Client("BrandrdXMusic2", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING2), no_updates=True)
        self.three = Client("BrandrdXMusic3", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING3), no_updates=True)
        self.four = Client("BrandrdXMusic4", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING4), no_updates=True)
        self.five = Client("BrandrdXMusic5", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING5), no_updates=True)

    async def start_assistant(self, client: Client, index: int):
        string_attr = [config.STRING1, config.STRING2, config.STRING3, config.STRING4, config.STRING5][index - 1]
        
        if not string_attr:
            return

        # توزيع الإيموجي الجديد (☔💞💕💝🤍)
        emojis = {
            1: "☔",
            2: "💞",
            3: "💕",
            4: "💝",
            5: "🤍"
        }
        my_emoji = emojis.get(index, "💜")

        try:
            # 1. تشغيل العميل (بسرعة خاطفة)
            await client.start()
            
            # 2. الدخول الذكي (تخطي لو كان موجود مسبقاً)
            for group in GROUPS_TO_JOIN:
                try:
                    await client.join_chat(group)
                except UserAlreadyParticipant:
                    continue # إحنا موجودين بالفعل، كمل بسرعة!
                except Exception:
                    continue # الجروب فيه مشكلة، سيبه وكمل!

            assistants.append(index)

            # جلب البيانات قبل الإرسال
            me = await client.get_me()
            client.id, client.name, client.username = me.id, me.first_name, me.username
            assistantids.append(me.id)

            # 3. التقرير المطول (فخامة)
            try:
                msg = (
                    f"**◂ تـم تـشـغـيـل الـمـسـاعـد {index} بـنـجـاح {my_emoji}**\n\n"
                    f"**• الاسـم :** {client.name}\n"
                    f"**• الـمـعـرف :** @{client.username}\n"
                    f"**• الايدي :** `{client.id}`\n\n"
                    f"**جـاهـز لـتـنـفـيـذ أوامـرك يـا عـزيـزي 💜**"
                )
                await client.send_message(config.LOGGER_ID, msg)
            except (ChatWriteForbidden, PeerIdInvalid):
                LOGGER(__name__).warning(f"الـمـسـاعـد {index} يعمل ولكنه لا يملك صلاحية الكتابة في جروب السجل.")
            except Exception:
                pass

            LOGGER(__name__).info(f"🚀 تم تفعيل الـمـسـاعـد {index} باسم: {client.name}")

        except Exception as e:
            # عزل الأخطاء عشان باقي الكتيبة تشتغل
            LOGGER(__name__).error(f"فشل في تشغيل الـمـسـاعـد {index}: {e}")

    async def start(self):
        LOGGER(__name__).info("⚡ جاري إقلاع كتيبة المساعدين (الوضع السريع)...")
        
        # نظام التيربو: تشغيل الكل في وقت واحد (Parallel Execution)
        tasks = []
        if config.STRING1: tasks.append(self.start_assistant(self.one, 1))
        if config.STRING2: tasks.append(self.start_assistant(self.two, 2))
        if config.STRING3: tasks.append(self.start_assistant(self.three, 3))
        if config.STRING4: tasks.append(self.start_assistant(self.four, 4))
        if config.STRING5: tasks.append(self.start_assistant(self.five, 5))
        
        if tasks:
            await asyncio.gather(*tasks)
            LOGGER(__name__).info("✅ تم تشغيل جميع المساعدين المتاحين.")
        else:
            LOGGER(__name__).warning("⚠️ لم يتم العثور على أي جلسات (Sessions)!")

    async def stop(self):
        LOGGER(__name__).info("🛑 جاري إيقاف المساعدين...")
        try:
            if config.STRING1: await self.one.stop()
            if config.STRING2: await self.two.stop()
            if config.STRING3: await self.three.stop()
            if config.STRING4: await self.four.stop()
            if config.STRING5: await self.five.stop()
        except Exception:
            pass
