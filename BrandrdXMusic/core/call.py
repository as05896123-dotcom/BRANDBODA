"""
██████╗ ██████╗  █████╗ ███╗   ██╗██████╗ ██████╗ ██████╗ ██╗  ██╗
██╔══██╗██╔══██╗██╔══██╗████╗  ██║██╔══██╗██╔══██╗██╔══██╗╚██╗██╔╝
██████╔╝██████╔╝███████║██╔██╗ ██║██║  ██║██████╔╝██║  ██║ ╚███╔╝ 
██╔══██╗██╔══██╗██╔══██║██║╚██╗██║██║  ██║██╔══██╗██║  ██║ ██╔██╗ 
██████╔╝██║  ██║██║  ██║██║ ╚████║██████╔╝██║  ██║██████╔╝██╔╝ ██╗
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝

[ SYSTEM: ADVANCED CALL ENGINE - FINAL FULL VERSION ]
[ VERSION: 5.0.0 STABLE ]
[ DEVELOPER: GEMINI AI & YOU ]
"""

import asyncio
import os
import sys
import traceback
from datetime import datetime, timedelta
from typing import Union, List
from functools import wraps

# =======================================================================
# 🩹 1. MONKEY PATCHING SECTION (CRITICAL FIXES)
# =======================================================================
def _apply_critical_patches():
    """
    تطبيق إصلاحات إجبارية للمكتبات لضمان التوافقية.
    يتم استدعاء هذه الدالة قبل أي عملية استيراد أخرى.
    """
    targets = [
        "pyrogram.raw.types", 
        "pyrogram.types", 
        "pytgcalls.types"
    ]
    
    for module_name in targets:
        try:
            mod = __import__(module_name, fromlist=["UpdateGroupCall"])
            if hasattr(mod, "UpdateGroupCall"):
                cls = getattr(mod, "UpdateGroupCall")
                if not hasattr(cls, "chat_id"):
                    def _get_chat_id(self):
                        if hasattr(self, "chat") and getattr(self.chat, "id", None):
                            return self.chat.id
                        if hasattr(self, "_chat_id"):
                            return self._chat_id
                        return 0
                    setattr(cls, "chat_id", property(_get_chat_id))
        except Exception:
            pass

_apply_critical_patches()

# =======================================================================
# 📚 2. LIBRARY IMPORTS
# =======================================================================
from pyrogram import Client
from pyrogram.errors import (
    FloodWait,
    ChatAdminRequired,
    UserAlreadyParticipant,
    UserNotParticipant
)
from pyrogram.types import InlineKeyboardMarkup

from pytgcalls import PyTgCalls
from pytgcalls.types import (
    AudioQuality,
    VideoQuality,
    ChatUpdate,
    MediaStream,
    StreamEnded,
    Update
)
from pytgcalls.exceptions import (
    NoActiveGroupCall,
    NoAudioSourceFound,
    NoVideoSourceFound,
    NotConnected,
    GroupCallNotFound
)

# استيراد إعدادات المشروع
try:
    import config
    from BrandrdXMusic import LOGGER, YouTube, app
    from BrandrdXMusic.misc import db
    from BrandrdXMusic.utils.database import (
        add_active_chat,
        add_active_video_chat,
        get_loop,
        group_assistant,
        is_autoend,
        music_on,
        remove_active_chat,
        remove_active_video_chat,
        set_loop,
        get_lang
    )
    from BrandrdXMusic.utils.exceptions import AssistantErr
    from BrandrdXMusic.utils.formatters import check_duration, seconds_to_min, speed_converter
    from BrandrdXMusic.utils.inline.play import stream_markup
    from BrandrdXMusic.utils.stream.autoclear import auto_clean
    from BrandrdXMusic.utils.thumbnails import get_thumb
    from strings import get_string
    
    try:
        from BrandrdXMusic.utils.inline.play import stream_markup2
    except ImportError:
        stream_markup2 = None
        
except ImportError as e:
    print(f"CRITICAL IMPORT ERROR: {e}")
    sys.exit(1)


# =======================================================================
# ⚙️ 3. CONFIGURATION & CONSTANTS
# =======================================================================

FFMPEG_BUFFER_SIZE = "4096k"
FFMPEG_MAX_RATE = "2048k"
FFMPEG_BASE_OPTIONS = "-preset ultrafast -tune zerolatency -f flv"

autoend = {}
counter = {}

# =======================================================================
# 🛡️ 4. ERROR HANDLING DECORATORS
# =======================================================================

