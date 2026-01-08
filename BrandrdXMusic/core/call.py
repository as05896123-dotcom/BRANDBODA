"""
██████╗ ██████╗ ██████╗ ███████╗    ██████╗ ███████╗██╗     ██╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔══██╗██╔════╝██║     ██║
██║     ██║   ██║██████╔╝█████╗      ██████╔╝█████╗  ██║     ██║
██║     ██║   ██║██╔══██╗██╔══╝      ██╔══██╗██╔══╝  ██║     ██║
╚██████╗╚██████╔╝██║  ██║███████╗    ██║  ██║███████╗███████╗███████╗
 ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝    ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝

[النظام: وحدة التحكم المركزية للبث - الإصدار النووي 🚀]
[الحالة: متصل، محمي، ومعالج ذاتياً]
[المطور: تم التجهيز بواسطة أفضل ممارسات البرمجة الآمنة]
"""

import asyncio
import os
import logging
from datetime import datetime, timedelta
from typing import Union, List, Dict, Optional
from functools import wraps

# --- Pyrogram Imports ---
from pyrogram import Client
from pyrogram.errors import (
    FloodWait, 
    ChatAdminRequired,
    UserAlreadyParticipant,
    UserNotParticipant
)
from pyrogram.types import InlineKeyboardMarkup

# --- PyTgCalls Imports ---
from pytgcalls import PyTgCalls
from pytgcalls.types import (
    AudioQuality, 
    ChatUpdate, 
    MediaStream, 
    StreamEnded, 
    Update, 
    VideoQuality,
    GroupCallConfig
)

# -----------------------------------------------------------
# 🛡️ المنطقة الآمنة (Compatibility Layer & Patching)
# -----------------------------------------------------------
# معالجة اختلافات الإصدارات لتجنب الانهيار المفاجئ
try:
    from pytgcalls.exceptions import (
        NoActiveGroupCall,
        NoAudioSourceFound,
        NoVideoSourceFound,
        NotConnected,
        AlreadyJoinedError
    )
except ImportError:
    # Fallback للإصدارات الحديثة التي غيرت أسماء الاستثناءات
    from pytgcalls.exceptions import (
        NoActiveGroupCall,
        NoAudioSourceFound,
        NoVideoSourceFound,
        AlreadyJoinedError
    )
    # Patching: تعويض الاستثناء المفقود
    NotConnected = NoActiveGroupCall

# معالجة أخطاء الشبكة
try:
    from ntgcalls import TelegramServerError, ConnectionNotFound
except ImportError:
    class TelegramServerError(Exception): pass
    class ConnectionNotFound(Exception): pass

# -----------------------------------------------------------
# ⚙️ استيراد التكوينات والملحقات
# -----------------------------------------------------------
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

# متغيرات التشغيل التلقائي
autoend = {}
counter = {}

