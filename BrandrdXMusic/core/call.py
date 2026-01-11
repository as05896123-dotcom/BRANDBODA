# -*- coding: utf-8 -*-
"""
call.py — Call controller for BrandrdXMusic
مصمم للعمل مع:
 - py-tgcalls >= 2.2.8
 - ntgcalls >= 2.0.6 (fallback)
تحسينات:
 - حماية من الاستثناءات الغير متوافرة
 - الكشف عن UpdateGroupCall بدون chat_id
 - استرداد Zombie Calls
 - watchdog دوري و locks لكل chat
 - دعم حتى 5 مساعدين
"""

import asyncio
import os
import random
import contextlib
from datetime import datetime, timedelta
from typing import Union, Optional, Dict

from pyrogram import Client
from pyrogram.errors import UserAlreadyParticipant
from pyrogram.types import InlineKeyboardMarkup

from pytgcalls import PyTgCalls
from pytgcalls.types import (
    MediaStream,
    AudioQuality,
    VideoQuality,
    StreamEnded,
    ChatUpdate,
    Update,
)

# استيراد الاستثناءات بتسامح (fallbacks إذا لم توجد)
try:
    from pytgcalls.exceptions import (
        NoActiveGroupCall,
        NoAudioSourceFound,
        NoVideoSourceFound,
        ConnectionNotFound,
        AlreadyJoinedError,
        GroupCallNotFound,
    )
except Exception:
    class NoActiveGroupCall(Exception): pass
    class NoAudioSourceFound(Exception): pass
    class NoVideoSourceFound(Exception): pass
    class ConnectionNotFound(Exception): pass
    class AlreadyJoinedError(Exception): pass
    class GroupCallNotFound(Exception): pass

# TelegramServerError قد تكون متوفرة في ntgcalls
try:
    from pytgcalls.exceptions import TelegramServerError
except Exception:
    try:
        from ntgcalls import TelegramServerError  # بعض الحزم توفرها هنا
    except Exception:
        class TelegramServerError(Exception): pass

# raw functions لإنشاء GroupCall عند الحاجة
from pyrogram.raw import functions as raw_functions

# استيراد حاجات المشروع
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
from BrandrdXMusic.utils.stream.autoclear import auto_clean
from BrandrdXMusic.utils.thumbnails import get_thumb
from BrandrdXMusic.utils.inline.play import stream_markup

try:
    from BrandrdXMusic.utils.inline.play import stream_markup2
except Exception:
    stream_markup2 = None

# حالات عامة
autoend: Dict[int, datetime] = {}
locks: Dict[int, asyncio.Lock] = {}
watchdog_task: Optional[asyncio.Task] = None

def get_lock(chat_id: int) -> asyncio.Lock:
    """كل دردشة لها Lock لمنع حالات السباق عند تغيير المسار/الانضمام."""
    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    return locks[chat_id]

def safe_extract_chat_id(update) -> Optional[int]:
    """حاول استخراج chat_id من Update بطرق متعددة لتغلب على اختلاف أشكال التحديث."""
    try:
        if hasattr(update, "chat_id"):
            cid = getattr(update, "chat_id")
            if isinstance(cid, int):
                return cid
        if hasattr(update, "chat"):
            chat = getattr(update, "chat")
            if hasattr(chat, "id"):
                return getattr(chat, "id")
        # بعض النسخ تحتوي group_call أو call
        for attr in ("group_call", "call", "peer", "message"):
            if hasattr(update, attr):
                obj = getattr(update, attr)
                if isinstance(obj, int):
                    return obj
                if hasattr(obj, "chat_id"):
                    return getattr(obj, "chat_id")
                if hasattr(obj, "id"):
                    return getattr(obj, "id")
    except Exception:
        return None
    return None

