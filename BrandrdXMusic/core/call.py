import asyncio
import os
import traceback
from datetime import datetime, timedelta
from typing import Union
from functools import wraps

from pyrogram import Client
from pyrogram.errors import (
    FloodWait, 
    ChatAdminRequired, 
    UserAlreadyParticipant, 
    RPCError
)
from pyrogram.types import InlineKeyboardMarkup

from pytgcalls import PyTgCalls
from pytgcalls.types import (
    AudioQuality, 
    ChatUpdate, 
    MediaStream, 
    StreamEnded, 
    Update, 
    VideoQuality
)

# ❌ تم إزالة الاستيراد المسبب للمشاكل (pytgcalls.mtproto.data)
# ✅ تم استبداله بفحص ذكي داخل الكود (Smart Check)

# =======================================================================
# 🩹 PATCH: إصلاح دائم لمشكلة chat_id (Critical Fix)
# =======================================================================
try:
    from pytgcalls.types import UpdateGroupCall
    if not hasattr(UpdateGroupCall, 'chat_id'):
        UpdateGroupCall.chat_id = property(lambda self: getattr(getattr(self, "chat", None), "id", 0))
except ImportError:
    pass

# =======================================================================
# 🧱 جدار الحماية (Exception Firewall)
# =======================================================================
class _DummyException(Exception): pass
try: from pytgcalls.exceptions import NoActiveGroupCall
except ImportError: NoActiveGroupCall = _DummyException
try: from pytgcalls.exceptions import NoAudioSourceFound
except ImportError: NoAudioSourceFound = _DummyException
try: from pytgcalls.exceptions import NotConnected
except ImportError: NotConnected = _DummyException
try: from ntgcalls import TelegramServerError, ConnectionNotFound
except ImportError: TelegramServerError, ConnectionNotFound = _DummyException, _DummyException

# =======================================================================
# ⚙️ الإعدادات
# =======================================================================
import config
from strings import get_string
from BrandrdXMusic import LOGGER, YouTube, app
from BrandrdXMusic.misc import db
from BrandrdXMusic.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_lang,
    get_loop,
    group_assistant,
    is_autoend,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
)
from BrandrdXMusic.utils.exceptions import AssistantErr
from BrandrdXMusic.utils.formatters import check_duration, seconds_to_min, speed_converter
from BrandrdXMusic.utils.inline.play import stream_markup
from BrandrdXMusic.utils.stream.autoclear import auto_clean
from BrandrdXMusic.utils.thumbnails import get_thumb

# محاولة استيراد stream_markup2 لو موجودة، لو لا نستخدم stream_markup
try:
    from BrandrdXMusic.utils.inline.play import stream_markup2
except ImportError:
    stream_markup2 = None

autoend = {}
counter = {}