# -----------------------------------------------------------
# 🚨 نظام تسجيل الأخطاء الداخلي (Embedded Logger)
# -----------------------------------------------------------
def capture_internal_err(func):
    """
    ديكوريتور (Decorator) لحماية الدوال من الانهيار وتسجيل الأخطاء.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            func_name = func.__name__
            LOGGER(__name__).error(f"⚠️ خطأ حرج في الدالة [{func_name}]: {str(e)}")
            # يمكن إضافة إعادة محاولة (Retry Logic) هنا مستقبلاً
    return wrapper

# -----------------------------------------------------------
# 🎛️ تكوين وسائط البث (Media Configuration Factory)
# -----------------------------------------------------------
def dynamic_media_stream(path: str, video: bool = False, ffmpeg_params: str = None) -> MediaStream:
    """
    تقوم بإنشاء كائن البث بأعلى جودة ممكنة مع التحقق من المسار.
    """
    if not path or not isinstance(path, str):
        LOGGER(__name__).warning(f"تم اكتشاف مسار غير صالح: {path}")
        raise AssistantErr("مسار الملف غير صالح أو مفقود.")

    if video:
        LOGGER(__name__).info(f"تجهيز بث فيديو: {path}")
        return MediaStream(
            media_path=path,
            audio_parameters=AudioQuality.HIGH,  # جودة استوديو
            video_parameters=VideoQuality.HD_720p, # دقة عالية
            audio_flags=MediaStream.Flags.REQUIRED,
            video_flags=MediaStream.Flags.REQUIRED,
            ffmpeg_parameters=ffmpeg_params,
        )
    else:
        LOGGER(__name__).info(f"تجهيز بث صوتي: {path}")
        return MediaStream(
            media_path=path,
            audio_parameters=AudioQuality.HIGH,
            audio_flags=MediaStream.Flags.REQUIRED,
            video_flags=MediaStream.Flags.IGNORE, # توفير البيانات
            ffmpeg_parameters=ffmpeg_params,
        )

async def _clear_(chat_id: int) -> None:
    """تنظيف شامل لبيانات الشات من الذاكرة وقاعدة البيانات"""
    try:
        popped = db.pop(chat_id, None)
        if popped:
            await auto_clean(popped)
        
        # تنظيف القوائم
        if chat_id in db:
            del db[chat_id]
            
        # تحديث قاعدة البيانات
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        await set_loop(chat_id, 0)
        
        LOGGER(__name__).info(f"تم تنظيف بيانات الشات: {chat_id}")
    except Exception as e:
        LOGGER(__name__).error(f"خطأ أثناء تنظيف الشات {chat_id}: {e}")

# =======================================================================
# 🚀 وحدة التحكم المركزية (Call Controller Class)
# =======================================================================

class Call:
    def __init__(self):
        self.userbot1 = Client("BrandrdXAssis1", config.API_ID, config.API_HASH, session_string=config.STRING1) if config.STRING1 else None
        self.one = PyTgCalls(self.userbot1) if self.userbot1 else None

        self.userbot2 = Client("BrandrdXAssis2", config.API_ID, config.API_HASH, session_string=config.STRING2) if config.STRING2 else None
        self.two = PyTgCalls(self.userbot2) if self.userbot2 else None

        self.userbot3 = Client("BrandrdXAssis3", config.API_ID, config.API_HASH, session_string=config.STRING3) if config.STRING3 else None
        self.three = PyTgCalls(self.userbot3) if self.userbot3 else None

        self.userbot4 = Client("BrandrdXAssis4", config.API_ID, config.API_HASH, session_string=config.STRING4) if config.STRING4 else None
        self.four = PyTgCalls(self.userbot4) if self.userbot4 else None

        self.userbot5 = Client("BrandrdXAssis5", config.API_ID, config.API_HASH, session_string=config.STRING5) if config.STRING5 else None
        self.five = PyTgCalls(self.userbot5) if self.userbot5 else None

        self.active_calls: set[int] = set()
        LOGGER(__name__).info("✅ تم تهيئة وحدة الاتصال بنجاح.")

    # ---------------------------------------------------------
    # 🧠 الذكاء الاصطناعي للمساعدين (The Smart Resolver)
    # ---------------------------------------------------------
    async def get_call_engine(self, chat_id: int) -> PyTgCalls:
        """
        دالة ذكية تحدد أي مساعد (PyTgCalls Client) يجب استخدامه للشات الحالي.
        تقوم بتحويل كائن Pyrogram Client إلى كائن PyTgCalls Client تلقائياً.
        """
        try:
            # 1. الحصول على اليوزربوت المخصص لهذا الشات من قاعدة البيانات
            userbot = await group_assistant(self, chat_id)
            
            # 2. مطابقة اليوزربوت مع محرك الاتصال المناسب
            if userbot and self.userbot1 and userbot.me.id == self.userbot1.me.id: return self.one
            if userbot and self.userbot2 and userbot.me.id == self.userbot2.me.id: return self.two
            if userbot and self.userbot3 and userbot.me.id == self.userbot3.me.id: return self.three
            if userbot and self.userbot4 and userbot.me.id == self.userbot4.me.id: return self.four
            if userbot and self.userbot5 and userbot.me.id == self.userbot5.me.id: return self.five
            
            # 3. خطة بديلة: إذا فشل التحديد، نستخدم المساعد الأول
            LOGGER(__name__).warning(f"لم يتم العثور على تطابق للمساعد في {chat_id}، جاري استخدام المساعد الرئيسي.")
            return self.one
        except Exception as e:
            LOGGER(__name__).error(f"فشل في resolver المساعدين: {e}")
            return self.one

    # ---------------------------------------------------------
    # 🕹️ أوامر التحكم (Controls)
    # ---------------------------------------------------------
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
    async def stop_stream(self, chat_id: int) -> None:
        assistant = await self.get_call_engine(chat_id)
        await _clear_(chat_id)
        if chat_id not in self.active_calls:
            return
        try:
            await assistant.leave_call(chat_id)
        except Exception:
            pass
        finally:
            self.active_calls.discard(chat_id)

    @capture_internal_err
    async def force_stop_stream(self, chat_id: int) -> None:
        assistant = await self.get_call_engine(chat_id)
        try:
            check = db.get(chat_id)
            if check:
                check.pop(0)
        except (IndexError, KeyError):
            pass
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        await _clear_(chat_id)
        if chat_id not in self.active_calls:
            return
        try:
            await assistant.leave_call(chat_id)
        except Exception:
            pass
        finally:
            self.active_calls.discard(chat_id)

    @capture_internal_err
    async def skip_stream(self, chat_id: int, link: str, video: Union[bool, str] = None, image: Union[bool, str] = None) -> None:
        assistant = await self.get_call_engine(chat_id)
        stream = dynamic_media_stream(path=link, video=bool(video))
        await assistant.play(chat_id, stream)

    @capture_internal_err
    async def seek_stream(self, chat_id: int, file_path: str, to_seek: str, duration: str, mode: str) -> None:
        assistant = await self.get_call_engine(chat_id)
        ffmpeg_params = f"-ss {to_seek} -to {duration}"
        is_video = mode == "video"
        stream = dynamic_media_stream(path=file_path, video=is_video, ffmpeg_params=ffmpeg_params)
        await assistant.play(chat_id, stream)

    @capture_internal_err
    async def speedup_stream(self, chat_id: int, file_path: str, speed: float, playing: list) -> None:
        if not isinstance(playing, list) or not playing or not isinstance(playing[0], dict):
            raise AssistantErr("Invalid stream info for speedup.")

        assistant = await self.get_call_engine(chat_id)
        base = os.path.basename(file_path)
        chatdir = os.path.join(os.getcwd(), "playback", str(speed))
        os.makedirs(chatdir, exist_ok=True)
        out = os.path.join(chatdir, base)

        if not os.path.exists(out):
            vs = str(2.0 / float(speed))
            cmd = f'ffmpeg -i "{file_path}" -filter:v "setpts={vs}*PTS" -filter:a atempo={speed} -y "{out}"'
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdin=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

        dur = int(await asyncio.get_event_loop().run_in_executor(None, check_duration, out))
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration_min = seconds_to_min(dur)
        is_video = playing[0]["streamtype"] == "video"
        ffmpeg_params = f"-ss {played} -to {duration_min}"
        stream = dynamic_media_stream(path=out, video=is_video, ffmpeg_params=ffmpeg_params)

        if chat_id in db and db[chat_id] and db[chat_id][0].get("file") == file_path:
            await assistant.play(chat_id, stream)
            db[chat_id][0].update({
                "played": con_seconds,
                "dur": duration_min,
                "seconds": dur,
                "speed_path": out,
                "speed": speed,
                "old_dur": db[chat_id][0].get("dur"),
                "old_second": db[chat_id][0].get("seconds"),
            })

    # ---------------------------------------------------------
    # 🔗 الانضمام الآمن للمكالمة (Safe Join Logic)
    # ---------------------------------------------------------
    @capture_internal_err
    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link: str,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ) -> None:
        """
        منطق الانضمام المحصن:
        1. يحدد المحرك الصحيح.
        2. يتحقق من صحة الرابط.
        3. يعالج جميع استثناءات الاتصال المعروفة.
        """
        # جلب المساعد الصحيح
        assistant = await self.get_call_engine(chat_id)
        
        # جلب ملف اللغة
        lang = await get_lang(chat_id)
        _ = get_string(lang)
        
        # التحقق من الرابط
        if not link:
            raise AssistantErr("رابط التشغيل غير صالح أو فارغ. (Empty URL)")

        # تجهيز البث
        stream = dynamic_media_stream(path=link, video=bool(video))

        try:
            # محاولة التشغيل الأساسية
            await assistant.play(chat_id, stream)
            
        except (NoActiveGroupCall, ChatAdminRequired):
            raise AssistantErr(_["call_8"]) # يجب فتح الكول أولاً
        except NoAudioSourceFound:
            raise AssistantErr(_["call_11"])
        except NoVideoSourceFound:
            raise AssistantErr(_["call_12"])
        except (ConnectionNotFound, TelegramServerError):
            raise AssistantErr(_["call_10"]) # مشكلة سيرفر
        except NotConnected:
            raise AssistantErr(_["call_8"])
        except AlreadyJoinedError:
            # إذا كان منضماً بالفعل، لا بأس، فقط نحدث التراك
            pass 
        except Exception as e:
            # معالجة الخطأ الشهير "Client has no attribute play"
            if "has no attribute 'play'" in str(e):
                LOGGER(__name__).warning("اكتشاف عدم تطابق الكلاينت، جاري التصحيح التلقائي...")
                try:
                    # المحاولة الأخيرة باستخدام الكلاينت رقم 1 كحل جذري
                    await self.one.play(chat_id, stream)
                except Exception as final_e:
                    raise AssistantErr(f"فشل الانضمام بعد التصحيح: {final_e}")
            else:
                raise AssistantErr(f"فشل الانضمام للمكالمة.\nالسبب: {e}")
        
        # تحديث حالة المكالمات النشطة
        self.active_calls.add(chat_id)
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video:
            await add_active_video_chat(chat_id)

        # إعداد المؤقت للإغلاق التلقائي إذا كان المساعد وحيداً
        if await is_autoend():
            counter[chat_id] = {}
            try:
                users = len(await assistant.get_participants(chat_id))
                if users == 1:
                    autoend[chat_id] = datetime.now() + timedelta(minutes=1)
            except: pass

    # ---------------------------------------------------------
    # 🎧 مشغل الوسائط المتكامل (The Core Player)
    # ---------------------------------------------------------
    @capture_internal_err
    async def play(self, client, chat_id: int) -> None:
        """
        المحرك الرئيسي لتشغيل وإدارة قائمة الانتظار.
        يتعامل مع جميع أنواع المصادر: Live, File, YouTube, SoundCloud, Telegram Audio/Video.
        """
        # التأكد من صحة العميل المرر (Client Validation)
        if isinstance(client, Client): 
             # إذا تم تمرير يوزربوت بدلاً من PyTgCalls، قم بتبديله
             LOGGER(__name__).info(f"تصحيح نوع العميل للشات {chat_id}")
             client = await self.get_call_engine(chat_id)

        check = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)
        
        try:
            if loop == 0:
                popped = check.pop(0)
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)
            await auto_clean(popped)
            
            if not check:
                await _clear_(chat_id)
                if chat_id in self.active_calls:
                    try:
                        await client.leave_call(chat_id)
                    except: pass
                    finally:
                        self.active_calls.discard(chat_id)
                return
        except:
            try:
                await _clear_(chat_id)
                return await client.leave_call(chat_id)
            except: return

        # استخراج بيانات المسار التالي
        queued = check[0]["file"]
        language = await get_lang(chat_id)
        _ = get_string(language)
        title = (check[0]["title"]).title()
        user = check[0]["by"]
        original_chat_id = check[0]["chat_id"]
        streamtype = check[0]["streamtype"]
        videoid = check[0]["vidid"]
        db[chat_id][0]["played"] = 0

        exis = (check[0]).get("old_dur")
        if exis:
            db[chat_id][0]["dur"] = exis
            db[chat_id][0]["seconds"] = check[0]["old_second"]
            db[chat_id][0]["speed_path"] = None
            db[chat_id][0]["speed"] = 1.0

        video = True if str(streamtype) == "video" else False

        # --- معالجة أنواع الميديا المختلفة ---

        # 1. بث مباشر (Live Stream)
        if "live_" in queued:
            n, link = await YouTube.video(videoid, True)
            if n == 0:
                return await app.send_message(original_chat_id, text=_["call_6"])
            stream = dynamic_media_stream(path=link, video=video)
            try:
                await client.play(chat_id, stream)
            except Exception as e:
                LOGGER(__name__).error(f"Live Play Error: {e}")
                return await app.send_message(original_chat_id, text=_["call_6"])
            
            img = await get_thumb(videoid)
            button = stream_markup(_, videoid, chat_id)
            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=img,
                caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{videoid}", title[:23], check[0]["dur"], user),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

        # 2. ملفات تم تحميلها (Downloaded Files)
        elif "vid_" in queued:
            mystic = await app.send_message(original_chat_id, _["call_7"])
            try:
                file_path, _ = await YouTube.download(
                    videoid,
                    mystic,
                    videoid=True,
                    video=True if str(streamtype) == "video" else False,
                )
            except Exception as e:
                LOGGER(__name__).error(f"Download Error: {e}")
                return await mystic.edit_text(_["call_6"], disable_web_page_preview=True)
            
            stream = dynamic_media_stream(path=file_path, video=video)
            try:
                await client.play(chat_id, stream)
            except Exception as e:
                LOGGER(__name__).error(f"Play File Error: {e}")
                return await app.send_message(original_chat_id, text=_["call_6"])
            
            img = await get_thumb(videoid)
            button = stream_markup(_, videoid, chat_id)
            await mystic.delete()
            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=img,
                caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{videoid}", title[:23], check[0]["dur"], user),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"

        # 3. مصادر أخرى (Telegram / SoundCloud / Index)
        else:
            stream = dynamic_media_stream(path=queued, video=video)
            try:
                await client.play(chat_id, stream)
            except Exception as e:
                LOGGER(__name__).error(f"Other Source Play Error: {e}")
                return await app.send_message(original_chat_id, text=_["call_6"])
            
            if videoid == "telegram":
                button = stream_markup(_, "telegram", chat_id)
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=config.TELEGRAM_VIDEO_URL if video else config.TELEGRAM_AUDIO_URL,
                    caption=_["stream_1"].format(config.SUPPORT_CHAT, title[:23], check[0]["dur"], user),
                    reply_markup=InlineKeyboardMarkup(button),
                )
            elif videoid == "soundcloud":
                button = stream_markup(_, "soundcloud", chat_id)
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=config.SOUNCLOUD_IMG_URL,
                    caption=_["stream_1"].format(config.SUPPORT_CHAT, title[:23], check[0]["dur"], user),
                    reply_markup=InlineKeyboardMarkup(button),
                )
            else:
                img = await get_thumb(videoid)
                button = stream_markup(_, videoid, chat_id)
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{videoid}", title[:23], check[0]["dur"], user),
                    reply_markup=InlineKeyboardMarkup(button),
                )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

    # ---------------------------------------------------------
    # 📡 التشغيل والمراقبة (Startup & Monitoring)
    # ---------------------------------------------------------
    async def start(self) -> None:
        LOGGER(__name__).info("جاري تشغيل عملاء PyTgCalls...")
        clients = [self.one, self.two, self.three, self.four, self.five]
        for i, cli in enumerate(clients, 1):
            if cli: 
                await cli.start()
                LOGGER(__name__).info(f"تم تشغيل المساعد رقم {i} بنجاح.")

    @capture_internal_err
    async def ping(self) -> str:
        """قياس زمن الاستجابة لجميع المساعدين"""
        pings = []
        clients = [self.one, self.two, self.three, self.four, self.five]
        for cli in clients:
            if cli and cli.ping:
                pings.append(cli.ping)
        return str(round(sum(pings) / len(pings), 3)) if pings else "0.0"

    @capture_internal_err
    async def decorators(self) -> None:
        """إعداد معالجات الأحداث (Event Handlers) لجميع المساعدين"""
        assistants = list(filter(None, [self.one, self.two, self.three, self.four, self.five]))

        async def unified_update_handler(client, update: Update) -> None:
            # 1. عند انتهاء البث (تشغيل التالي)
            if isinstance(update, StreamEnded):
                if update.stream_type == StreamEnded.Type.AUDIO:
                    LOGGER(__name__).info(f"انتهاء البث في {update.chat_id}، تشغيل التالي...")
                    # استخدام get_call_engine لضمان الكلاينت الصحيح دائماً
                    assistant = await self.get_call_engine(update.chat_id)
                    await self.play(assistant, update.chat_id)
            
            # 2. تحديثات حالة المكالمة (طرد/خروج)
            elif isinstance(update, ChatUpdate):
                status = update.status
                if status in [ChatUpdate.Status.KICKED, ChatUpdate.Status.LEFT_GROUP, ChatUpdate.Status.CLOSED_VOICE_CHAT]:
                    LOGGER(__name__).warning(f"توقف قسري للمكالمة في {update.chat_id} (Status: {status})")
                    await self.stop_stream(update.chat_id)

        # ربط المعالج الموحد بجميع المساعدين
        for assistant in assistants:
            assistant.on_update()(unified_update_handler)

# تهيئة الكائن الرئيسي
Hotty = Call()
