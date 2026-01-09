"""
██████╗ ██████╗  █████╗ ███╗   ██╗██████╗ ██████╗ ██████╗ ██╗  ██╗
██╔══██╗██╔══██╗██╔══██╗████╗  ██║██╔══██╗██╔══██╗██╔══██╗╚██╗██╔╝
██████╔╝██████╔╝███████║██╔██╗ ██║██║  ██║██████╔╝██║  ██║ ╚███╔╝ 
██╔══██╗██╔══██╗██╔══██║██║╚██╗██║██║  ██║██╔══██╗██║  ██║ ██╔██╗ 
██████╔╝██║  ██║██║  ██║██║ ╚████║██████╔╝██║  ██║██████╔╝██╔╝ ██╗
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝

[ SYSTEM: THE MASTER ENGINE - AUTOMATED & SECURE ]
[ BUILD: ULTIMATE STABILITY EDITION ]
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Union, Optional
from functools import wraps

# =======================================================================
# 🛡️ MODULE 1: SYSTEM KERNEL PATCHES (الحماية من الانهيار)
# =======================================================================
def _system_patch():
    """حقن تعديلات برمجية لمنع توقف البوت بسبب أخطاء المكتبات"""
    try:
        import pytgcalls.mtproto.pyrogram_client
        original_update = pytgcalls.mtproto.pyrogram_client.PyrogramClient.on_update

        async def secure_on_update(self, client, update):
            try:
                # فلترة التحديثات الفاسدة (Chat ID 0)
                if getattr(update, 'chat_id', None) == 0:
                    return
                await original_update(self, client, update)
            except (KeyError, IndexError):
                pass # تجاهل صامت للأخطاء غير المؤثرة
            except Exception:
                pass 

        pytgcalls.mtproto.pyrogram_client.PyrogramClient.on_update = secure_on_update
    except ImportError:
        pass

_system_patch()

# =======================================================================
# 🔌 MODULE 2: SAFE IMPORTS (الاستيراد الآمن)
# =======================================================================
class _SystemPlaceholder(Exception): pass

# استيراد PyTgCalls مع تأمين ضد الإصدارات المفقودة
try:
    from pytgcalls import PyTgCalls
    from pytgcalls.types import AudioQuality, VideoQuality, ChatUpdate, MediaStream, StreamEnded, Update
except ImportError:
    print("❌ CRITICAL SYSTEM ERROR: PyTgCalls Library Missing!")
    sys.exit(1)

# استيراد الاستثناءات بشكل ديناميكي
_EXCEPTIONS = [
    "NoActiveGroupCall", "NoAudioSourceFound", "NoVideoSourceFound", 
    "NotConnected", "GroupCallNotFound", "InvalidStreamMode"
]

for exc in _EXCEPTIONS:
    try:
        exec(f"from pytgcalls.exceptions import {exc}")
    except ImportError:
        exec(f"{exc} = _SystemPlaceholder")

from pyrogram import Client
from pyrogram.errors import FloodWait, ChatAdminRequired, UserAlreadyParticipant, MessageIdInvalid
from pyrogram.types import InlineKeyboardMarkup

# استيراد ملفات البوت الداخلية
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
from BrandrdXMusic.utils.inline.play import stream_markup
from BrandrdXMusic.utils.stream.autoclear import auto_clean
from BrandrdXMusic.utils.thumbnails import get_thumb

# محاولة استيراد stream_markup2 لو موجودة
try: from BrandrdXMusic.utils.inline.play import stream_markup2
except ImportError: stream_markup2 = None

autoend = {}
counter = {}

# =======================================================================
# ⚙️ MODULE 3: ENGINE TOOLS (أدوات التشغيل)
# =======================================================================
def system_log(func):
    """Decorator لتسجيل الأخطاء الداخلية دون إيقاف البوت"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            LOGGER(__name__).error(f"⚠️ [SYSTEM]: Error in {func.__name__} -> {e}")
            return None
    return wrapper