# =======================================================================
# 🛡️ مزخرف الأخطاء (Logger)
# =======================================================================
def capture_internal_err(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # تسجيل الخطأ بالتفصيل عشان نعرف سببه
            err_trace = traceback.format_exc()
            LOGGER(__name__).error(f"⚠️ Error in {func.__name__}: {e}")
            LOGGER(__name__).debug(f"🔍 Traceback: {err_trace}")
            return None
    return wrapper

# =======================================================================
# 🚀 إعدادات البث (Monster Config)
# =======================================================================
def dynamic_media_stream(path: str, video: bool = False, image: str = None, ffmpeg_params: str = None) -> MediaStream:
    audio_q = AudioQuality.HIGH
    video_q = VideoQuality.HD_720p if video else VideoQuality.SD_480p
    
    # إعدادات الـ Buffer والسرعة (علاج التقطيع)
    base_params = "-preset ultrafast -tune zerolatency -maxrate 3000k -bufsize 6000k"
    final_params = f"{base_params} {ffmpeg_params}" if ffmpeg_params else base_params

    return MediaStream(
        media_path=path,
        audio_parameters=audio_q,
        video_parameters=video_q if video else None,
        audio_flags=MediaStream.Flags.REQUIRED,
        video_flags=MediaStream.Flags.REQUIRED if video else MediaStream.Flags.IGNORE,
        ffmpeg_parameters=final_params,
    )

async def _clear_(chat_id: int) -> None:
    try:
        popped = db.pop(chat_id, None)
        if popped: await auto_clean(popped)
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        await set_loop(chat_id, 0)
    except: pass

# =======================================================================
# 📞 الكلاس الرئيسي (Fused Engine)
# =======================================================================
class Call:
    def __init__(self):
        self.userbot1 = Client("BrandrdXMusic1", config.API_ID, config.API_HASH, session_string=config.STRING1) if config.STRING1 else None
        self.one = PyTgCalls(self.userbot1) if self.userbot1 else None

        self.userbot2 = Client("BrandrdXMusic2", config.API_ID, config.API_HASH, session_string=config.STRING2) if config.STRING2 else None
        self.two = PyTgCalls(self.userbot2) if self.userbot2 else None

        self.userbot3 = Client("BrandrdXMusic3", config.API_ID, config.API_HASH, session_string=config.STRING3) if config.STRING3 else None
        self.three = PyTgCalls(self.userbot3) if self.userbot3 else None

        self.userbot4 = Client("BrandrdXMusic4", config.API_ID, config.API_HASH, session_string=config.STRING4) if config.STRING4 else None
        self.four = PyTgCalls(self.userbot4) if self.userbot4 else None

        self.userbot5 = Client("BrandrdXMusic5", config.API_ID, config.API_HASH, session_string=config.STRING5) if config.STRING5 else None
        self.five = PyTgCalls(self.userbot5) if self.userbot5 else None

        self.active_calls: set[int] = set()

    async def get_call_engine(self, chat_id: int) -> PyTgCalls:
        try:
            bot = await group_assistant(self, chat_id)
            if self.userbot1 and bot.me.id == self.userbot1.me.id: return self.one
            if self.userbot2 and bot.me.id == self.userbot2.me.id: return self.two
            if self.userbot3 and bot.me.id == self.userbot3.me.id: return self.three
            if self.userbot4 and bot.me.id == self.userbot4.me.id: return self.four
            if self.userbot5 and bot.me.id == self.userbot5.me.id: return self.five
            return self.one
        except: return self.one

    async def start(self) -> None:
        LOGGER(__name__).info("🚀 Starting All Assistant Clients...")
        clients = [c for c in [self.one, self.two, self.three, self.four, self.five] if c]
        if clients:
            await asyncio.gather(*[cli.start() for cli in clients])
        LOGGER(__name__).info(f"✅ Started {len(clients)} Assistant Clients.")

    # ===================================================================
    # 🥊 دالة الانضمام المدرعة (Robust Join)
    # ===================================================================
    async def join_call_robust(self, assistant: PyTgCalls, chat_id: int, stream: MediaStream) -> None:
        attempts = 4
        retry_delay = 1
        while attempts > 0:
            try:
                LOGGER(__name__).info(f"🔄 Connecting to {chat_id}...")
                await assistant.play(chat_id, stream)
                LOGGER(__name__).info(f"✅ Connected to {chat_id}")
                return 
            except UserAlreadyParticipant:
                LOGGER(__name__).info(f"ℹ️ Already in {chat_id}, playing...")
                return 
            except FloodWait as e:
                wait_time = e.value + 1
                if wait_time < 30:
                    LOGGER(__name__).warning(f"⏳ FloodWait {wait_time}s. Sleeping...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise AssistantErr(f"Heavy FloodWait: {wait_time}s")
            except (NoActiveGroupCall, ChatAdminRequired):
                raise AssistantErr("Voice chat not started or missing permissions.")
            except (NoAudioSourceFound, NoVideoSourceFound, ConnectionNotFound):
                LOGGER(__name__).warning("⚠️ Connection issue, retrying...")
            except Exception as e:
                LOGGER(__name__).warning(f"⚠️ Join Error {chat_id}: {e}")
            
            attempts -= 1
            await asyncio.sleep(retry_delay)
            retry_delay += 1
            
        raise AssistantErr("Failed to connect after retries.")

    # ===================================================================
    # 🎮 التحكم (Actions)
    # ===================================================================
    @capture_internal_err
    async def stop_stream(self, chat_id: int) -> None:
        assistant = await self.get_call_engine(chat_id)
        await _clear_(chat_id)
        try:
            await assistant.leave_call(chat_id)
        except (NotConnected, NoActiveGroupCall):
            pass
        except Exception:
            pass
        finally:
            self.active_calls.discard(chat_id)

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
        try:
            await assistant.leave_call(chat_id)
        except: pass
        finally:
            self.active_calls.discard(chat_id)

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
        stream = dynamic_media_stream(path=link, video=bool(video), image=image)
        await self.join_call_robust(assistant, chat_id, stream)

    @capture_internal_err
    async def seek_stream(self, chat_id: int, file_path: str, to_seek: str, duration: str, mode: str) -> None:
        assistant = await self.get_call_engine(chat_id)
        ffmpeg_params = f"-ss {to_seek} -to {duration}"
        stream = dynamic_media_stream(path=file_path, video=(mode == "video"), ffmpeg_params=ffmpeg_params)
        await assistant.play(chat_id, stream)

    @capture_internal_err
    async def speedup_stream(self, chat_id: int, file_path: str, speed: float, playing: list) -> None:
        if not isinstance(playing, list) or not playing: return
        assistant = await self.get_call_engine(chat_id)
        base = os.path.basename(file_path)
        chatdir = os.path.join(os.getcwd(), "playback", str(speed))
        os.makedirs(chatdir, exist_ok=True)
        out = os.path.join(chatdir, base)

        if not os.path.exists(out):
            vs = str(2.0 / float(speed))
            cmd = f'ffmpeg -i "{file_path}" -filter:v "setpts={vs}*PTS" -filter:a atempo={speed} -y "{out}"'
            proc = await asyncio.create_subprocess_shell(cmd, stdin=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            await proc.communicate()

        dur = int(await asyncio.get_event_loop().run_in_executor(None, check_duration, out))
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration_min = seconds_to_min(dur)
        ffmpeg_params = f"-ss {played} -to {duration_min}"
        stream = dynamic_media_stream(path=out, video=(playing[0]["streamtype"] == "video"), ffmpeg_params=ffmpeg_params)

        if chat_id in db and db[chat_id] and db[chat_id][0].get("file") == file_path:
            await assistant.play(chat_id, stream)
            db[chat_id][0].update({
                "played": con_seconds, "dur": duration_min, "seconds": dur,
                "speed_path": out, "speed": speed,
                "old_dur": db[chat_id][0].get("dur"),
                "old_second": db[chat_id][0].get("seconds"),
            })

    @capture_internal_err
    async def join_call(self, chat_id: int, original_chat_id: int, link: str, video: Union[bool, str] = None, image: Union[bool, str] = None) -> None:
        assistant = await self.get_call_engine(chat_id)
        stream = dynamic_media_stream(path=link, video=bool(video), image=image)
        
        await self.join_call_robust(assistant, chat_id, stream)
        
        self.active_calls.add(chat_id)
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video: await add_active_video_chat(chat_id)
        
        if await is_autoend():
            counter[chat_id] = {}
            try:
                users = len(await assistant.get_participants(chat_id))
                if users == 1: autoend[chat_id] = datetime.now() + timedelta(minutes=1)
            except: pass

    # ===================================================================
    # 🎵 Play (Logic Merged)
    # ===================================================================
    @capture_internal_err
    async def play(self, client, chat_id: int) -> None:
        if isinstance(client, Client): client = await self.get_call_engine(chat_id)
        
        check = db.get(chat_id)
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
        except Exception:
            await _clear_(chat_id)
            return await self.stop_stream(chat_id)

        # تجهيز البيانات
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

        exis = (check[0]).get("old_dur")
        if exis:
            db[chat_id][0]["dur"] = exis
            db[chat_id][0]["seconds"] = check[0]["old_second"]
            db[chat_id][0]["speed_path"] = None
            db[chat_id][0]["speed"] = 1.0

        try:
            stream = None
            img = await get_thumb(videoid)

            # 1. Live Stream
            if "live_" in queued:
                n, link = await YouTube.video(videoid, True)
                if n == 0: return await app.send_message(original_chat_id, text=_["call_6"])
                
                stream = dynamic_media_stream(path=link, video=video, image=img)
                await self.join_call_robust(client, chat_id, stream)

                button = stream_markup2(_, chat_id) if stream_markup2 else stream_markup(_, videoid, chat_id)
                run = await app.send_photo(
                    chat_id=original_chat_id, photo=img,
                    caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{videoid}", title[:23], check[0]["dur"], user),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"

            # 2. Video/File Download
            elif "vid_" in queued:
                mystic = await app.send_message(original_chat_id, _["call_7"])
                try:
                    file_path, _ = await YouTube.download(videoid, mystic, videoid=True, video=video)
                except:
                    return await mystic.edit_text(_["call_6"])
                
                stream = dynamic_media_stream(path=file_path, video=video, image=img)
                await self.join_call_robust(client, chat_id, stream)
                
                button = stream_markup(_, videoid, chat_id)
                await mystic.delete()
                run = await app.send_photo(
                    chat_id=original_chat_id, photo=img,
                    caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{videoid}", title[:23], check[0]["dur"], user),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"

            # 3. Index/Direct Link
            elif "index_" in queued:
                stream = dynamic_media_stream(path=videoid, video=video, image=img)
                await self.join_call_robust(client, chat_id, stream)
                
                button = stream_markup(_, videoid, chat_id)
                run = await app.send_photo(
                    chat_id=original_chat_id, photo=config.STREAM_IMG_URL,
                    caption=_["stream_2"].format(user),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"

            # 4. Standard/Audio
            else:
                stream = dynamic_media_stream(path=queued, video=video, image=img)
                await self.join_call_robust(client, chat_id, stream)

                if videoid == "telegram":
                    button = stream_markup2(_, chat_id) if stream_markup2 else stream_markup(_, "telegram", chat_id)
                    photo = config.TELEGRAM_AUDIO_URL if str(streamtype) == "audio" else config.TELEGRAM_VIDEO_URL
                    run = await app.send_photo(
                        chat_id=original_chat_id, photo=photo,
                        caption=_["stream_1"].format(config.SUPPORT_CHAT, title[:23], check[0]["dur"], user),
                        reply_markup=InlineKeyboardMarkup(button),
                    )
                elif videoid == "soundcloud":
                    button = stream_markup2(_, chat_id) if stream_markup2 else stream_markup(_, "soundcloud", chat_id)
                    run = await app.send_photo(
                        chat_id=original_chat_id, photo=config.SOUNCLOUD_IMG_URL,
                        caption=_["stream_1"].format(config.SUPPORT_CHAT, title[:23], check[0]["dur"], user),
                        reply_markup=InlineKeyboardMarkup(button),
                    )
                else:
                    button = stream_markup(_, videoid, chat_id)
                    run = await app.send_photo(
                        chat_id=original_chat_id, photo=img,
                        caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{videoid}", title[:23], check[0]["dur"], user),
                        reply_markup=InlineKeyboardMarkup(button),
                    )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"

        except Exception as e:
            LOGGER(__name__).error(f"❌ Play Loop Error: {e}")
            await _clear_(chat_id)

    @capture_internal_err
    async def ping(self) -> str:
        pings = []
        clients = [c for c in [self.one, self.two, self.three, self.four, self.five] if c]
        for cli in clients:
            if cli.ping: pings.append(cli.ping)
        return str(round(sum(pings) / len(pings), 3)) if pings else "0.0"

    # ===================================================================
    # ⚠️ معالج التحديثات (Smart Update Handler - NO IMPORTS)
    # ===================================================================
    @capture_internal_err
    async def decorators(self) -> None:
        assistants = [c for c in [self.one, self.two, self.three, self.four, self.five] if c]
        
        async def unified_update_handler(client, update: Update) -> None:
            try:
                # 1. Stream Ended
                if isinstance(update, StreamEnded):
                    if update.stream_type == StreamEnded.Type.AUDIO:
                        LOGGER(__name__).info(f"🎵 Stream Ended {update.chat_id}, Next...")
                        await self.play(client, update.chat_id)
                
                # 2. Chat Update (Kicked/Left)
                elif isinstance(update, ChatUpdate):
                    if update.status in [ChatUpdate.Status.KICKED, ChatUpdate.Status.LEFT_GROUP, ChatUpdate.Status.CLOSED_VOICE_CHAT]:
                        LOGGER(__name__).info(f"🚫 Chat Status {update.status} in {update.chat_id}")
                        await self.stop_stream(update.chat_id)
                
                # 3. الحل الجذري لمشكلة Wrapper Error
                # بدلاً من استيراد الكلاس المفقود، نتأكد إن الكائن فيه chat_id
                # ومش من الأنواع اللي احنا عارفينها فوق
                elif hasattr(update, 'chat_id'):
                    # ده غالباً التحديث الداخلي اللي بيعمل المشكلة
                    # بنعمل stop عشان ننظف الداتا ونمنع التعليق
                    await self.stop_stream(update.chat_id)
                        
            except Exception as e:
                LOGGER(__name__).error(f"Update Handler: {e}")

        for assistant in assistants:
            assistant.on_update()(unified_update_handler)

Hotty = Call()
