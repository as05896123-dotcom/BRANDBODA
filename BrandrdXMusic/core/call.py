"""
██████╗ ██████╗  █████╗ ███╗   ██╗██████╗ ██████╗ ██████╗ ██╗  ██╗
██╔══██╗██╔══██╗██╔══██╗████╗  ██║██╔══██╗██╔══██╗██╔══██╗╚██╗██╔╝
██████╔╝██████╔╝███████║██╔██╗ ██║██║  ██║██████╔╝██║  ██║ ╚███╔╝ 
██╔══██╗██╔══██╗██╔══██║██║╚██╗██║██║  ██║██╔══██╗██║  ██║ ██╔██╗ 
██████╔╝██║  ██║██║  ██║██║ ╚████║██████╔╝██║  ██║██████╔╝██╔╝ ██╗
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝

[ SYSTEM: THE ULTIMATE ENGINE - FINAL FIX ]
[ STATUS: ANTI-CRASH ENABLED ]
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Union
from functools import wraps

from pyrogram import Client
from pyrogram.errors import FloodWait, ChatAdminRequired, UserAlreadyParticipant
from pyrogram.types import InlineKeyboardMarkup

import config
from strings import get_string
from BrandrdXMusic import LOGGER, YouTube, app
from BrandrdXMusic.misc import db
from BrandrdXMusic.utils.database import (
    add_active_chat, add_active_video_chat, get_lang, get_loop, group_assistant,
    is_autoend, music_on, remove_active_chat, remove_active_video_chat, set_loop,
)
from BrandrdXMusic.utils.exceptions import AssistantErr
from BrandrdXMusic.utils.formatters import check_duration, seconds_to_min, speed_converter
from BrandrdXMusic.utils.stream.autoclear import auto_clean
from BrandrdXMusic.utils.thumbnails import get_thumb

try: 
    from BrandrdXMusic.utils.inline.play import stream_markup2
except ImportError: 
    stream_markup2 = None
from BrandrdXMusic.utils.inline.play import stream_markup

autoend = {}
counter = {}

# =======================================================================
# 🛡️ HELPER: Safe Execution
# =======================================================================
def safe_execution(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            LOGGER(__name__).error(f"⚠️ [ENGINE ERROR] in {func.__name__}: {e}")
            return None
    return wrapper

async def _clean_garbage(chat_id):
    try:
        popped = db.pop(chat_id, None)
        if popped: await auto_clean(popped)
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        await set_loop(chat_id, 0)
    except: pass

# =======================================================================
# 🚀 CORE CLASS
# =======================================================================
class Call:
    def __init__(self):
        # تعريف العملاء دون بدء التشغيل
        self.userbot1 = Client("BrandrdXMusic1", config.API_ID, config.API_HASH, session_string=config.STRING1) if config.STRING1 else None
        self.userbot2 = Client("BrandrdXMusic2", config.API_ID, config.API_HASH, session_string=config.STRING2) if config.STRING2 else None
        self.userbot3 = Client("BrandrdXMusic3", config.API_ID, config.API_HASH, session_string=config.STRING3) if config.STRING3 else None
        self.userbot4 = Client("BrandrdXMusic4", config.API_ID, config.API_HASH, session_string=config.STRING4) if config.STRING4 else None
        self.userbot5 = Client("BrandrdXMusic5", config.API_ID, config.API_HASH, session_string=config.STRING5) if config.STRING5 else None
        
        self.one = None
        self.two = None
        self.three = None
        self.four = None
        self.five = None
        self.active_calls = set()

    async def start(self):
        LOGGER(__name__).info("🛠️ Starting Audio Engine...")
        
        # 1. الاستيراد المتأخر لمنع المشاكل
        try:
            from pytgcalls import PyTgCalls
        except ImportError:
            LOGGER(__name__).error("CRITICAL: PyTgCalls is missing!")
            sys.exit(1)

        # 2. محاولة تطبيق الباتش (Soft Patch)
        # لو فشل مش هيوقف البوت، هيكمل عادي
        try:
            import pytgcalls.mtproto.pyrogram_client
            if hasattr(pytgcalls.mtproto.pyrogram_client.PyrogramClient, 'on_update'):
                original_update = pytgcalls.mtproto.pyrogram_client.PyrogramClient.on_update
                
                async def patched_update(self, client, update):
                    try:
                        if getattr(update, 'chat_id', None) == 0: return
                        await original_update(self, client, update)
                    except: pass
                
                pytgcalls.mtproto.pyrogram_client.PyrogramClient.on_update = patched_update
        except (ImportError, AttributeError):
            LOGGER(__name__).warning("⚠️ Could not apply PyTgCalls patch. Continuing anyway...")

        # 3. تشغيل العملاء بأمان (تجاهل الجلسات التالفة)
        clients_map = [
            (self.userbot1, 'one'), (self.userbot2, 'two'), 
            (self.userbot3, 'three'), (self.userbot4, 'four'), (self.userbot5, 'five')
        ]
        
        valid_tasks = []
        for client, attr in clients_map:
            if client:
                tg_cli = PyTgCalls(client)
                setattr(self, attr, tg_cli)
                valid_tasks.append(tg_cli.start())
        
        if valid_tasks:
            # تشغيل الكل، ولو واحد فشل البوت يكمل
            results = await asyncio.gather(*valid_tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    LOGGER(__name__).error(f"❌ Failed to start an assistant: {res}")
            
            await self.decorators()
            LOGGER(__name__).info("✅ Audio Engine Started.")
        else:
            LOGGER(__name__).warning("⚠️ No assistants found!")

    @safe_execution
    async def join_call(self, chat_id, original_chat_id, link, video=None, image=None):
        from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
        
        assistant = await group_assistant(self, chat_id)
        stream_mode = MediaStream.Flags.REQUIRED if video else MediaStream.Flags.IGNORE
        vid_quality = VideoQuality.HD_720p if video else None
        
        stream = MediaStream(link, AudioQuality.HIGH, vid_quality, video_flags=stream_mode)

        try:
            await assistant.play(chat_id, stream)
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
            await assistant.play(chat_id, stream)
        except UserAlreadyParticipant:
            pass
        except Exception as e:
            # لو الخطأ "No active call" نعيد رميه، غير كده نتجاهل
            if "No active group call" in str(e):
                raise AssistantErr("لم يتم العثور على مكالمة.")
        
        self.active_calls.add(chat_id)
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video: await add_active_video_chat(chat_id)

        if await is_autoend():
            try:
                if len(await assistant.get_participants(chat_id)) <= 1:
                    autoend[chat_id] = datetime.now() + timedelta(minutes=1)
            except: pass

    @safe_execution
    async def play(self, client, chat_id):
        from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
        
        check = db.get(chat_id)
        if not check:
            await _clean_garbage(chat_id)
            return

        popped = None
        loop = await get_loop(chat_id)
        try:
            if loop == 0: popped = check.pop(0)
            else:
                loop -= 1
                await set_loop(chat_id, loop)
            if popped: await auto_clean(popped)
            if not check:
                await _clean_garbage(chat_id)
                try: await client.leave_call(chat_id)
                except: pass
                return
        except:
            await _clean_garbage(chat_id)
            return

        track = check[0]
        queued = track["file"]
        vidid = track["vidid"]
        title = track["title"].title()
        user = track["by"]
        duration = track["dur"]
        orig_chat = track["chat_id"]
        stype = track["streamtype"]
        video = True if str(stype) == "video" else False
        
        if track.get("old_dur"):
            db[chat_id][0]["dur"] = track["old_dur"]
            db[chat_id][0]["seconds"] = track["old_second"]
            db[chat_id][0]["speed_path"], db[chat_id][0]["speed"] = None, 1.0

        lang = await get_lang(chat_id)
        _ = get_string(lang)

        def build_stream(path, is_vid):
            flags = MediaStream.Flags.REQUIRED if is_vid else MediaStream.Flags.IGNORE
            vid_q = VideoQuality.HD_720p if is_vid else None
            return MediaStream(path, AudioQuality.HIGH, vid_q, video_flags=flags)

        try:
            stream = None
            if "live_" in queued:
                n, link = await YouTube.video(vidid, True)
                if n == 0: return await self._safe_send(orig_chat, _["call_6"])
                stream = build_stream(link, video)
                await client.play(chat_id, stream)
                img = await get_thumb(vidid)
                btn = self._get_btn(_, vidid, chat_id)
                await self._safe_send_ui(orig_chat, img, title, duration, user, vidid, btn, chat_id, "tg", _)

            elif "vid_" in queued:
                mystic = await self._safe_send(orig_chat, _["call_7"])
                try: file_path, _ = await YouTube.download(vidid, mystic, videoid=True, video=video)
                except: 
                    if mystic: await mystic.edit_text(_["call_6"])
                    return
                stream = build_stream(file_path, video)
                await client.play(chat_id, stream)
                img = await get_thumb(vidid)
                btn = stream_markup(_, vidid, chat_id)
                if mystic: await mystic.delete()
                await self._safe_send_ui(orig_chat, img, title, duration, user, vidid, btn, chat_id, "stream", _)

            elif "index_" in queued:
                stream = build_stream(vidid, video)
                await client.play(chat_id, stream)
                btn = stream_markup(_, vidid, chat_id)
                await self._safe_send_ui(orig_chat, config.STREAM_IMG_URL, title, duration, user, vidid, btn, chat_id, "tg", _, custom_cap=_["stream_2"].format(user))

            else:
                stream = build_stream(queued, video)
                await client.play(chat_id, stream)
                link_txt = config.SUPPORT_CHAT if vidid in ["telegram", "soundcloud"] else f"https://t.me/{app.username}?start=info_{vidid}"
                
                if vidid == "telegram":
                    img = config.TELEGRAM_AUDIO_URL if str(stype) == "audio" else config.TELEGRAM_VIDEO_URL
                    btn = self._get_btn(_, "telegram", chat_id)
                elif vidid == "soundcloud":
                    img = config.SOUNCLOUD_IMG_URL
                    btn = self._get_btn(_, "soundcloud", chat_id)
                else:
                    img = await get_thumb(vidid)
                    btn = stream_markup(_, vidid, chat_id)

                await self._safe_send_ui(orig_chat, img, title, duration, user, link_txt, btn, chat_id, "tg", _)

        except Exception as e:
            LOGGER(__name__).error(f"Play Stream Error: {e}")
            await _clean_garbage(chat_id)

    async def _safe_send(self, chat_id, text):
        try: return await app.send_message(chat_id, text)
        except: return None

    async def _safe_send_ui(self, chat_id, photo, title, duration, user, link, btn, db_id, m_type, lang, custom_cap=None):
        if custom_cap: caption = custom_cap
        else: caption = lang["stream_1"].format(link, title[:23], duration, user)
        try:
            msg = await app.send_photo(chat_id, photo, caption=caption, reply_markup=InlineKeyboardMarkup(btn))
            if db_id in db: db[db_id][0]["mystic"], db[db_id][0]["markup"] = msg, m_type
        except: pass

    def _get_btn(self, lang, vidid, chat_id):
        if stream_markup2: return stream_markup2(lang, chat_id)
        return stream_markup(lang, vidid, chat_id)

    @safe_execution
    async def stop_stream(self, chat_id):
        assistant = await group_assistant(self, chat_id)
        await _clean_garbage(chat_id)
        if chat_id in self.active_calls:
            try: await assistant.leave_call(chat_id)
            except: pass
            finally: self.active_calls.discard(chat_id)

    @safe_execution
    async def force_stop_stream(self, chat_id):
        assistant = await group_assistant(self, chat_id)
        try:
            check = db.get(chat_id)
            if check: check.pop(0)
        except: pass
        await _clean_garbage(chat_id)
        if chat_id in self.active_calls:
            try: await assistant.leave_call(chat_id)
            except: pass
            finally: self.active_calls.discard(chat_id)

    @safe_execution
    async def skip_stream(self, chat_id, link, video=None, image=None):
        from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
        assistant = await group_assistant(self, chat_id)
        flags = MediaStream.Flags.REQUIRED if video else MediaStream.Flags.IGNORE
        vid_q = VideoQuality.HD_720p if video else None
        stream = MediaStream(link, AudioQuality.HIGH, vid_q, video_flags=flags)
        await assistant.play(chat_id, stream)

    @safe_execution
    async def seek_stream(self, chat_id, file_path, to_seek, duration, mode):
        from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
        assistant = await group_assistant(self, chat_id)
        params = f"-ss {to_seek} -to {duration}"
        flags = MediaStream.Flags.REQUIRED if mode == "video" else MediaStream.Flags.IGNORE
        vid_q = VideoQuality.HD_720p if mode == "video" else None
        stream = MediaStream(file_path, AudioQuality.HIGH, vid_q, video_flags=flags, ffmpeg_parameters=params)
        await assistant.play(chat_id, stream)

    @safe_execution
    async def speedup_stream(self, chat_id, file_path, speed, playing):
        from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
        if not playing: return
        assistant = await group_assistant(self, chat_id)
        base = os.path.basename(file_path)
        chatdir = os.path.join(os.getcwd(), "playback", str(speed))
        os.makedirs(chatdir, exist_ok=True)
        out = os.path.join(chatdir, base)
        if not os.path.exists(out):
            cmd = f'ffmpeg -i "{file_path}" -filter:v "setpts={str(2.0/float(speed))}*PTS" -filter:a atempo={speed} -y "{out}"'
            proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            await proc.communicate()
        dur = int(await asyncio.get_event_loop().run_in_executor(None, check_duration, out))
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        params = f"-ss {played} -to {seconds_to_min(dur)}"
        
        is_video = playing[0]["streamtype"] == "video"
        flags = MediaStream.Flags.REQUIRED if is_video else MediaStream.Flags.IGNORE
        vid_q = VideoQuality.HD_720p if is_video else None
        stream = MediaStream(out, AudioQuality.HIGH, vid_q, video_flags=flags, ffmpeg_parameters=params)
        
        if chat_id in db:
            await assistant.play(chat_id, stream)
            db[chat_id][0].update({"played": con_seconds, "dur": seconds_to_min(dur), "seconds": dur, "speed_path": out, "speed": speed})

    @safe_execution
    async def pause_stream(self, chat_id):
        await (await group_assistant(self, chat_id)).pause(chat_id)

    @safe_execution
    async def resume_stream(self, chat_id):
        await (await group_assistant(self, chat_id)).resume(chat_id)

    @safe_execution
    async def mute_stream(self, chat_id):
        await (await group_assistant(self, chat_id)).mute(chat_id)

    @safe_execution
    async def unmute_stream(self, chat_id):
        await (await group_assistant(self, chat_id)).unmute(chat_id)

    @safe_execution
    async def ping(self):
        pings = []
        clients = list(filter(None, [self.one, self.two, self.three, self.four, self.five]))
        for c in clients:
            if hasattr(c, 'ping'): pings.append(c.ping)
        return str(round(sum(pings)/len(pings), 3)) if pings else "0.0"

    @safe_execution
    async def decorators(self):
        from pytgcalls.types import StreamEnded, ChatUpdate
        clients = list(filter(None, [self.one, self.two, self.three, self.four, self.five]))
        
        async def handler(client, update):
            try:
                if isinstance(update, StreamEnded) and update.stream_type == StreamEnded.Type.AUDIO:
                    await self.play(client, update.chat_id)
                elif isinstance(update, ChatUpdate) and update.status in [ChatUpdate.Status.KICKED, ChatUpdate.Status.LEFT_GROUP]:
                    await self.stop_stream(update.chat_id)
            except: pass

        for c in clients:
            try: c.on_update()(handler)
            except: pass

Hotty = Call()