def create_stream_link(path: str, video: bool = False, ffmpeg: str = None) -> MediaStream:
    """إنشاء رابط تشغيل متوافق مع كافة الصيغ"""
    if video:
        return MediaStream(
            media_path=path,
            audio_parameters=AudioQuality.HIGH,
            video_parameters=VideoQuality.HD_720p,
            audio_flags=MediaStream.Flags.REQUIRED,
            video_flags=MediaStream.Flags.REQUIRED,
            ffmpeg_parameters=ffmpeg
        )
    return MediaStream(
        media_path=path,
        audio_parameters=AudioQuality.HIGH,
        audio_flags=MediaStream.Flags.REQUIRED,
        video_flags=MediaStream.Flags.IGNORE,
        ffmpeg_parameters=ffmpeg
    )

async def _safe_clean(chat_id):
    """تنظيف آمن للبيانات"""
    try:
        popped = db.pop(chat_id, None)
        if popped: await auto_clean(popped)
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        await set_loop(chat_id, 0)
    except: pass

# =======================================================================
# 🚀 MODULE 4: THE CORE CLASS (نظام الاتصال المركزي)
# =======================================================================
class Call(PyTgCalls):
    def __init__(self):
        # تحميل المساعدين (النظام الاحتياطي المتعدد)
        self.clients = []
        self._init_client(config.STRING1, "BrandrdXMusic1", "one")
        self._init_client(config.STRING2, "BrandrdXMusic2", "two")
        self._init_client(config.STRING3, "BrandrdXMusic3", "three")
        self._init_client(config.STRING4, "BrandrdXMusic4", "four")
        self._init_client(config.STRING5, "BrandrdXMusic5", "five")
        self.active_calls = set()

    def _init_client(self, session, name, attr_name):
        if session:
            cli = Client(name, config.API_ID, config.API_HASH, session_string=session)
            tg_cli = PyTgCalls(cli)
            setattr(self, f"userbot{attr_name}", cli) # Legacy support
            setattr(self, attr_name, tg_cli)          # Legacy support
            self.clients.append(tg_cli)
        else:
            setattr(self, f"userbot{attr_name}", None)
            setattr(self, attr_name, None)

    async def start(self):
        LOGGER(__name__).info("⚡ Initializing Sound System...")
        await asyncio.gather(*[c.start() for c in self.clients])
        LOGGER(__name__).info("✅ All Assistant Clients Started.")

    @system_log
    async def join_call(self, chat_id, original_chat_id, link, video=None, image=None):
        """دالة الدخول الذكية مع المحاولات المتكررة"""
        assistant = await group_assistant(self, chat_id)
        stream = create_stream_link(path=link, video=bool(video))
        lang = await get_lang(chat_id)
        _ = get_string(lang)

        # محاولة الدخول (نظام Retry)
        try:
            await assistant.play(chat_id, stream)
        except (NoActiveGroupCall, ChatAdminRequired):
            raise AssistantErr(_["call_8"])
        except (UserAlreadyParticipant, KeyError):
            pass # هو موجود بالفعل، كمل شغل
        except FloodWait as e:
            # انتظر وحاول مرة أخرى
            await asyncio.sleep(e.value + 2)
            try: await assistant.play(chat_id, stream)
            except: pass
        except Exception as e:
            # لو فشل تماماً، بلغ المستخدم
            if "No audio" in str(e): raise AssistantErr(_["call_11"])
            pass

        self.active_calls.add(chat_id)
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video: await add_active_video_chat(chat_id)

        # نظام الإغلاق التلقائي
        if await is_autoend():
            try:
                if len(await assistant.get_participants(chat_id)) <= 1:
                    autoend[chat_id] = datetime.now() + timedelta(minutes=1)
            except: pass

    @system_log
    async def play(self, client, chat_id):
        """نظام التشغيل الرئيسي (المتوافق مع قاعدة البيانات القديمة)"""
        check = db.get(chat_id)
        if not check:
            await self._cleanup_and_leave(client, chat_id)
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
                await self._cleanup_and_leave(client, chat_id)
                return
        except:
            await self._cleanup_and_leave(client, chat_id)
            return

        # استخراج البيانات
        track = check[0]
        queued = track["file"]
        title = track["title"].title()
        user = track["by"]
        orig_chat = track["chat_id"]
        stype = track["streamtype"]
        vidid = track["vidid"]
        duration = track["dur"]
        db[chat_id][0]["played"] = 0
        video = True if str(stype) == "video" else False
        
        # استعادة المدة الأصلية لو تم تخزينها
        if track.get("old_dur"):
            db[chat_id][0]["dur"] = track["old_dur"]
            db[chat_id][0]["seconds"] = track["old_second"]
            db[chat_id][0]["speed_path"], db[chat_id][0]["speed"] = None, 1.0

        _ = get_string(await get_lang(chat_id))

        try:
            # 1. LIVE STREAM
            if "live_" in queued:
                n, link = await YouTube.video(vidid, True)
                if n == 0: return await self._safe_send(orig_chat, _["call_6"])
                stream = create_stream_link(link, video)
                await client.play(chat_id, stream)
                img = await get_thumb(vidid)
                btn = self._get_markup(_, vidid, chat_id)
                await self._send_play_ui(orig_chat, img, title, duration, user, vidid, btn, chat_id, "tg", _)

            # 2. DOWNLOADED VIDEO/AUDIO
            elif "vid_" in queued:
                mystic = await self._safe_send(orig_chat, _["call_7"])
                try: file_path, _ = await YouTube.download(vidid, mystic, videoid=True, video=video)
                except: 
                    if mystic: await mystic.edit_text(_["call_6"])
                    return
                stream = create_stream_link(file_path, video)
                await client.play(chat_id, stream)
                img = await get_thumb(vidid)
                btn = stream_markup(_, vidid, chat_id)
                if mystic: await mystic.delete()
                await self._send_play_ui(orig_chat, img, title, duration, user, vidid, btn, chat_id, "stream", _)

            # 3. INDEX / M3U8
            elif "index_" in queued:
                stream = create_stream_link(vidid, video)
                await client.play(chat_id, stream)
                btn = stream_markup(_, vidid, chat_id)
                await self._send_play_ui(orig_chat, config.STREAM_IMG_URL, title, duration, user, vidid, btn, chat_id, "tg", _, custom_cap=_["stream_2"].format(user))

            # 4. DIRECT LINK / PLATFORMS
            else:
                stream = create_stream_link(queued, video)
                await client.play(chat_id, stream)
                if vidid == "telegram":
                    img = config.TELEGRAM_AUDIO_URL if str(stype) == "audio" else config.TELEGRAM_VIDEO_URL
                    link_txt = config.SUPPORT_CHAT
                    btn = self._get_markup(_, "telegram", chat_id)
                elif vidid == "soundcloud":
                    img = config.SOUNCLOUD_IMG_URL
                    link_txt = config.SUPPORT_CHAT
                    btn = self._get_markup(_, "soundcloud", chat_id)
                else:
                    img = await get_thumb(vidid)
                    link_txt = f"https://t.me/{app.username}?start=info_{vidid}"
                    btn = stream_markup(_, vidid, chat_id)
                
                await self._send_play_ui(orig_chat, img, title, duration, user, link_txt, btn, chat_id, "stream", _)

        except Exception as e:
            LOGGER(__name__).error(f"Play Logic Error: {e}")
            await self._cleanup_and_leave(client, chat_id)

    # --- Helper Methods (أدوات المساعدة الداخلية) ---

    async def _cleanup_and_leave(self, client, chat_id):
        await _safe_clean(chat_id)
        if chat_id in self.active_calls:
            try: await client.leave_call(chat_id)
            except: pass
            finally: self.active_calls.discard(chat_id)

    async def _safe_send(self, chat_id, text):
        try: return await app.send_message(chat_id, text)
        except: return None

    def _get_markup(self, lang, vidid, chat_id):
        if stream_markup2: return stream_markup2(lang, chat_id)
        return stream_markup(lang, vidid, chat_id)

    async def _send_play_ui(self, chat_id, photo, title, duration, user, link, btn, db_id, m_type, lang, custom_cap=None):
        if custom_cap:
            caption = custom_cap
        else:
            # تأكد أن الرابط نص وليس كائن آخر
            real_link = link if isinstance(link, str) else f"https://t.me/{app.username}"
            caption = lang["stream_1"].format(real_link, title[:23], duration, user)
        
        try:
            msg = await app.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(btn)
            )
            if db_id in db:
                db[db_id][0]["mystic"] = msg
                db[db_id][0]["markup"] = m_type
        except Exception as e:
            LOGGER(__name__).warning(f"UI Send Failed: {e}")

    # --- Controls (أوامر التحكم) ---

    @system_log
    async def stop_stream(self, chat_id):
        assistant = await group_assistant(self, chat_id)
        await self._cleanup_and_leave(assistant, chat_id)

    @system_log
    async def force_stop_stream(self, chat_id):
        assistant = await group_assistant(self, chat_id)
        try:
            check = db.get(chat_id)
            if check: check.pop(0)
        except: pass
        await self._cleanup_and_leave(assistant, chat_id)

    @system_log
    async def skip_stream(self, chat_id, link, video=None, image=None):
        assistant = await group_assistant(self, chat_id)
        stream = create_stream_link(link, video)
        await assistant.play(chat_id, stream)

    @system_log
    async def seek_stream(self, chat_id, file_path, to_seek, duration, mode):
        assistant = await group_assistant(self, chat_id)
        params = f"-ss {to_seek} -to {duration}"
        stream = create_stream_link(file_path, mode=="video", params)
        await assistant.play(chat_id, stream)

    @system_log
    async def speedup_stream(self, chat_id, file_path, speed, playing):
        if not playing: return
        assistant = await group_assistant(self, chat_id)
        # (نفس كود التسريع الأصلي مع حماية)
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
        stream = create_stream_link(out, playing[0]["streamtype"]=="video", params)
        if chat_id in db:
            await assistant.play(chat_id, stream)
            db[chat_id][0].update({"played": con_seconds, "dur": seconds_to_min(dur), "seconds": dur, "speed_path": out, "speed": speed})

    @system_log
    async def pause_stream(self, chat_id):
        await (await group_assistant(self, chat_id)).pause(chat_id)

    @system_log
    async def resume_stream(self, chat_id):
        await (await group_assistant(self, chat_id)).resume(chat_id)

    @system_log
    async def mute_stream(self, chat_id):
        await (await group_assistant(self, chat_id)).mute(chat_id)

    @system_log
    async def unmute_stream(self, chat_id):
        await (await group_assistant(self, chat_id)).unmute(chat_id)

    @system_log
    async def ping(self):
        pings = [c.ping for c in self.clients if hasattr(c, 'ping')]
        return str(round(sum(pings)/len(pings), 3)) if pings else "0.0"

    @system_log
    async def decorators(self):
        async def handler(client, update):
            try:
                if isinstance(update, StreamEnded) and update.stream_type == StreamEnded.Type.AUDIO:
                    await self.play(client, update.chat_id)
                elif isinstance(update, ChatUpdate) and update.status in [ChatUpdate.Status.KICKED, ChatUpdate.Status.LEFT_GROUP]:
                    await self.stop_stream(update.chat_id)
            except: pass
        
        for c in self.clients:
            c.on_update()(handler)

Hotty = Call()
