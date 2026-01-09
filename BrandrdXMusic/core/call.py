import asyncio
import os
from datetime import datetime, timedelta
from typing import Union
from functools import wraps

from pyrogram import Client
from pyrogram.errors import FloodWait, ChatAdminRequired, UserAlreadyParticipant
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

# =======================================================================
# 🩹 PATCH: إصلاح مشكلة chat_id (Standard Fix)
# =======================================================================
try:
    from pytgcalls.types import UpdateGroupCall
    if not hasattr(UpdateGroupCall, 'chat_id'):
        UpdateGroupCall.chat_id = property(lambda self: getattr(getattr(self, "chat", None), "id", 0))
except: pass

# =======================================================================
# 🧱 جدار الحماية (Exception Firewall)
# =======================================================================
class _DummyException(Exception): pass
try: from pytgcalls.exceptions import NoActiveGroupCall
except ImportError: NoActiveGroupCall = _DummyException
try: from pytgcalls.exceptions import NoAudioSourceFound
except ImportError: NoAudioSourceFound = _DummyException
try: from pytgcalls.exceptions import NoVideoSourceFound
except ImportError: NoVideoSourceFound = _DummyException
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
    add_active_chat, add_active_video_chat,
    get_lang, get_loop,
    group_assistant, is_autoend,
    music_on, remove_active_chat,
    remove_active_video_chat, set_loop,
)
from BrandrdXMusic.utils.exceptions import AssistantErr
from BrandrdXMusic.utils.formatters import check_duration, seconds_to_min, speed_converter
from BrandrdXMusic.utils.inline.play import stream_markup
from BrandrdXMusic.utils.stream.autoclear import auto_clean
from BrandrdXMusic.utils.thumbnails import get_thumb

autoend = {}
counter = {}