def capture_internal_err(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            LOGGER(__name__).error(f"⚠️ [CallEngine Error] in {func.__name__}: {e}")
            return None
    return wrapper

# =======================================================================
# 🎬 5. MEDIA STREAM FACTORY
# =======================================================================

def create_media_stream(path: str, video: bool = False, image: str = None, ffmpeg_params: str = None) -> MediaStream:
    audio_q = AudioQuality.HIGH
    
    # إصلاح هام: نمرر جودة الفيديو دائماً حتى لو صوت فقط لتجنب NoneType Error
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

# =======================================================================
# 📞 6. THE CALL MANAGER CLASS (CORE ENGINE)
# =======================================================================

class Call:
    def __init__(self):
        self.active_calls: set[int] = set()
        self.clients_list = []
        self.pytgcalls_list = []
        self._load_clients()

    def _load_clients(self):
        sessions = [
            (config.STRING1, "BrandrdXMusic1"),
            (config.STRING2, "BrandrdXMusic2"),
            (config.STRING3, "BrandrdXMusic3"),
            (config.STRING4, "BrandrdXMusic4"),
            (config.STRING5, "BrandrdXMusic5"),
        ]
        
        for session_str, name in sessions:
            if session_str:
                try:
                    client = Client(name=name, api_id=config.API_ID, api_hash=config.API_HASH, session_string=session_str)
                    tg_call = PyTgCalls(client)
                    self.clients_list.append(client)
                    self.pytgcalls_list.append(tg_call)
                except Exception as e:
                    LOGGER(__name__).error(f"Failed to initialize assistant {name}: {e}")

        # Aliases for compatibility
        self.one = self.pytgcalls_list[0] if len(self.pytgcalls_list) > 0 else None
        self.two = self.pytgcalls_list[1] if len(self.pytgcalls_list) > 1 else None
        self.three = self.pytgcalls_list[2] if len(self.pytgcalls_list) > 2 else None
        self.four = self.pytgcalls_list[3] if len(self.pytgcalls_list) > 3 else None
        self.five = self.pytgcalls_list[4] if len(self.pytgcalls_list) > 4 else None

        self.userbot1 = self.clients_list[0] if len(self.clients_list) > 0 else None
        self.userbot2 = self.clients_list[1] if len(self.clients_list) > 1 else None
        self.userbot3 = self.clients_list[2] if len(self.clients_list) > 2 else None
        self.userbot4 = self.clients_list[3] if len(self.clients_list) > 3 else None
        self.userbot5 = self.clients_list[4] if len(self.clients_list) > 4 else None

    async def start(self) -> None:
        LOGGER(__name__).info("🚀 Starting Assistant Clients...")
        if not self.pytgcalls_list:
            LOGGER(__name__).error("❌ No Assistant Clients Found!")
            return
        await asyncio.gather(*[cli.start() for cli in self.pytgcalls_list])
        LOGGER(__name__).info(f"✅ Started {len(self.pytgcalls_list)} assistants.")

    async def get_call_engine(self, chat_id: int) -> PyTgCalls:
        try:
            assistant = await group_assistant(self, chat_id)
            if assistant:
                for i, client in enumerate(self.clients_list):
                    if client.me.id == assistant.me.id:
                        return self.pytgcalls_list[i]
            return self.one
        except: return self.one

    async def join_call_robust(self, assistant: PyTgCalls, chat_id: int, stream: MediaStream) -> None:
        max_retries = 3
        retry_delay = 2
        for attempt in range(1, max_retries + 1):
            try:
                await assistant.play(chat_id, stream)
                LOGGER(__name__).info(f"✅ Joined call in {chat_id}")
                return
            except UserAlreadyParticipant:
                return
            except FloodWait as e:
                if e.value > 45: raise AssistantErr(f"FloodWait: {e.value}s")
                await asyncio.sleep(e.value + 1)
            except (NoActiveGroupCall, GroupCallNotFound):
                raise AssistantErr("No Active Group Call.")
            except ChatAdminRequired:
                raise AssistantErr("Assistant missing permissions.")
            except Exception as e:
                LOGGER(__name__).warning(f"⚠️ Join Attempt {attempt} failed: {e}")
                if attempt == max_retries: raise AssistantErr(f"Failed to join after {max_retries} attempts.")
                await asyncio.sleep(retry_delay)
                retry_delay += 2

    # ===================================================================
    # 🎮 CONTROLS
    # ===================================================================

    @capture_internal_err
    async def stop_stream(self, chat_id: int) -> None:
        assistant = await self.get_call_engine(chat_id)
        await _clear_(chat_id)
        try: await assistant.leave_call(chat_id)
        except: pass
        finally: self.active_calls.discard(chat_id)

    @capture_internal_err
    async def force_stop_stream(self, chat_id: int) -> None:
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
    async def pause_stream(self, chat_id: int) -> None:
        assistant = await self.get_call_engine(chat_id)
        await assistant.pause(chat_id)

    @capture_internal_err
    async def resume_stream(self, chat_id: int) -> None:
        assistant = await self.get_call_engine(chat_id)
        await assistant.resume(chat_id)

    @capture_internal_err
    async def mute_stream(self, chat_id: int) -> None:
        assistant = await self.get_call_engine(chat_id)
        await assistant.mute(chat_id)

    @capture_internal_err
    async def unmute_stream(self, chat_id: int) -> None:
        assistant = await self.get_call_engine(chat_id)
        await assistant.unmute(chat_id)

    @capture_internal_err
    async def skip_stream(self, chat_id: int, link: str, video: Union[bool, str] = None, image: Union[bool, str] = None) -> None:
        assistant = await self.get_call_engine(chat_id)
        stream = create_media_stream(path=link, video=bool(video), image=image)
        await self.join_call_robust(assistant, chat_id, stream)

    @capture_internal_err
    async def seek_stream(self, chat_id: int, file_path: str, to_seek: str, duration: str, mode: str) -> None:
        assistant = await self.get_call_engine(chat_id)
        params = f"-ss {to_seek} -to {duration}"
        stream = create_media_stream(path=file_path, video=(mode == "video"), ffmpeg_params=params)
        await assistant.play(chat_id, stream)

    @capture_internal_err
    async def speedup_stream(self, chat_id: int, file_path: str, speed: float, playing: list) -> None:
        if not playing or not isinstance(playing, list): return
        assistant = await self.get_call_engine(chat_id)
        base = os.path.basename(file_path)
        playback_dir = os.path.join(os.getcwd(), "playback", str(speed))
        os.makedirs(playback_dir, exist_ok=True)
        out_file = os.path.join(playback_dir, base)

        if not os.path.exists(out_file):
            video_speed = str(2.0 / float(speed))
            cmd = f'ffmpeg -i "{file_path}" -filter:v "setpts={video_speed}*PTS" -filter:a "atempo={speed}" -y "{out_file}"'
            process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            await process.communicate()

        dur = int(await asyncio.get_event_loop().run_in_executor(None, check_duration, out_file))
        played_time, con_seconds = speed_converter(playing[0]["played"], speed)
        duration_min = seconds_to_min(dur)
        
        params = f"-ss {played_time} -to {duration_min}"
        stream = create_media_stream(path=out_file, video=(playing[0]["streamtype"] == "video"), ffmpeg_params=params)

        if chat_id in db and db[chat_id] and db[chat_id][0].get("file") == file_path:
            await assistant.play(chat_id, stream)
            db[chat_id][0].update({
                "played": con_seconds, "dur": duration_min, "seconds": dur,
                "speed_path": out_file, "speed": speed,
                "old_dur": db[chat_id][0].get("dur"), "old_second": db[chat_id][0].get("seconds"),
            })

    # ===================================================================
    # ▶️ MAIN PLAY LOGIC
    # ===================================================================

    @capture_internal_err
    async def join_call(self, chat_id: int, original_chat_id: int, link: str, video: Union[bool, str] = None, image: Union[bool, str] = None) -> None:
        assistant = await self.get_call_engine(chat_id)
        stream = create_media_stream(path=link, video=bool(video), image=image)
        await self.join_call_robust(assistant, chat_id, stream)
        
        self.active_calls.add(chat_id)
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video: await add_active_video_chat(chat_id)
        
        if await is_autoend():
            counter[chat_id] = {}
            try:
                participants = await assistant.get_participants(chat_id)
                if len(participants) <= 1:
                    autoend[chat_id] = datetime.now() + timedelta(minutes=1)
            except: pass

    @capture_internal_err
    async def play(self, client, chat_id: int) -> None:
        if isinstance(client, Client):
            client = await self.get_call_engine(chat_id)
            
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
        language = await get_lang(chat_id)
        _ = get_string(language)
        title = (check[0]["title"]).title()
        user = check[0]["by"]
        original_chat_id = check[0]["chat_id"]
        streamtype = check[0]["streamtype"]
        videoid = check[0]["vidid"]
        db[chat_id][0]["played"] = 0
        video = (str(streamtype) == "video")

        if check[0].get("old_dur"):
            db[chat_id][0]["dur"] = check[0]["old_dur"]
            db[chat_id][0]["seconds"] = check[0]["old_second"]
            db[chat_id][0]["speed_path"] = None
            db[chat_id][0]["speed"] = 1.0

        try:
            stream = None
            try: img = await get_thumb(videoid)
            except: img = config.STREAM_IMG_URL

            # 1. LIVE
            if "live_" in queued:
                n, link = await YouTube.video(videoid, True)
                if n == 0: return await app.send_message(original_chat_id, text=_["call_6"])
                stream = create_media_stream(path=link, video=video, image=img)
                await self.join_call_robust(client, chat_id, stream)
                await self._send_play_message(original_chat_id, videoid, title, check[0]["dur"], user, video, _, chat_id, img, "live")

            # 2. VIDEO/FILE
            elif "vid_" in queued:
                mystic = await app.send_message(original_chat_id, _["call_7"])
                try:
                    file_path, _ = await YouTube.download(videoid, mystic, videoid=True, video=video)
                except: return await mystic.edit_text(_["call_6"])
                stream = create_media_stream(path=file_path, video=video, image=img)
                await self.join_call_robust(client, chat_id, stream)
                await mystic.delete()
                await self._send_play_message(original_chat_id, videoid, title, check[0]["dur"], user, video, _, chat_id, img, "vid")

            # 3. INDEX
            elif "index_" in queued:
                stream = create_media_stream(path=videoid, video=video, image=img)
                await self.join_call_robust(client, chat_id, stream)
                await self._send_play_message(original_chat_id, videoid, title, check[0]["dur"], user, video, _, chat_id, img, "index")

            # 4. STANDARD
            else:
                stream = create_media_stream(path=queued, video=video, image=img)
                await self.join_call_robust(client, chat_id, stream)
                await self._send_play_message(original_chat_id, videoid, title, check[0]["dur"], user, video, _, chat_id, img, streamtype)

        except Exception as e:
            LOGGER(__name__).error(f"❌ Play Error: {e}")
            await _clear_(chat_id)

    async def _send_play_message(self, chat_id, videoid, title, duration, user, is_video, lang, db_chat_id, img, stype):
        try:
            if stream_markup2: buttons = stream_markup2(lang, db_chat_id)
            else: buttons = stream_markup(lang, videoid, db_chat_id)
            
            photo = img
            link = f"https://t.me/{app.username}?start=info_{videoid}"
            m_type = "stream"

            if videoid == "telegram":
                photo = config.TELEGRAM_VIDEO_URL if is_video else config.TELEGRAM_AUDIO_URL
                link = config.SUPPORT_CHAT
            elif videoid == "soundcloud":
                photo = config.SOUNCLOUD_IMG_URL
                link = config.SUPPORT_CHAT
            elif stype == "index":
                photo = config.STREAM_IMG_URL
                m_type = "tg"

            caption = lang["stream_1"].format(link, title[:23], duration, user)
            if stype == "index": caption = lang["stream_2"].format(user)

            run = await app.send_photo(chat_id=chat_id, photo=photo, caption=caption, reply_markup=InlineKeyboardMarkup(buttons))
            if db_chat_id in db:
                db[db_chat_id][0]["mystic"] = run
                db[db_chat_id][0]["markup"] = m_type
        except: pass

    @capture_internal_err
    async def ping(self) -> str:
        pings = []
        for cli in self.pytgcalls_list:
            try:
                if hasattr(cli, "ping"): pings.append(cli.ping)
            except: pass
        return str(round(sum(pings) / len(pings), 3)) if pings else "0.0"

    @capture_internal_err
    async def decorators(self) -> None:
        async def unified_update_handler(client, update: Update) -> None:
            try:
                if isinstance(update, StreamEnded):
                    if update.stream_type == StreamEnded.Type.AUDIO:
                        await self.play(client, update.chat_id)
                elif isinstance(update, ChatUpdate):
                    if update.status in [ChatUpdate.Status.KICKED, ChatUpdate.Status.LEFT_GROUP, ChatUpdate.Status.CLOSED_VOICE_CHAT]:
                        await self.stop_stream(update.chat_id)
            except Exception as e:
                LOGGER(__name__).error(f"Update Handler: {e}")

        for assistant in self.pytgcalls_list:
            try: assistant.on_update()(unified_update_handler)
            except: pass

Hotty = Call()
