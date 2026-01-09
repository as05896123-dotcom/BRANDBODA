"""
██████╗ ██████╗  █████╗ ███╗   ██╗██████╗ ██████╗ ██████╗ ██╗  ██╗
██╔══██╗██╔══██╗██╔══██╗████╗  ██║██╔══██╗██╔══██╗██╔══██╗╚██╗██╔╝
██████╔╝██████╔╝███████║██╔██╗ ██║██║  ██║██████╔╝██║  ██║ ╚███╔╝ 
██╔══██╗██╔══██╗██╔══██║██║╚██╗██║██║  ██║██╔══██╗██║  ██║ ██╔██╗ 
██████╔╝██║  ██║██║  ██║██║ ╚████║██████╔╝██║  ██║██████╔╝██╔╝ ██╗
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝

[ SYSTEM: ADVANCED CALL ENGINE - FULL FIXED VERSION ]
"""

import asyncio
import os
import sys
import traceback
from datetime import datetime, timedelta
from typing import Union, List
from functools import wraps

# =======================================================================
# 🩹 1. MONKEY PATCHING & COMPATIBILITY
# =======================================================================
def _apply_critical_patches():
    targets = ["pyrogram.raw.types", "pyrogram.types", "pytgcalls.types"]
    for module_name in targets:
        try:
            mod = __import__(module_name, fromlist=["UpdateGroupCall"])
            if hasattr(mod, "UpdateGroupCall"):
                cls = getattr(mod, "UpdateGroupCall")
                if not hasattr(cls, "chat_id"):
                    def _get_chat_id(self):
                        if hasattr(self, "chat") and getattr(self.chat, "id", None):
                            return self.chat.id
                        if hasattr(self, "_chat_id"): return self._chat_id
                        return 0
                    setattr(cls, "chat_id", property(_get_chat_id))
        except: pass
_apply_critical_patches()

# =======================================================================
# 🛡️ 2. IMPORT FIREWALL (الحل لمشكلة NotConnected)
# =======================================================================
class _DummyException(Exception): pass

# نحاول نستورد المكتبات الأساسية
try:
    from pytgcalls import PyTgCalls
    from pytgcalls.types import (
        AudioQuality, VideoQuality, ChatUpdate, MediaStream, StreamEnded, Update
    )
except ImportError:
    print("CRITICAL: PyTgCalls not found!")
    sys.exit(1)

# استيراد الأخطاء بشكل آمن عشان اختلاف النسخ
try: from pytgcalls.exceptions import NoActiveGroupCall
except ImportError: NoActiveGroupCall = _DummyException

try: from pytgcalls.exceptions import NoAudioSourceFound
except ImportError: NoAudioSourceFound = _DummyException

try: from pytgcalls.exceptions import NoVideoSourceFound
except ImportError: NoVideoSourceFound = _DummyException

try: from pytgcalls.exceptions import NotConnected
except ImportError: NotConnected = _DummyException  # ✅ ده الإصلاح المهم

try: from pytgcalls.exceptions import GroupCallNotFound
except ImportError: GroupCallNotFound = _DummyException

# باقي المكتبات
from pyrogram import Client
from pyrogram.errors import FloodWait, ChatAdminRequired, UserAlreadyParticipant
from pyrogram.types import InlineKeyboardMarkup

# =======================================================================
# ⚙️ 3. CONFIG & DATABASE
# =======================================================================
try:
    import config
    from BrandrdXMusic import LOGGER, YouTube, app
    from BrandrdXMusic.misc import db
    from BrandrdXMusic.utils.database import (
        add_active_chat, add_active_video_chat, get_loop, group_assistant,
        is_autoend, music_on, remove_active_chat, remove_active_video_chat,
        set_loop, get_lang
    )
    from BrandrdXMusic.utils.exceptions import AssistantErr
    from BrandrdXMusic.utils.formatters import check_duration, seconds_to_min, speed_converter
    from BrandrdXMusic.utils.inline.play import stream_markup
    from BrandrdXMusic.utils.stream.autoclear import auto_clean
    from BrandrdXMusic.utils.thumbnails import get_thumb
    from strings import get_string
    try: from BrandrdXMusic.utils.inline.play import stream_markup2
    except ImportError: stream_markup2 = None