def build_stream(path: str, video: bool = False, ffmpeg: Optional[str] = None, duration: int = 0) -> MediaStream:
    """بناء MediaStream مع معلمات ffmpeg مناسبة للروابط والملفات."""
    is_url = isinstance(path, str) and path.startswith("http")
    base_ffmpeg = " -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ac 2"
    final_ffmpeg = (ffmpeg or "")
    if is_url:
        final_ffmpeg += base_ffmpeg
    else:
        final_ffmpeg += " -ac 2"
    audio_params = AudioQuality.HIGH
    video_params = VideoQuality.SD_480p
    return MediaStream(
        media_path=path,
        audio_parameters=audio_params,
        audio_flags=MediaStream.Flags.REQUIRED,
        video_parameters=video_params,
        video_flags=MediaStream.Flags.REQUIRED if video else MediaStream.Flags.IGNORE,
        ffmpeg_parameters=final_ffmpeg if final_ffmpeg else None,
    )

async def _clear_(chat_id: int) -> None:
    """تنظيف السجل عند إيقاف أو انتهاء الطابور."""
    try:
        if popped := db.pop(chat_id, None):
            await auto_clean(popped)
    except Exception:
        pass
    with contextlib.suppress(Exception):
        await remove_active_video_chat(chat_id)
    with contextlib.suppress(Exception):
        await remove_active_chat(chat_id)
    with contextlib.suppress(Exception):
        await set_loop(chat_id, 0)