# =======================================================================
# 🛡️ معالج الأخطاء الصامت (Silent Error Handler)
# =======================================================================
def capture_internal_err(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            LOGGER(__name__).error(f"⚠️ Handled Error in {func.__name__}: {e}")
            return None
    return wrapper

# =======================================================================
# 🚀 إعدادات البث (High Stability)
# =======================================================================
def dynamic_media_stream(path: str, video: bool = False, image: str = None, ffmpeg_params: str = None) -> MediaStream:
    audio_q = AudioQuality.HIGH
    video_q = VideoQuality.HD_720p if video else VideoQuality.SD_480p
    
    # تحسينات Latency عشان المساعد ميتأخرش
    base_params = "-preset ultrafast -tune zerolatency"
    final_params = f"{base_params} {ffmpeg_params}" if ffmpeg_params else base_params

    if video:
        return MediaStream(
            media_path=path,
            audio_parameters=audio_q,
            video_parameters=video_q,
            audio_flags=MediaStream.Flags.REQUIRED,
            video_flags=MediaStream.Flags.REQUIRED,
            ffmpeg_parameters=final_params
        )
    else:
        return MediaStream(
            media_path=path,
            audio_parameters=audio_q,
            audio_flags=MediaStream.Flags.REQUIRED,
            video_flags=MediaStream.Flags.IGNORE,
            ffmpeg_parameters=final_params
        )

async def _clear_(chat_id: int) -> None:
    try:
        popped = db.pop(chat_id, None)
        if popped: await auto_clean(popped)
        if chat_id in db: del db[chat_id]
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        await set_loop(chat_id, 0)
    except: pass

# =======================================================================
# 📞 الكلاس الرئيسي (The Persistent Engine)
# =======================================================================
class Call:
    def __init__(self):
        self.userbot1 = Client("BrandrdXAssis1", config.API_ID, config.API_HASH, session_string=config.STRING1) if config.STRING1 else None
        self.one = PyTgCalls(self.userbot1) if self.userbot1 else None
        
        # بنعرف باقي المساعدين عادي عشان لو السورس احتاجهم، بس التركيز كله على الـ Assigned
        self.userbot2 = Client("BrandrdXAssis2", config.API_ID, config.API_HASH, session_string=config.STRING2) if config.STRING2 else None
        self.two = PyTgCalls(self.userbot2) if self.userbot2 else None
        self.userbot3 = Client("BrandrdXAssis3", config.API_ID, config.API_HASH, session_string=config.STRING3) if config.STRING3 else None
        self.three = PyTgCalls(self.userbot3) if self.userbot3 else None
        self.userbot4 = Client("BrandrdXAssis4", config.API_ID, config.API_HASH, session_string=config.STRING4) if config.STRING4 else None
        self.four = PyTgCalls(self.userbot4) if self.userbot4 else None
        self.userbot5 = Client("BrandrdXAssis5", config.API_ID, config.API_HASH, session_string=config.STRING5) if config.STRING5 else None
        self.five = PyTgCalls(self.userbot5) if self.userbot5 else None

        self.active_calls: set[int] = set()

    async def get_call_engine(self, chat_id: int) -> PyTgCalls:
        try:
            userbot = await group_assistant(self, chat_id)
            if userbot:
                if self.userbot1 and userbot.me.id == self.userbot1.me.id: return self.one
                if self.userbot2 and userbot.me.id == self.userbot2.me.id: return self.two
                if self.userbot3 and userbot.me.id == self.userbot3.me.id: return self.three
                if self.userbot4 and userbot.me.id == self.userbot4.me.id: return self.four
                if self.userbot5 and userbot.me.id == self.userbot5.me.id: return self.five
            return self.one
        except: return self.one

    async def start(self) -> None:
        LOGGER(__name__).info("Starting Robust Clients...")
        clients = [c for c in [self.one, self.two, self.three, self.four, self.five] if c]
        if clients:
            await asyncio.gather(*[cli.start() for cli in clients])

    # ===================================================================
    # 🥊 دالة الانضمام الشرسة (Bulldozer Function)
    # ===================================================================
    async def join_call_robust(self, assistant: PyTgCalls, chat_id: int, stream: MediaStream) -> None:
        """
        تحاول الدخول بقوة، وتعيد المحاولة تلقائياً عند الفشل، وتعالج الـ FloodWait.
        """
        attempts = 3  # عدد محاولات الإصرار
        while attempts > 0:
            try:
                await assistant.play(chat_id, stream)
                return # نجح، اخرج فوراً
            
            except (UserAlreadyParticipant, ConnectionNotFound):
                # لو قالك أنا موجود أصلاً، أو مش لاقي اتصال قديم، ده مش خطأ حقيقي
                # بنعتبره نجاح ونكمل، لأننا بعتنا أمر play
                return 

            except FloodWait as e:
                # المعالج الذكي: لو الوقت قصير انتظره وادخل، لو طويل اضرب Error
                if e.value < 15: # لو الانتظار أقل من 15 ثانية
                    LOGGER(__name__).warning(f"⏳ FloodWait {e.value}s in chat {chat_id}, Sleeping and Retrying...")
                    await asyncio.sleep(e.value + 1) # نام وكمل Loop
                    continue
                else:
                    raise AssistantErr(f"Assistant FloodWait: {e.value}s") # وقت طويل جداً
            
            except (NoActiveGroupCall, ChatAdminRequired):
                # دي أخطاء يوزر (مفيش كول أو مفيش أدمن)، مينفعش نحاول فيها تاني
                raise AssistantErr("No Active Call or No Permissions.")
            
            except Exception as e:
                # أي خطأ شبكة تاني (Timeout, ServerError)
                LOGGER(__name__).warning(f"🔄 Retry join {chat_id} due to: {e}")
                attempts -= 1
                await asyncio.sleep(1.5) # ريح ثانية ونص وحاول تاني
        
        # لو خلص المحاولات ولسه معرفش يدخل
        raise AssistantErr("Connection Failed after 3 attempts.")


    @capture_internal_err
    async def join_call(self, chat_id: int, original_chat_id: int, link: str, video: Union[bool, str] = None, image: Union[bool, str] = None) -> None:
        assistant = await self.get_call_engine(chat_id)
        lang = await get_lang(chat_id)
        _ = get_string(lang)
        stream = dynamic_media_stream(path=link, video=bool(video), image=image)

        # تنفيذ الدخول القوي
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

    @capture_internal_err
    async def stop_stream(self, chat_id: int) -> None:
        assistant = await self.get_call_engine(chat_id)
        await _clear_(chat_id)
        if chat_id in self.active_calls:
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
        if chat_id in self.active_calls:
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
        stream = dynamic_media_stream(path=link, video=bool(video), image=image)
        # استخدام نفس منطق الإصرار في التخطي
        await self.join_call_robust(assistant, chat_id, stream)

    @capture_internal_err
    async def seek_stream(self, chat_id: int, file_path: str, to_seek: str, duration: str, mode: str) -> None:
        assistant = await self.get_call_engine(chat_id)
        ffmpeg_params = f"-ss {to_seek} -to {duration}"
        stream = dynamic_media_stream(path=file_path, video=(mode == "video"), ffmpeg_params=ffmpeg_params)
        await assistant.play(chat_id, stream)

    @capture_internal_err
    async def speedup_stream(self, chat_id: int, file_path: str, speed: float, playing: list) -> None:
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
            db[chat_id][0].update({"played": con_seconds, "dur": duration_min, "seconds": dur, "speed_path": out, "speed": speed})

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
        
        try:
            try: img = await get_thumb(videoid)
            except: img = config.STREAM_IMG_URL

            if "live_" in queued:
                n, link = await YouTube.video(videoid, True)
                if n == 0: raise Exception("Live Failed")
                stream = dynamic_media_stream(path=link, video=video, image=img)
                await self.join_call_robust(client, chat_id, stream)
            
            elif "vid_" in queued:
                mystic = await app.send_message(original_chat_id, _["call_7"])
                try:
                    file_path, _ = await YouTube.download(videoid, mystic, videoid=True, video=video)
                except:
                    await mystic.delete()
                    return await app.send_message(original_chat_id, text=_["call_6"])
                stream = dynamic_media_stream(path=file_path, video=video, image=img)
                await self.join_call_robust(client, chat_id, stream)
                await mystic.delete()
                
            else:
                stream = dynamic_media_stream(path=queued, video=video, image=img)
                # استخدام join_call_robust بدل client.play العادية عشان الإصرار
                await self.join_call_robust(client, chat_id, stream)

            asyncio.create_task(self._send_playing_message(original_chat_id, videoid, title, check[0]["dur"], user, video, _, chat_id))

        except Exception as e:
            LOGGER(__name__).error(f"Play Error: {e}")
            await _clear_(chat_id)

    async def _send_playing_message(self, chat_id, videoid, title, dur, user, video, _, original_chat_id_for_markup):
        try:
            img = await get_thumb(videoid)
            button = stream_markup(_, videoid, original_chat_id_for_markup)
            
            if videoid == "telegram":
                 photo = config.TELEGRAM_VIDEO_URL if video else config.TELEGRAM_AUDIO_URL
                 link = config.SUPPORT_CHAT
            elif videoid == "soundcloud":
                 photo = config.SOUNCLOUD_IMG_URL
                 link = config.SUPPORT_CHAT
            else:
                 photo = img
                 link = f"https://t.me/{app.username}?start=info_{videoid}"

            run = await app.send_photo(
                chat_id=chat_id, photo=photo,
                caption=_["stream_1"].format(link, title[:23], dur, user),
                reply_markup=InlineKeyboardMarkup(button),
            )
            if original_chat_id_for_markup in db:
                db[original_chat_id_for_markup][0]["mystic"] = run
                db[original_chat_id_for_markup][0]["markup"] = "tg"
        except: pass

    @capture_internal_err
    async def ping(self) -> str:
        pings = []
        clients = [c for c in [self.one, self.two, self.three, self.four, self.five] if c]
        for cli in clients:
            if cli.ping: pings.append(cli.ping)
        return str(round(sum(pings) / len(pings), 3)) if pings else "0.0"

    @capture_internal_err
    async def decorators(self) -> None:
        assistants = [c for c in [self.one, self.two, self.three, self.four, self.five] if c]
        async def unified_update_handler(client, update: Update) -> None:
            if isinstance(update, StreamEnded):
                if update.stream_type == StreamEnded.Type.AUDIO:
                    await self.play(client, update.chat_id)
            elif isinstance(update, ChatUpdate):
                if update.status == ChatUpdate.Status.KICKED or \
                   update.status == ChatUpdate.Status.LEFT_GROUP or \
                   update.status == ChatUpdate.Status.CLOSED_VOICE_CHAT:
                    await self.stop_stream(update.chat_id)
        for assistant in assistants:
            assistant.on_update()(unified_update_handler)

Hotty = Call()
