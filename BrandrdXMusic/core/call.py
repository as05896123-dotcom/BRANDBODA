# core/call.py

import os
import asyncio
from datetime import datetime, timedelta

from pyrogram import Client
from pyrogram.raw.functions.phone import CreateGroupCall
from pyrogram.errors import ChatAdminRequired

from pytgcalls import PyTgCalls
from pytgcalls.exceptions import AlreadyInCallError, NoActiveGroupCall
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality, Update
from pytgcalls.types.stream import StreamAudioEnded

import config
from BrandrdXMusic import LOGGER, app, YouTube
from BrandrdXMusic.misc import db

# ===== Database (NEW STRUCTURE) =====
from BrandrdXMusic.core.database.assistants import group_assistant
from BrandrdXMusic.core.database.settings import (
    get_lang,
    get_loop,
    set_loop,
    is_autoend,
)
from BrandrdXMusic.core.database.queries import set_queries

from BrandrdXMusic.utils.database import (
    add_active_chat,
    add_active_video_chat,
    remove_active_chat,
    remove_active_video_chat,
    music_on,
)

from BrandrdXMusic.utils.exceptions import AssistantErr
from BrandrdXMusic.utils.stream.autoclear import auto_clean
from strings import get_string


# =======================
# Globals
# =======================

AUTOEND = {}
QUEUE_LOCK = asyncio.Lock()


# =======================
# Helpers
# =======================

async def _clear_(chat_id: int):
    async with QUEUE_LOCK:
        db[chat_id] = []
    AUTOEND.pop(chat_id, None)
    await remove_active_chat(chat_id)
    await remove_active_video_chat(chat_id)


# =======================
# Call Class
# =======================

class Call:
    def __init__(self):

        # -------- Userbots --------
        self.userbot1 = Client(
            "BrandrdXMusic1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
        )
        self.userbot2 = Client(
            "BrandrdXMusic2",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING2),
        )
        self.userbot3 = Client(
            "BrandrdXMusic3",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING3),
        )
        self.userbot4 = Client(
            "BrandrdXMusic4",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING4),
        )
        self.userbot5 = Client(
            "BrandrdXMusic5",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING5),
        )

        # -------- PyTgCalls --------
        self.one = PyTgCalls(self.userbot1)
        self.two = PyTgCalls(self.userbot2)
        self.three = PyTgCalls(self.userbot3)
        self.four = PyTgCalls(self.userbot4)
        self.five = PyTgCalls(self.userbot5)

    # =======================
    # Basic Controls
    # =======================

    async def pause_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.pause_stream(chat_id)

    async def resume_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.resume_stream(chat_id)

    async def mute_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.mute_stream(chat_id)

    async def unmute_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.unmute_stream(chat_id)

    async def stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            await _clear_(chat_id)
            await assistant.leave(chat_id)
        except Exception:
            pass

    # =======================
    # Join Call
    # =======================

    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link: str,
        video: bool = False,
    ):
        assistant = await group_assistant(self, chat_id)
        language = await get_lang(chat_id)
        _ = get_string(language)

        if not link.startswith("http") and not os.path.isfile(link):
            raise AssistantErr(_["call_7"])

        stream = MediaStream(
            link,
            audio_parameters=AudioQuality.HIGH,
            video_parameters=VideoQuality.SD_480p if video else None,
            video_flags=None if video else MediaStream.IGNORE,
        )

        try:
            await assistant.play(chat_id, stream)

        except NoActiveGroupCall:
            try:
                await app.invoke(
                    CreateGroupCall(
                        peer=await app.resolve_peer(chat_id),
                        random_id=app.rnd_id(),
                    )
                )
                await assistant.play(chat_id, stream)
            except (ChatAdminRequired, Exception):
                raise AssistantErr(_["call_8"])

        except AlreadyInCallError:
            raise AssistantErr(_["call_9"])

        await add_active_chat(chat_id)
        await music_on(chat_id)
        await set_queries(1)

        if video:
            await add_active_video_chat(chat_id)

        if await is_autoend():
            asyncio.create_task(self.autoend_watcher(chat_id))

    # =======================
    # Change Stream
    # =======================

    async def change_stream(self, client: PyTgCalls, chat_id: int):
        async with QUEUE_LOCK:
            queue = db.get(chat_id)
            if not queue:
                await self.stop_stream(chat_id)
                return

            loop_count = await get_loop(chat_id)
            if loop_count == 0:
                popped = queue.pop(0)
            else:
                await set_loop(chat_id, loop_count - 1)
                popped = None

        await auto_clean(popped)

        async with QUEUE_LOCK:
            if not db.get(chat_id):
                await self.stop_stream(chat_id)
                return
            data = db[chat_id][0]

        file = data["file"]
        videoid = data["vidid"]
        streamtype = data["streamtype"]

        if file.startswith(("vid_", "live_")):
            link = await YouTube.video(videoid, file.startswith("live_"))
        else:
            link = file

        if not link.startswith("http") and not os.path.isfile(link):
            await self.stop_stream(chat_id)
            return

        stream = MediaStream(
            link,
            audio_parameters=AudioQuality.HIGH,
            video_parameters=VideoQuality.SD_480p if streamtype == "video" else None,
            video_flags=None if streamtype == "video" else MediaStream.IGNORE,
        )

        try:
            await client.change_stream(chat_id, stream)
        except Exception as e:
            LOGGER(__name__).error(e)
            await self.stop_stream(chat_id)

    # =======================
    # Auto-End Watcher
    # =======================

    async def autoend_watcher(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        AUTOEND[chat_id] = datetime.now() + timedelta(minutes=1)

        while True:
            await asyncio.sleep(20)

            if chat_id not in AUTOEND:
                return

            if datetime.now() < AUTOEND[chat_id]:
                continue

            try:
                participants = await assistant.get_participants(chat_id)
            except Exception:
                continue

            if len(participants) <= 1:
                await self.stop_stream(chat_id)
                AUTOEND.pop(chat_id, None)
                return

    # =======================
    # Start & Decorators
    # =======================

    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls Clients...")
        await self.one.start()
        await self.two.start()
        await self.three.start()
        await self.four.start()
        await self.five.start()

    async def decorators(self):

        @self.one.on_stream_end()
        async def _(client, update: Update):
            if isinstance(update, StreamAudioEnded):
                await self.change_stream(client, update.chat_id)

        @self.two.on_stream_end()
        async def _(client, update: Update):
            if isinstance(update, StreamAudioEnded):
                await self.change_stream(client, update.chat_id)

        @self.three.on_stream_end()
        async def _(client, update: Update):
            if isinstance(update, StreamAudioEnded):
                await self.change_stream(client, update.chat_id)

        @self.four.on_stream_end()
        async def _(client, update: Update):
            if isinstance(update, StreamAudioEnded):
                await self.change_stream(client, update.chat_id)

        @self.five.on_stream_end()
        async def _(client, update: Update):
            if isinstance(update, StreamAudioEnded):
                await self.change_stream(client, update.chat_id)


# =======================
# Instance
# =======================

Hotty = Call()