except ImportError: sys.exit(1)

FFMPEG_BUFFER_SIZE = "4096k"
FFMPEG_MAX_RATE = "2048k"
FFMPEG_BASE_OPTIONS = "-preset ultrafast -tune zerolatency -f flv"
autoend = {}
counter = {}

# =======================================================================
# 🛠️ 4. HELPER FUNCTIONS
# =======================================================================
def capture_internal_err(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try: return await func(*args, **kwargs)
        except Exception as e:
            LOGGER(__name__).error(f"⚠️ [CallEngine] {func.__name__}: {e}")
            return None
    return wrapper

def create_media_stream(path: str, video: bool = False, image: str = None, ffmpeg_params: str = None) -> MediaStream:
    audio_q = AudioQuality.HIGH
    if video:
        video_q = VideoQuality.HD_720p
        video_flags = MediaStream.Flags.REQUIRED
    else:
        video_q = VideoQuality.SD_480p 
        video_flags = MediaStream.Flags.IGNORE
        
    base_cmd = f"{FFMPEG_BASE_OPTIONS} -maxrate {FFMPEG_MAX_RATE} -bufsize {FFMPEG_BUFFER_SIZE}"
    final_cmd = f"{base_cmd} {ffmpeg_params}" if ffmpeg_params else base_cmd
    
    return MediaStream(
        media_path=path,
        audio_parameters=audio_q,
        video_parameters=video_q,
        audio_flags=MediaStream.Flags.REQUIRED,
        video_flags=video_flags,
        ffmpeg_parameters=final_cmd
    )

async def _clear_(chat_id):
    try:
        popped = db.pop(chat_id, None)
        if popped: await auto_clean(popped)
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        await set_loop(chat_id, 0)
    except: pass

# =======================================================================
# 📞 5. MAIN CALL CLASS
# =======================================================================
class Call:
    def __init__(self):
        self.active_calls = set()
        self.clients_list = []
        self.pytgcalls_list = []
        self._load_clients()

    def _load_clients(self):
        sessions = [
            (config.STRING1, "BrandrdXMusic1"), (config.STRING2, "BrandrdXMusic2"),
            (config.STRING3, "BrandrdXMusic3"), (config.STRING4, "BrandrdXMusic4"),
            (config.STRING5, "BrandrdXMusic5"),
        ]
        for session_str, name in sessions:
            if session_str:
                try:
                    client = Client(name=name, api_id=config.API_ID, api_hash=config.API_HASH, session_string=session_str)
                    tg_call = PyTgCalls(client)
                    self.clients_list.append(client)
                    self.pytgcalls_list.append(tg_call)
                except: pass
        
        # Aliases
        self.one = self.pytgcalls_list[0] if len(self.pytgcalls_list) > 0 else None
        self.two = self.pytgcalls_list[1] if len(self.pytgcalls_list) > 1 else None
        self.three = self.pytgcalls_list[2] if len(self.pytgcalls_list) > 2 else None
        self.four = self.pytgcalls_list[3] if len(self.pytgcalls_list) > 3 else None
        self.five = self.pytgcalls_list[4] if len(self.pytgcalls_list) > 4 else None

    async def start(self):
        if not self.pytgcalls_list: return
        await asyncio.gather(*[cli.start() for cli in self.pytgcalls_list])

    async def get_call_engine(self, chat_id):
        try:
            assistant = await group_assistant(self, chat_id)
            if assistant:
                for i, client in enumerate(self.clients_list):
                    if client.me.id == assistant.me.id: return self.pytgcalls_list[i]
            return self.one
        except: return self.one

    async def join_call_robust(self, assistant, chat_id, stream):
        try:
            await assistant.play(chat_id, stream)
        except UserAlreadyParticipant: return
        except FloodWait as e: await asyncio.sleep(e.value + 1)
        except (NoActiveGroupCall, GroupCallNotFound): raise AssistantErr("No Active Group Call.")
        except ChatAdminRequired: raise AssistantErr("Assistant missing permissions.")
        except Exception: pass

    @capture_internal_err
    async def stop_stream(self, chat_id):
        assistant = await self.get_call_engine(chat_id)
        await _clear_(chat_id)
        try: await assistant.leave_call(chat_id)
        except: pass
        finally: self.active_calls.discard(chat_id)

    @capture_internal_err
    async def force_stop_stream(self, chat_id):
        assistant = await self.get_call_engine(chat_id)
        try:
            check = db.get(chat_id)
            if check: check.pop(0)
        except: pass
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        await _clear_(chat_id)
        try: await assistant.leave_call(chat_id)
        except: pass
        finally: self.active_calls.discard(chat_id)

    @capture_internal_err
    async def pause_stream(self, chat_id):
        try: await (await self.get_call_engine(chat_id)).pause(chat_id)
        except: pass

    @capture_internal_err
    async def resume_stream(self, chat_id):
        try: await (await self.get_call_engine(chat_id)).resume(chat_id)
        except: pass

    @capture_internal_err
    async def mute_stream(self, chat_id):
        try: await (await self.get_call_engine(chat_id)).mute(chat_id)
        except: pass

    @capture_internal_err
    async def unmute_stream(self, chat_id):
        try: await (await self.get_call_engine(chat_id)).unmute(chat_id)
        except: pass

    @capture_internal_err
    async def skip_stream(self, chat_id, link, video=None, image=None):
        assistant = await self.get_call_engine(chat_id)
        stream = create_media_stream(path=link, video=bool(video), image=image)
        await self.join_call_robust(assistant, chat_id, stream)

    @capture_internal_err
    async def seek_stream(self, chat_id, file_path, to_seek, duration, mode):
        assistant = await self.get_call_engine(chat_id)
        params = f"-ss {to_seek} -to {duration}"
        stream = create_media_stream(path=file_path, video=(mode == "video"), ffmpeg_params=params)
        await assistant.play(chat_id, stream)

    @capture_internal_err
    async def speedup_stream(self, chat_id, file_path, speed, playing):
        if not playing or not isinstance(playing, list): return
        assistant = await self.get_call_engine(chat_id)
        base = os.path.basename(file_path)
        playback_dir = os.path.join(os.getcwd(), "playback", str(speed))
        os.makedirs(playback_dir, exist_ok=True)
        out = os.path.join(playback_dir, base)
        if not os.path.exists(out):
            cmd = f'ffmpeg -i "{file_path}" -filter:v "setpts={str(2.0/float(speed))}*PTS" -filter:a "atempo={speed}" -y "{out}"'
            proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            await proc.communicate()
        dur = int(await asyncio.get_event_loop().run_in_executor(None, check_duration, out))
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        params = f"-ss {played} -to {seconds_to_min(dur)}"
        stream = create_media_stream(path=out, video=(playing[0]["streamtype"]=="video"), ffmpeg_params=params)
        if chat_id in db and db[chat_id] and db[chat_id][0].get("file") == file_path:
            await assistant.play(chat_id, stream)
            db[chat_id][0].update({"played": con_seconds, "dur": seconds_to_min(dur), "seconds": dur, "speed_path": out, "speed": speed})

    @capture_internal_err
    async def join_call(self, chat_id, original_chat_id, link, video=None, image=None):
        assistant = await self.get_call_engine(chat_id)
        stream = create_media_stream(path=link, video=bool(video), image=image)
        await self.join_call_robust(assistant, chat_id, stream)
        self.active_calls.add(chat_id)
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video: await add_active_video_chat(chat_id)
        if await is_autoend():
            try:
                if len(await assistant.get_participants(chat_id)) <= 1:
                    autoend[chat_id] = datetime.now() + timedelta(minutes=1)
            except: pass

    @capture_internal_err
    async def play(self, client, chat_id):
        if isinstance(client, Client): client = await self.get_call_engine(chat_id)
        check = db.get(chat_id)
        if not check:
            await _clear_(chat_id)
            return await self.stop_stream(chat_id)
        popped = None
        loop = await get_loop(chat_id)
        try:
            if loop == 0: popped = check.pop(0)
            else:
                loop -= 1
                await set_loop(chat_id, loop)
            if popped: await auto_clean(popped)
            if not check:
                await _clear_(chat_id)
                return await self.stop_stream(chat_id)
        except:
            await _clear_(chat_id)
            return await self.stop_stream(chat_id)

        queued = check[0]["file"]
        lang = await get_lang(chat_id)
        _ = get_string(lang)
        title, user = (check[0]["title"]).title(), check[0]["by"]
        orig_chat, stype, vidid = check[0]["chat_id"], check[0]["streamtype"], check[0]["vidid"]
        db[chat_id][0]["played"] = 0
        video = (str(stype) == "video")
        if check[0].get("old_dur"):
            db[chat_id][0]["dur"] = check[0]["old_dur"]
            db[chat_id][0]["seconds"] = check[0]["old_second"]
            db[chat_id][0]["speed_path"], db[chat_id][0]["speed"] = None, 1.0

        try:
            try: img = await get_thumb(vidid)
            except: img = config.STREAM_IMG_URL
            stream = None
            if "live_" in queued:
                n, link = await YouTube.video(vidid, True)
                if n == 0: return await app.send_message(orig_chat, text=_["call_6"])
                stream = create_media_stream(path=link, video=video, image=img)
                await self.join_call_robust(client, chat_id, stream)
                await self._send_play_message(orig_chat, vidid, title, check[0]["dur"], user, video, _, chat_id, img, "live")
            elif "vid_" in queued:
                mystic = await app.send_message(orig_chat, _["call_7"])
                try: path, _ = await YouTube.download(vidid, mystic, videoid=True, video=video)
                except: return await mystic.edit_text(_["call_6"])
                stream = create_media_stream(path=path, video=video, image=img)
                await self.join_call_robust(client, chat_id, stream)
                await mystic.delete()
                await self._send_play_message(orig_chat, vidid, title, check[0]["dur"], user, video, _, chat_id, img, "vid")
            elif "index_" in queued:
                stream = create_media_stream(path=vidid, video=video, image=img)
                await self.join_call_robust(client, chat_id, stream)
                await self._send_play_message(orig_chat, vidid, title, check[0]["dur"], user, video, _, chat_id, img, "index")
            else:
                stream = create_media_stream(path=queued, video=video, image=img)
                await self.join_call_robust(client, chat_id, stream)
                await self._send_play_message(orig_chat, vidid, title, check[0]["dur"], user, video, _, chat_id, img, stype)
        except Exception as e:
            LOGGER(__name__).error(f"❌ Play Error: {e}")
            await _clear_(chat_id)

    async def _send_play_message(self, chat_id, vidid, title, dur, user, is_vid, lang, db_id, img, stype):
        try:
            btns = stream_markup2(lang, db_id) if stream_markup2 else stream_markup(lang, vidid, db_id)
            photo, link, mtype = img, f"https://t.me/{app.username}?start=info_{vidid}", "stream"
            if vidid == "telegram":
                photo = config.TELEGRAM_VIDEO_URL if is_vid else config.TELEGRAM_AUDIO_URL
                link = config.SUPPORT_CHAT
            elif vidid == "soundcloud":
                photo = config.SOUNCLOUD_IMG_URL
                link = config.SUPPORT_CHAT
            elif stype == "index":
                photo = config.STREAM_IMG_URL
                mtype = "tg"
            cap = lang["stream_1"].format(link, title[:23], dur, user)
            if stype == "index": cap = lang["stream_2"].format(user)
            run = await app.send_photo(chat_id, photo, caption=cap, reply_markup=InlineKeyboardMarkup(btns))
            if db_id in db: db[db_id][0]["mystic"], db[db_id][0]["markup"] = run, mtype
        except: pass

    @capture_internal_err
    async def ping(self):
        pings = []
        for c in self.pytgcalls_list:
            try:
                if hasattr(c, "ping"): pings.append(c.ping)
            except: pass
        return str(round(sum(pings)/len(pings), 3)) if pings else "0.0"

    @capture_internal_err
    async def decorators(self):
        async def handler(c, u):
            try:
                if isinstance(u, StreamEnded) and u.stream_type == StreamEnded.Type.AUDIO:
                    await self.play(c, u.chat_id)
                elif isinstance(u, ChatUpdate) and u.status in [ChatUpdate.Status.KICKED, ChatUpdate.Status.LEFT_GROUP]:
                    await self.stop_stream(u.chat_id)
            except: pass
        for a in self.pytgcalls_list:
            try: a.on_update()(handler)
            except: pass

Hotty = Call()