class Call:
    def __init__(self):
        # إنشاء المستخدمين المساعدين إن وُجدوا
        self.userbot1 = Client("BrandrdXMusic1", config.API_ID, config.API_HASH, session_string=getattr(config, "STRING1", None)) if getattr(config, "STRING1", None) else None
        self.one = PyTgCalls(self.userbot1) if self.userbot1 else None

        self.userbot2 = Client("BrandrdXMusic2", config.API_ID, config.API_HASH, session_string=getattr(config, "STRING2", None)) if getattr(config, "STRING2", None) else None
        self.two = PyTgCalls(self.userbot2) if self.userbot2 else None

        self.userbot3 = Client("BrandrdXMusic3", config.API_ID, config.API_HASH, session_string=getattr(config, "STRING3", None)) if getattr(config, "STRING3", None) else None
        self.three = PyTgCalls(self.userbot3) if self.userbot3 else None

        self.userbot4 = Client("BrandrdXMusic4", config.API_ID, config.API_HASH, session_string=getattr(config, "STRING4", None)) if getattr(config, "STRING4", None) else None
        self.four = PyTgCalls(self.userbot4) if self.userbot4 else None

        self.userbot5 = Client("BrandrdXMusic5", config.API_ID, config.API_HASH, session_string=getattr(config, "STRING5", None)) if getattr(config, "STRING5", None) else None
        self.five = PyTgCalls(self.userbot5) if self.userbot5 else None

        self.active_calls = set()
        self.pytgcalls_map = {
            id(self.userbot1) if self.userbot1 else None: self.one,
            id(self.userbot2) if self.userbot2 else None: self.two,
            id(self.userbot3) if self.userbot3 else None: self.three,
            id(self.userbot4) if self.userbot4 else None: self.four,
            id(self.userbot5) if self.userbot5 else None: self.five,
        }

    async def get_tgcalls(self, chat_id: int) -> PyTgCalls:
        """اختيار PyTgCalls المناسب بناءً على assistant الموجود في DB."""
        assistant = await group_assistant(self, chat_id)
        return self.pytgcalls_map.get(id(assistant), self.one)

    async def _assistant_is_admin(self, assistant: Client, chat_id: int) -> bool:
        """تحقق إن المساعد (حساب المستخدم) مشرف في الجروب مع صلاحية إدارة المكالمات."""
        try:
            if not assistant:
                return False
            me = await assistant.get_me()
            if not me:
                return False
            aid = getattr(me, "id", None)
            member = await assistant.get_chat_member(chat_id, aid)
            status = getattr(member, "status", "")
            if status in ("administrator", "creator"):
                # بعض الإصدارات تحتوي privileges attribute
                priv = getattr(member, "privileges", None)
                if priv is None:
                    return True
                for p in ("can_manage_voice_chats", "can_manage_video_chats", "can_manage_calls"):
                    if hasattr(priv, p):
                        if getattr(priv, p):
                            return True
                        else:
                            return False
                return True
            return False
        except Exception:
            return False

    async def _play_stream_safe(self, client: PyTgCalls, chat_id: int, path: str, video: bool, duration_sec: int = 0, ffmpeg: Optional[str] = None):
        """محاولة تشغيل Stream مع تحليل الأخطاء ومحاولات متكررة قصيرة."""
        stream = build_stream(path, video, ffmpeg, duration_sec)
        last_exc = None
        for attempt in range(1, 3):
            try:
                await client.play(chat_id, stream)
                return
            except (NoActiveGroupCall, GroupCallNotFound) as e:
                # لا توجد مكالمة نشطة
                raise NoActiveGroupCall()
            except Exception as e:
                last_exc = e
                err = str(e)
                if "GROUPCALL_INVALID" in err or "call_interface" in err:
                    raise NoActiveGroupCall()
                try:
                    LOGGER(__name__).warning(f"_play_stream_safe attempt {attempt} for {chat_id} error: {err}")
                except Exception:
                    pass
                await asyncio.sleep(0.5 * attempt)
        if last_exc:
            raise last_exc

    async def start(self):
        """تشغيل جميع عملاء PyTgCalls وربط المعالجات."""
        try:
            LOGGER(__name__).info("🚀 Starting Audio Engine...")
        except Exception:
            pass
        clients = [c for c in (self.one, self.two, self.three, self.four, self.five) if c]
        for c in clients:
            try:
                await c.start()
            except Exception as e:
                try:
                    LOGGER(__name__).warning(f"Failed to start PyTgCalls client: {e}")
                except Exception:
                    pass
        await self.decorators()
        self._start_watchdog()

    async def ping(self) -> str:
        pings = []
        for c in (self.one, self.two, self.three, self.four, self.five):
            if c:
                with contextlib.suppress(Exception):
                    pings.append(c.ping)
        return str(round(sum(pings) / len(pings), 3)) if pings else "0.0"

    # تحكمات بسيطة
    async def pause_stream(self, chat_id: int):
        client = await self.get_tgcalls(chat_id)
        with contextlib.suppress(Exception):
            await client.pause(chat_id)

    async def resume_stream(self, chat_id: int):
        client = await self.get_tgcalls(chat_id)
        with contextlib.suppress(Exception):
            await client.resume(chat_id)

    async def mute_stream(self, chat_id: int):
        client = await self.get_tgcalls(chat_id)
        with contextlib.suppress(Exception):
            await client.mute(chat_id)

    async def unmute_stream(self, chat_id: int):
        client = await self.get_tgcalls(chat_id)
        with contextlib.suppress(Exception):
            await client.unmute(chat_id)

    async def stop_stream(self, chat_id: int):
        client = await self.get_tgcalls(chat_id)
        await _clear_(chat_id)
        if chat_id in self.active_calls:
            try:
                await client.leave_call(chat_id)
            except Exception as e:
                try:
                    LOGGER(__name__).warning(f"stop_stream leave_call failed for {chat_id}: {e}")
                except Exception:
                    pass
            finally:
                self.active_calls.discard(chat_id)

    async def force_stop_stream(self, chat_id: int):
        client = await self.get_tgcalls(chat_id)
        try:
            check = db.get(chat_id)
            if check:
                check.pop(0)
        except Exception:
            pass
        with contextlib.suppress(Exception):
            await remove_active_video_chat(chat_id)
            await remove_active_chat(chat_id)
            await _clear_(chat_id)
        if chat_id in self.active_calls:
            try:
                await client.leave_call(chat_id)
            except Exception:
                pass
            finally:
                self.active_calls.discard(chat_id)

    async def join_call(self, chat_id: int, original_chat_id: int, link: str, video: Union[bool, str] = None, image: Union[bool, str] = None):
        """الانضمام إلى المكالمة وتشغيل الملف/الرابط مع فحوصات admin و retry."""
        client = await self.get_tgcalls(chat_id)
        assistant = await group_assistant(self, chat_id)
        lang = await get_lang(chat_id)
        _ = get_string(lang)

        if not link.startswith("http"):
            link = os.path.abspath(link)

        lock = get_lock(chat_id)
        async with lock:
            with contextlib.suppress(Exception):
                await assistant.join_chat(chat_id)

            try:
                try:
                    await self._play_stream_safe(client, chat_id, link, bool(video))
                except NoActiveGroupCall:
                    # تأكد أن المساعد admin قبل محاولة CreateGroupCall
                    is_admin = await self._assistant_is_admin(assistant, chat_id)
                    if not is_admin:
                        raise AssistantErr(_["call_9"] if "call_9" in _ else "⚠️ البوت يحتاج أن يكون مشرفًا لبدء المكالمة.")
                    try:
                        peer = await assistant.resolve_peer(chat_id)
                        random_id = random.getrandbits(32)
                        await assistant.send(raw_functions.phone.CreateGroupCall(peer=peer, random_id=random_id))
                        await asyncio.sleep(1.2)
                    except Exception as ce:
                        # لو فشل الإنشاء، أبلغ المستخدم برسالة عامة
                        try:
                            LOGGER(__name__).warning(f"CreateGroupCall failed for {chat_id}: {ce}")
                        except Exception:
                            pass
                        raise AssistantErr(_["call_8"] if "call_8" in _ else "فشل بدء المكالمة.")
                    # محاولة تشغيل ثانية
                    await self._play_stream_safe(client, chat_id, link, bool(video))
            except (NoAudioSourceFound, NoVideoSourceFound):
                raise AssistantErr(_["call_11"] if "call_11" in _ else "لم يتم العثور على مصدر صوت/فيديو.")
            except (TelegramServerError, ConnectionNotFound):
                raise AssistantErr(_["call_10"] if "call_10" in _ else "خطأ في خوادم تيليجرام أو الاتصال.")
            except AssistantErr:
                raise
            except Exception as e:
                try:
                    LOGGER(__name__).error(f"Join Call Error for {chat_id}: {e}")
                except Exception:
                    pass
                raise AssistantErr(_["call_8"] if "call_8" in _ else "فشل في الانضمام للمكالمة.")

            # نجاح
            self.active_calls.add(chat_id)
            await add_active_chat(chat_id)
            await music_on(chat_id)
            if video:
                await add_active_video_chat(chat_id)

            # autoend detection
            if await is_autoend():
                try:
                    # حاول استخدام get_participants ثم fallback ل get_chat_members_count
                    participants = None
                    with contextlib.suppress(Exception):
                        if hasattr(assistant, "get_participants"):
                            parts = await assistant.get_participants(chat_id)
                            participants = len(parts) if parts is not None else None
                    with contextlib.suppress(Exception):
                        if participants is None:
                            participants = await assistant.get_chat_members_count(chat_id)
                    if participants is not None and participants <= 1:
                        autoend[chat_id] = datetime.now() + timedelta(minutes=1)
                except Exception:
                    pass

    async def change_stream(self, client: PyTgCalls, chat_id: int):
        """التبديل إلى المسار التالي في الطابور."""
        lock = get_lock(chat_id)
        async with lock:
            check = db.get(chat_id)
            popped = None
            try:
                loop = await get_loop(chat_id)
            except Exception:
                loop = 0
            try:
                if not check:
                    await _clear_(chat_id)
                    if chat_id in self.active_calls:
                        with contextlib.suppress(Exception):
                            await client.leave_call(chat_id)
                        self.active_calls.discard(chat_id)
                    return

                if loop == 0:
                    popped = check.pop(0)
                else:
                    loop -= 1
                    await set_loop(chat_id, loop)

                if popped:
                    with contextlib.suppress(Exception):
                        await auto_clean(popped)

                if not check:
                    await _clear_(chat_id)
                    if chat_id in self.active_calls:
                        with contextlib.suppress(Exception):
                            await client.leave_call(chat_id)
                        self.active_calls.discard(chat_id)
                    return
            except Exception as e:
                try:
                    LOGGER(__name__).error(f"change_stream prepare error for {chat_id}: {e}")
                except Exception:
                    pass
                with contextlib.suppress(Exception):
                    await _clear_(chat_id)
                    await client.leave_call(chat_id)
                return

            queued = check[0].get("file")
            lang = await get_lang(chat_id)
            _ = get_string(lang)
            title = (check[0].get("title") or "").title()
            user = check[0].get("by")
            original_chat_id = check[0].get("chat_id")
            streamtype = check[0].get("streamtype")
            videoid = check[0].get("vidid")
            duration_sec = check[0].get("seconds", 0)

            db[chat_id][0]["played"] = 0
            video = True if str(streamtype) == "video" else False

            def get_btn(vid_id):
                if stream_markup2:
                    return stream_markup2(_, chat_id)
                return stream_markup(_, vid_id, chat_id)

            try:
                if "live_" in queued:
                    n, link = await YouTube.video(videoid, True)
                    if n == 0:
                        return await app.send_message(original_chat_id, text=_["call_6"])
                    await self._play_stream_safe(client, chat_id, link, video, 0)
                    img = await get_thumb(videoid)
                    run = await app.send_photo(
                        chat_id=original_chat_id,
                        photo=img,
                        caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{videoid}", title[:23], check[0].get("dur", ""), user),
                        reply_markup=InlineKeyboardMarkup(get_btn(videoid)),
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"

                elif "vid_" in queued:
                    mystic = await app.send_message(original_chat_id, _["call_7"])
                    try:
                        file_path, direct = await YouTube.download(videoid, mystic, videoid=True, video=video)
                    except Exception:
                        return await mystic.edit_text(_["call_6"])
                    await self._play_stream_safe(client, chat_id, file_path, video, duration_sec)
                    img = await get_thumb(videoid)
                    with contextlib.suppress(Exception):
                        await mystic.delete()
                    run = await app.send_photo(
                        chat_id=original_chat_id,
                        photo=img,
                        caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{videoid}", title[:23], check[0].get("dur", ""), user),
                        reply_markup=InlineKeyboardMarkup(stream_markup(_, videoid, chat_id)),
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "stream"

                elif "index_" in queued:
                    await self._play_stream_safe(client, chat_id, videoid, video, duration_sec)
                    run = await app.send_photo(
                        chat_id=original_chat_id,
                        photo=config.STREAM_IMG_URL,
                        caption=_["stream_2"].format(user),
                        reply_markup=InlineKeyboardMarkup(get_btn(videoid)),
                    )
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"

                else:
                    await self._play_stream_safe(client, chat_id, queued, video, duration_sec)

                    if videoid == "telegram":
                        img = config.TELEGRAM_AUDIO_URL if str(streamtype) == "audio" else config.TELEGRAM_VIDEO_URL
                        run = await app.send_photo(
                            chat_id=original_chat_id,
                            photo=img,
                            caption=_["stream_1"].format(config.SUPPORT_CHAT, title[:23], check[0].get("dur", ""), user),
                            reply_markup=InlineKeyboardMarkup(get_btn("telegram")),
                        )
                        db[chat_id][0]["mystic"] = run
                        db[chat_id][0]["markup"] = "tg"

                    elif videoid == "soundcloud":
                        run = await app.send_photo(
                            chat_id=original_chat_id,
                            photo=config.SOUNDCLOUD_IMG_URL,
                            caption=_["stream_1"].format(config.SUPPORT_CHAT, title[:23], check[0].get("dur", ""), user),
                            reply_markup=InlineKeyboardMarkup(get_btn("soundcloud")),
                        )
                        db[chat_id][0]["mystic"] = run
                        db[chat_id][0]["markup"] = "tg"

                    else:
                        img = await get_thumb(videoid)
                        run = await app.send_photo(
                            chat_id=original_chat_id,
                            photo=img,
                            caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{videoid}", title[:23], check[0].get("dur", ""), user),
                            reply_markup=InlineKeyboardMarkup(stream_markup(_, videoid, chat_id)),
                        )
                        db[chat_id][0]["mystic"] = run
                        db[chat_id][0]["markup"] = "stream"

            except Exception as e:
                try:
                    LOGGER(__name__).error(f"Play Error in change_stream for {chat_id}: {e}")
                except Exception:
                    pass
                try:
                    await self.change_stream(client, chat_id)
                except Exception:
                    pass

    async def skip_stream(self, chat_id: int, link: str, video: Union[bool, str] = None, image: Union[bool, str] = None):
        client = await self.get_tgcalls(chat_id)
        if not link.startswith("http"):
            link = os.path.abspath(link)
        await self._play_stream_safe(client, chat_id, link, bool(video))

    async def seek_stream(self, chat_id: int, file_path: str, to_seek: str, duration: str, mode: str):
        client = await self.get_tgcalls(chat_id)
        file_path = os.path.abspath(file_path)
        ffmpeg = f"-ss {to_seek} -to {duration}"
        await self._play_stream_safe(client, chat_id, file_path, (mode == "video"), ffmpeg=ffmpeg)

    async def speedup_stream(self, chat_id: int, file_path: str, speed: float, playing: list):
        client = await self.get_tgcalls(chat_id)
        file_path = os.path.abspath(file_path)
        base = os.path.basename(file_path)
        chatdir = os.path.join(os.getcwd(), "playback", str(speed))
        os.makedirs(chatdir, exist_ok=True)
        out = os.path.join(chatdir, base)

        if not os.path.exists(out):
            vs = str(2.0 / float(speed))
            cmd = f'ffmpeg -i "{file_path}" -filter:v "setpts={vs}*PTS" -filter:a atempo={speed} -y "{out}"'
            proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            await proc.communicate()

        dur = int(await asyncio.get_event_loop().run_in_executor(None, check_duration, out))
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        ffmpeg = f"-ss {played} -to {seconds_to_min(dur)}"

        if chat_id in db:
            await self._play_stream_safe(client, chat_id, out, (playing[0]["streamtype"] == "video"), ffmpeg=ffmpeg)
            db[chat_id][0].update({
                "played": con_seconds,
                "dur": seconds_to_min(dur),
                "seconds": dur,
                "speed_path": out,
                "speed": speed
            })

    async def decorators(self):
        """ربط معالج موحّد لتحديثات PyTgCalls (StreamEnded, ChatUpdate,...)."""
        assistants = list(filter(None, (self.one, self.two, self.three, self.four, self.five)))

        async def unified_update_handler(client, update: Update):
            try:
                chat_id = safe_extract_chat_id(update)
                if not chat_id:
                    return

                if isinstance(update, StreamEnded):
                    try:
                        await self.change_stream(client, chat_id)
                    except Exception as e:
                        try:
                            LOGGER(__name__).error(f"Error handling StreamEnded for {chat_id}: {e}")
                        except Exception:
                            pass

                elif isinstance(update, ChatUpdate):
                    try:
                        status = update.status
                        if status in (ChatUpdate.Status.LEFT_CALL, ChatUpdate.Status.KICKED, ChatUpdate.Status.CLOSED_VOICE_CHAT):
                            await self.stop_stream(chat_id)
                    except Exception as e:
                        try:
                            LOGGER(__name__).warning(f"ChatUpdate handling warning for {chat_id}: {e}")
                        except Exception:
                            pass
            except Exception as e:
                try:
                    LOGGER(__name__).warning(f"unified_update_handler outer error: {e}")
                except Exception:
                    pass

        for assistant in assistants:
            try:
                if hasattr(assistant, "on_update"):
                    assistant.on_update()(unified_update_handler)
            except Exception as e:
                try:
                    LOGGER(__name__).error(f"Failed to attach decorators: {e}")
                except Exception:
                    pass

    # watchdog loop للمراقبة واستعادة المكالمات الميتة
    def _start_watchdog(self):
        global watchdog_task
        if watchdog_task and not watchdog_task.done():
            return
        watchdog_task = asyncio.create_task(self._watchdog_loop())

    async def _watchdog_loop(self):
        while True:
            try:
                active = list(self.active_calls)
                for chat_id in active:
                    try:
                        assistant = await group_assistant(self, chat_id)
                        if not assistant:
                            await _clear_(chat_id)
                            self.active_calls.discard(chat_id)
                            continue
                        # تحقق عدد المشاركين
                        participants_count = None
                        with contextlib.suppress(Exception):
                            if hasattr(assistant, "get_participants"):
                                parts = await assistant.get_participants(chat_id)
                                participants_count = len(parts) if parts is not None else None
                        with contextlib.suppress(Exception):
                            if participants_count is None:
                                participants_count = await assistant.get_chat_members_count(chat_id)

                        # إذا بقي المساعد وحده -> جدولة autoend أو إغلاق
                        if participants_count is not None and participants_count <= 1:
                            if await is_autoend():
                                if chat_id not in autoend:
                                    autoend[chat_id] = datetime.now() + timedelta(minutes=1)
                            else:
                                await self.stop_stream(chat_id)
                                continue

                        # تنفيذ autoend عند الوقوع في الوقت
                        if chat_id in autoend:
                            if datetime.now() >= autoend[chat_id]:
                                await self.stop_stream(chat_id)
                                autoend.pop(chat_id, None)

                        # كشف مكالمات ميتة: إذا المساعد خارج المكالمة لكن queue موجودة -> نحاول recovery
                        in_call = True
                        with contextlib.suppress(Exception):
                            try:
                                parts = await assistant.get_participants(chat_id)
                                if not parts:
                                    in_call = False
                            except Exception:
                                in_call = False
                        if not in_call:
                            q = db.get(chat_id)
                            if q and len(q) > 0:
                                # حاول الاسترداد إذا المساعد admin
                                is_admin = await self._assistant_is_admin(assistant, chat_id)
                                if not is_admin:
                                    await self.stop_stream(chat_id)
                                    continue
                                try:
                                    client = await self.get_tgcalls(chat_id)
                                    first = q[0]
                                    file_path = first.get("file")
                                    video_flag = True if str(first.get("streamtype")) == "video" else False
                                    await self._play_stream_safe(client, chat_id, file_path, video_flag, first.get("seconds", 0))
                                    self.active_calls.add(chat_id)
                                except Exception as ex_re:
                                    try:
                                        LOGGER(__name__).warning(f"Recovery failed for {chat_id}: {ex_re}")
                                    except Exception:
                                        pass
                                    # اذا فشلت الاستعادة، اغلق لتنجنب loops مستمرة
                                    await self.stop_stream(chat_id)
                    except Exception as inner:
                        try:
                            LOGGER(__name__).warning(f"Watchdog inner for {chat_id}: {inner}")
                        except Exception:
                            pass
                await asyncio.sleep(20)
            except asyncio.CancelledError:
                break
            except Exception as e:
                try:
                    LOGGER(__name__).error(f"Watchdog outer error: {e}")
                except Exception:
                    pass
                await asyncio.sleep(10)

# instance export
Hotty = Call()
