import sys
from pyrogram import Client
import config
from ..logging import LOGGER

assistants = []
assistantids = []

# قنوات السورس القديم عشان المساعد يدخلها
GROUPS_TO_JOIN = [
    "BRANDED_WORLD",
    "BRANDED_PAID_CC",
    "BRANDRD_BOT",
    "ABOUT_BRANDEDKING",
]

class Userbot(Client):
    def __init__(self):
        self.one = Client(
            "BrandrdXMusic1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
            no_updates=True,
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

    async def start_assistant(self, client: Client, index: int):
        string_attr = [
            config.STRING1,
            config.STRING2,
            config.STRING3,
            config.STRING4,
            config.STRING5,
        ][index - 1]
        
        if not string_attr:
            return

        # توزيع الإيموجي لكل مساعد
        emojis = {
            1: "☔",
            2: "🤍",
            3: "🧚",
            4: "✨",
            5: "🎸"
        }
        my_emoji = emojis.get(index, "⚡️") # لو الرقم غريب يحط علامة البرق

        try:
            await client.start()
            # دخول القنوات تلقائي
            for group in GROUPS_TO_JOIN:
                try:
                    await client.join_chat(group)
                except Exception:
                    pass

            assistants.append(index)

            try:
                # الرسالة بالعربي مع الإيموجي الخاص بكل مساعد
                await client.send_message(
                    config.LOGGER_ID, 
                    f"تم تشغيل الحساب المساعد {index} يا عزيزي {my_emoji}"
                )
            except Exception:
                LOGGER(__name__).error(
                    f"Assistant {index} can't access the log group. Check permissions!"
                )
                sys.exit()

            me = await client.get_me()
            client.id, client.name, client.username = me.id, me.first_name, me.username
            assistantids.append(me.id)

            LOGGER(__name__).info(f"Assistant {index} Started as {client.name}")

        except Exception as e:
            LOGGER(__name__).error(f"Failed to start Assistant {index}: {e}")

    async def start(self):
        LOGGER(__name__).info("Starting Assistants...")
        await self.start_assistant(self.one, 1)
        await self.start_assistant(self.two, 2)
        await self.start_assistant(self.three, 3)
        await self.start_assistant(self.four, 4)
        await self.start_assistant(self.five, 5)

    async def stop(self):
        LOGGER(__name__).info("Stopping Assistants...")
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
        except Exception as e:
            LOGGER(__name__).error(f"Error while stopping assistants: {e}")
