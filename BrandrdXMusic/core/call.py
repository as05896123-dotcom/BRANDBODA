# BrandrdXMusic/core/call.py
import asyncio
import os
import random
import contextlib
from datetime import datetime, timedelta
from typing import Union, Optional

from pyrogram import Client
from pyrogram.raw import functions as raw_functions
from pyrogram.errors import ChatAdminRequired, UserAlreadyParticipant
from pyrogram.types import InlineKeyboardMarkup

from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality, ChatUpdate, StreamEnded, Update
from pytgcalls.exceptions import NoActiveGroupCall

import config
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
    from strings import get_string
except Exception:
    def get_string(lang: str):
        return {"call_6": "حدث خطأ أثناء التشغيل.", "call_7": "جاري المعالجة...", "call_8": "لا يوجد مكالمة نشطة.", "call_10": "خطأ من خوادم تيليجرام", "stream_1": "{}"}

try:
    from BrandrdXMusic.utils.inline.play import stream_markup2
except Exception:
    stream_markup2 = None

autoend = {}
counter = {}
AUTO_END_TIME = 1


def dynamic_media_stream(path: str, video: bool = False, ffmpeg_params: Optional[str] = None) -> MediaStream:
    """إنشاء MediaStream جديد للـ pytgcalls مع إعدادات افتراضية مرنة."""
    return MediaStream(
        media_path=path,
        audio_parameters=AudioQuality.HIGH,
        video_parameters=VideoQuality.SD_480p if video else None,
        ffmpeg_parameters=ffmpeg_params,
        video_flags=MediaStream.Flags.REQUIRED if video else MediaStream.Flags.IGNORE,
    )


async def _clear_(chat_id: int) -> None:
    """تنظيف حالة الدردشة وإزالة بيانات التشغيل."""
    try:
        popped = db.pop(chat_id, None)
        if popped:
            await auto_clean(popped)
    except Exception:
        pass
    try:
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        await set_loop(chat_id, 0)
    except Exception:
        pass


class Call:
    def __init__(self):
        # init pyrogram userbots (if session strings موجودة)
        self.userbot1 = Client("BrandrdXMusic1", config.API_ID, config.API_HASH, session_string=config.STRING1) if getattr(config, "STRING1", None) else None
        self.one = PyTgCalls(self.userbot1) if self.userbot1 else None

        self.userbot2 = Client("BrandrdXMusic2", config.API_ID, config.API_HASH, session_string=config.STRING2) if getattr(config, "STRING2", None) else None
        self.two = PyTgCalls(self.userbot2) if self.userbot2 else None

        self.userbot3 = Client("BrandrdXMusic3", config.API_ID, config.API_HASH, session_string=config.STRING3) if getattr(config, "STRING3", None) else None
        self.three = PyTgCalls(self.userbot3) if self.userbot3 else None

        self.userbot4 = Client("BrandrdXMusic4", config.API_ID, config.API_HASH, session_string=config.STRING4) if getattr(config, "STRING4", None) else None
        self.four = PyTgCalls(self.userbot4) if self.userbot4 else None

        self.userbot5 = Client("BrandrdXMusic5", config.API_ID, config.API_HASH, session_string=config.STRING5) if getattr(config, "STRING5", None) else None
        self.five = PyTgCalls(self.userbot5) if self.userbot5 else None

        # قائمة المساعدين (Pyrogram clients) والـ PyTgCalls المناظرة
        self._userbots = [self.userbot1, self.userbot2, self.userbot3, self.userbot4, self.userbot5]
        self._pytg_instances = [self.one, self.two, self.three, self.four, self.five]

        # مجموعة لمراقبة الـ chats النشطة حتى لا نكرر العمليات
        self.active_calls = set()

    async def _find_pytgcalls_for_assistant(self, assistant_client: Client):
        """
        نحاول إيجاد PyTgCalls instance المطابق لكائن pyrogram assistant الذي رجعته group_assistant().
        fallback: نرجع أول instance موجود.
        """
        try:
            for ub, pt in zip(self._userbots, self._pytg_instances):
                if ub is None or pt is None:
                    continue
                # المقارنة تكون بالمساواة أو حسب username/session_name إن وُجد
                try:
                    if assistant_client is ub:
                        return pt
                    # المقارنة حسب session_name أو name إذا وُجدت
                    if hasattr(assistant_client, "session_name") and hasattr(ub, "session_name") and getattr(assistant_client, "session_name", None) == getattr(ub, "session_name", None):
                        return pt
                except Exception:
                    pass
            # fallback: أول instance صالح
            for pt in self._pytg_instances:
                if pt:
                    return pt
        except Exception:
            pass
        return None

    async def get_tgcalls(self, chat_id: int):
        """الحصول على كائن PyTgCalls الملائم لهذه الدردشة - يحاول استخدام group_assistant أولاً."""
        try:
            assistant_client = await group_assistant(self, chat_id)
        except Exception:
            assistant_client = None
        # إذا حصلنا على assistant_client جرب نلاقي الـ pytgcalls المناسب
        pt = await self._find_pytgcalls_for_assistant(assistant_client)
        # إذا ما لقيناش حاجة ارجع أول instance موجود
        if pt:
            return pt
        for inst in self._pytg_instances:
            if inst:
                return inst
        raise RuntimeError("No PyTgCalls instance available")

    # ---- Wrappers للتعامل الآمن مع طرق تشغيل/تغيير البث ----
    async def _safe_play(self, tgcalls, chat_id: int, stream: MediaStream, assistant_client: Optional[Client] = None, create_if_missing: bool = True):
        """
        تنفيذ تشغيل بث مع محاولة استعمال الدوال المختلفة المتاحة في إصدارات pytgcalls
        يحاول: play -> change_stream -> join_group_call
        وفي حالة NoActiveGroupCall يحاول إنشاء كول جديد عبر assistant_client (pyrogram).
        """
        try:
            # 1) حاول play إن متاح
            if hasattr(tgcalls, "play"):
                await tgcalls.play(chat_id, stream)
                return True
            # 2) حاول change_stream
            if hasattr(tgcalls, "change_stream"):
                await tgcalls.change_stream(chat_id, stream)
                return True
            # 3) حاول join_group_call / join_call
            if hasattr(tgcalls, "join_group_call"):
                await tgcalls.join_group_call(chat_id, stream)
                return True
            if hasattr(tgcalls, "join_call"):
                await tgcalls.join_call(chat_id, stream)
                return True
            # لا توجد دوال معروفة - خطأ
            raise RuntimeError("No playable method on PyTgCalls instance")
        except NoActiveGroupCall:
            # لو مفيش مكالمة، جرب إنشاء واحدة عبر assistant_client
            if not create_if_missing or assistant_client is None:
                raise
            try:
                peer = await assistant_client.resolve_peer(chat_id)
                random_id = random.getrandbits(32)
                await assistant_client.send(raw_functions.phone.CreateGroupCall(peer=peer, random_id=random_id))
                await asyncio.sleep(1.2)
                # محاولة ثانية بدون إنشاء
                return await self._safe_play(tgcalls, chat_id, stream, assistant_client, create_if_missing=False)
            except Exception as e:
                LOGGER(__name__).error(f"Failed to create group call for {chat_id}: {e}")
                raise AssistantErr(await self._get_localized(chat_id, "call_8"))
        except Exception as e:
            LOGGER(__name__).error(f"_safe_play error on chat {chat_id}: {e}")
            raise

    async def _safe_leave(self, tgcalls, chat_id: int, assistant_client: Optional[Client] = None):
        """
        طُرق مغادرة المكالمة مع توافقيات للإصدارات المختلفة:
        leave_call, leave_group_call, leave
        """
        try:
            if hasattr(tgcalls, "leave_call"):
                await tgcalls.leave_call(chat_id)
                return
            if hasattr(tgcalls, "leave_group_call"):
                await tgcalls.leave_group_call(chat_id)
                return
            if hasattr(tgcalls, "leave"):
                await tgcalls.leave(chat_id)
                return
            # إذا لم توجد دوال، حاول استخدام pyrogram assistant لترك المكالمة
            if assistant_client:
                with contextlib.suppress(Exception):
                    # بعض النسخ تسمح بـ raw.leave chat - لكن عادة ترك المكالمة يتم عبر pytgcalls
                    await assistant_client.send(raw_functions.phone.DiscardGroupCall(group_call=chat_id, duration=0))
        except Exception as e:
            LOGGER(__name__).warning(f"_safe_leave warning for {chat_id}: {e}")

    async def _get_localized(self, chat_id: int, key: str):
        try:
            lang = await get_lang(chat_id)
            strings = get_string(lang)
            return strings.get(key, key)
        except Exception:
            # fallback english/arabic short msg
            fallback = {
                "call_6": "Unable to play the track.",
                "call_7": "Processing...",
                "call_8": "Please start a voice chat first.",
                "call_10": "Telegram server error.",
            }
            return fallback.get(key, key)

    # ---- واجهات تشغيل / تحكم ----
    async def pause_stream(self, chat_id: int):
        try:
            tgcalls = await self.get_tgcalls(chat_id)
            # قد تكون الدالة pause موجودة في PyTgCalls أو على assistant (pyrogram)
            if hasattr(tgcalls, "pause"):
                await tgcalls.pause(chat_id)
            else:
                # محاولة عبر play/override APIs غير ممكنة، فنسجل فقط
                LOGGER(__name__).info(f"Pause not supported on instance for {chat_id}")
        except Exception:
            pass

    async def resume_stream(self, chat_id: int):
        try:
            tgcalls = await self.get_tgcalls(chat_id)
            if hasattr(tgcalls, "resume"):
                await tgcalls.resume(chat_id)
            else:
                LOGGER(__name__).info(f"Resume not supported on instance for {chat_id}")
        except Exception:
            pass

    async def mute_stream(self, chat_id: int):
        try:
            tgcalls = await self.get_tgcalls(chat_id)
            if hasattr(tgcalls, "mute"):
                await tgcalls.mute(chat_id)
            else:
                LOGGER(__name__).info(f"Mute not supported on instance for {chat_id}")
        except Exception:
            pass

    async def unmute_stream(self, chat_id: int):
        try:
            tgcalls = await self.get_tgcalls(chat_id)
            if hasattr(tgcalls, "unmute"):
                await tgcalls.unmute(chat_id)
            else:
                LOGGER(__name__).info(f"Unmute not supported on instance for {chat_id}")
        except Exception:
            pass

    async def stop_stream(self, chat_id: int):
        """إيقاف البث بأمان ومغادرة المكالمة."""
        try:
            tgcalls = await self.get_tgcalls(chat_id)
            # حاول تنظيف الحالة المحلية أولاً
            await _clear_(chat_id)
            # لو حصلت على assistant client أيضًا حاول ترك المكالمة عبر الpyrogram assistant
            try:
                assistant_client = await group_assistant(self, chat_id)
            except Exception:
                assistant_client = None
            await self._safe_leave(tgcalls, chat_id, assistant_client)
        except Exception as e:
            LOGGER(__name__).warning(f"stop_stream warning: {e}")
        finally:
            self.active_calls.discard(chat_id)

    async def force_stop_stream(self, chat_id: int):
        """فرض إنهاء البث وتنظيف الطابور."""
        try:
            tgcalls = await self.get_tgcalls(chat_id)
            try:
                if queue := db.get(chat_id):
                    queue.pop(0)
            except Exception:
                pass
            await remove_active_video_chat(chat_id)
            await remove_active_chat(chat_id)
            await _clear_(chat_id)
            assistant_client = None
            try:
                assistant_client = await group_assistant(self, chat_id)
            except Exception:
                pass
            await self._safe_leave(tgcalls, chat_id, assistant_client)
        except Exception as e:
            LOGGER(__name__).warning(f"force_stop_stream warning: {e}")
        finally:
            self.active_calls.discard(chat_id)

    async def skip_stream(self, chat_id: int, link: str, video: Union[bool, str] = None, image: Union[bool, str] = None):
        """تخطي المسار الحالي وتشغيل الرابط / الملف الجديد بشكل آمن."""
        try:
            tgcalls = await self.get_tgcalls(chat_id)
            assistant_client = None
            try:
                assistant_client = await group_assistant(self, chat_id)
            except Exception:
                pass
            path = link if isinstance(link, str) and link.startswith("http") else os.path.abspath(link)
            stream = dynamic_media_stream(path, bool(video))
            await self._safe_play(tgcalls, chat_id, stream, assistant_client)
        except Exception as e:
            LOGGER(__name__).error(f"skip_stream error: {e}")

    async def seek_stream(self, chat_id: int, file_path: str, to_seek: str, duration: str, mode):
        """Seek داخل المسار عن طريق تشغيل ffmpeg باختيارات -ss -to."""
        try:
            tgcalls = await self.get_tgcalls(chat_id)
            assistant_client = None
            try:
                assistant_client = await group_assistant(self, chat_id)
            except Exception:
                pass
            ffmpeg_params = f"-ss {to_seek} -to {duration}"
            file_path = os.path.abspath(file_path)
            stream = dynamic_media_stream(file_path, mode == "video", ffmpeg_params)
            await self._safe_play(tgcalls, chat_id, stream, assistant_client)
        except Exception as e:
            LOGGER(__name__).error(f"seek_stream error: {e}")

    async def speedup_stream(self, chat_id: int, file_path: str, speed: float, playing: list):
        """تغيير سرعة التشغيل عبر إعادة ترميز مؤقتة وبدء البث على الملف الجديد."""
        try:
            tgcalls = await self.get_tgcalls(chat_id)
            assistant_client = None
            try:
                assistant_client = await group_assistant(self, chat_id)
            except Exception:
                pass

            file_path = os.path.abspath(file_path)
            base = os.path.basename(file_path)
            chatdir = os.path.join(os.getcwd(), "playback", str(speed))
            os.makedirs(chatdir, exist_ok=True)
            out = os.path.join(chatdir, base)

            if not os.path.exists(out):
                # حساب معقول لقيمة setpts / atempo
                vs = str(2.0 / float(speed)) if float(speed) != 0 else "1.0"
                cmd = f'ffmpeg -i "{file_path}" -filter:v "setpts={vs}*PTS" -filter:a atempo={speed} -y "{out}"'
                proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                await proc.communicate()

            dur = int(await asyncio.get_event_loop().run_in_executor(None, check_duration, out))
            played, con_seconds = speed_converter(playing[0]["played"], speed)
            duration_min = seconds_to_min(dur)
            ffmpeg_params = f"-ss {played} -to {duration_min}"
            video_flag = (playing[0]["streamtype"] == "video")
            stream = dynamic_media_stream(out, video_flag, ffmpeg_params)

            # تحقق من تطابق المسار قبل تبديل البث
            if chat_id in db and db[chat_id] and db[chat_id][0].get("file") == file_path:
                await self._safe_play(tgcalls, chat_id, stream, assistant_client)
                db[chat_id][0].update({
                    "played": con_seconds,
                    "dur": duration_min,
                    "seconds": dur,
                    "speed_path": out,
                    "speed": speed
                })
            else:
                raise AssistantErr("Stream mismatch during speedup.")
        except Exception as e:
            LOGGER(__name__).error(f"speedup_stream error: {e}")
            raise

    async def join_call(self, chat_id: int, original_chat_id: int, link, video: Union[bool, str] = None, image: Union[bool, str] = None):
        """
        انضمام ذكي للمكالمة: يحاول التشغيل مباشرة، وإذا لم توجد مكالمة ينشئها ثم يعيد المحاولة.
        يستخدم _safe_play الذي يتعامل مع اختلافات نسخ pytgcalls.
        """
        tgcalls = await self.get_tgcalls(chat_id)
        try:
            assistant_client = await group_assistant(self, chat_id)
        except Exception:
            assistant_client = None

        lang = ""
        try:
            lang = await get_lang(chat_id)
        except Exception:
            lang = None
        _ = get_string(lang) if lang else get_string("en")

        # تأكد من مسار صحيح
        if not isinstance(link, str):
            link = str(link)
        if not link.startswith("http"):
            link = os.path.abspath(link)

        # إعداد Stream
        stream = dynamic_media_stream(link, bool(video))
        try:
            await self._safe_play(tgcalls, chat_id, stream, assistant_client)
        except AssistantErr as ae:
            raise ae
        except NoActiveGroupCall:
            # _safe_play يحاول إنشاء المكالمة، لذا هنا نعتبر رسالة خطأ عامة
            raise AssistantErr(_["call_8"])
        except ChatAdminRequired:
            raise AssistantErr(_["call_8"])
        except Exception as e:
            LOGGER(__name__).error(f"join_call unknown error: {e}")
            raise AssistantErr(_["call_8"])

        # علامة أن المحادثة تعمل
        self.active_calls.add(chat_id)
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video:
            await add_active_video_chat(chat_id)

        # autoend logic
        try:
            if await is_autoend():
                try:
                    members = 0
                    if assistant_client:
                        members = await assistant_client.get_chat_members_count(chat_id)
                    if members <= 1:
                        autoend[chat_id] = datetime.now() + timedelta(minutes=AUTO_END_TIME)
                except Exception:
                    pass
        except Exception:
            pass

    async def change_stream(self, client, chat_id: int):
        """
        عند انتهاء دفق ننتقل للتراك التالي. client هو PyTgCalls instance الذي تلقاه مع الحدث.
        """
        try:
            queue = db.get(chat_id)
            if not queue:
                await _clear_(chat_id)
                try:
                    await self._safe_leave(client, chat_id, await group_assistant(self, chat_id))
                except Exception:
                    pass
                return

            popped = None
            loop = await get_loop(chat_id)
            if loop == 0:
                try:
                    popped = queue.pop(0)
                except Exception:
                    popped = None
            else:
                loop -= 1
                await set_loop(chat_id, loop)
            if popped:
                # تنظيف العنصر القديم
                with contextlib.suppress(Exception):
                    await auto_clean(popped)

            if not queue:
                await _clear_(chat_id)
                with contextlib.suppress(Exception):
                    await self._safe_leave(client, chat_id, await group_assistant(self, chat_id))
                self.active_calls.discard(chat_id)
                return

            # الآن نعالج العنصر التالي في الطابور
            queued = queue[0]["file"]
            lang = await get_lang(chat_id)
            _ = get_string(lang)
            title = (queue[0].get("title") or "").title()
            user = queue[0].get("by")
            original_chat_id = queue[0].get("chat_id")
            streamtype = queue[0].get("streamtype")
            videoid = queue[0].get("vidid")
            queue[0]["played"] = 0
            # معالجة سرعات سابقة
            if old := queue[0].get("old_dur"):
                queue[0]["dur"] = old
                queue[0]["seconds"] = queue[0].get("old_second", queue[0].get("seconds"))

            is_video = str(streamtype) == "video"

            # التعامل مع أنواع متعددة للمسارات
            if isinstance(queued, str) and queued.startswith("live_"):
                try:
                    n, link = await YouTube.video(videoid, True)
                    if n == 0:
                        return await app.send_message(original_chat_id, _["call_6"])
                    stream = dynamic_media_stream(link, is_video)
                    await self._safe_play(client, chat_id, stream, await group_assistant(self, chat_id))
                except Exception:
                    return await app.send_message(original_chat_id, _["call_6"])
                img = await get_thumb(videoid)
                btn = stream_markup2(_, chat_id) if stream_markup2 else stream_markup(_, videoid, chat_id)
                run = await app.send_photo(chat_id=original_chat_id, photo=img,
                                           caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{videoid}", title[:23], queue[0].get("dur", ""), user),
                                           reply_markup=InlineKeyboardMarkup(btn))
                queue[0]["mystic"] = run
                queue[0]["markup"] = "tg"

            elif isinstance(queued, str) and queued.startswith("vid_"):
                mystic = await app.send_message(original_chat_id, _["call_7"])
                try:
                    file_path, _ = await YouTube.download(videoid, mystic, videoid=True, video=is_video)
                except Exception:
                    return await mystic.edit_text(_["call_6"], disable_web_page_preview=True)
                stream = dynamic_media_stream(file_path, is_video)
                try:
                    await self._safe_play(client, chat_id, stream, await group_assistant(self, chat_id))
                except Exception:
                    return await app.send_message(original_chat_id, _["call_6"])
                img = await get_thumb(videoid)
                await mystic.delete()
                btn = stream_markup(_, videoid, chat_id)
                run = await app.send_photo(chat_id=original_chat_id, photo=img,
                                           caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{videoid}", title[:23], queue[0].get("dur", ""), user),
                                           reply_markup=InlineKeyboardMarkup(btn))
                queue[0]["mystic"] = run
                queue[0]["markup"] = "stream"

            else:
                # مسار عادي (ملف/رابط)
                stream = dynamic_media_stream(queued, is_video)
                try:
                    await self._safe_play(client, chat_id, stream, await group_assistant(self, chat_id))
                except Exception:
                    return await app.send_message(original_chat_id, _["call_6"])
                # إرسال صورة / وصف للمستخدم
                if videoid in ("telegram", "soundcloud"):
                    btn = stream_markup2(_, chat_id) if stream_markup2 else stream_markup(_, videoid, chat_id)
                    img = config.TELEGRAM_AUDIO_URL if str(streamtype) == "audio" else config.TELEGRAM_VIDEO_URL
                    run = await app.send_photo(chat_id=original_chat_id, photo=img,
                                               caption=_["stream_1"].format(config.SUPPORT_CHAT, title[:23], queue[0].get("dur", ""), user),
                                               reply_markup=InlineKeyboardMarkup(btn))
                    queue[0]["mystic"] = run
                    queue[0]["markup"] = "tg"
                else:
                    img = await get_thumb(videoid)
                    btn = stream_markup(_, videoid, chat_id)
                    try:
                        run = await app.send_photo(chat_id=original_chat_id, photo=img,
                                                   caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{videoid}", title[:23], queue[0].get("dur", ""), user),
                                                   reply_markup=InlineKeyboardMarkup(btn))
                    except Exception:
                        run = None
                    queue[0]["mystic"] = run
                    queue[0]["markup"] = "stream"

        except Exception as e:
            LOGGER(__name__).error(f"change_stream error: {e}")
            # محاولة احتياطية: لو فشل التغيير حاول تنظيف وترك المكالمة
            try:
                await _clear_(chat_id)
                await self.stop_stream(chat_id)
            except Exception:
                pass

    async def ping(self):
        """حساب متوسط ping عبر كل المساعدين المتصلين."""
        pings = []
        for inst in self._pytg_instances:
            if inst:
                try:
                    pings.append(inst.ping)
                except Exception:
                    pass
        try:
            return str(round(sum(pings) / len(pings), 3)) if pings else "0.0"
        except Exception:
            return "0.0"

    async def start(self):
        """Start all pytgcalls instances and register decorators."""
        LOGGER(__name__).info("Starting PyTgCalls clients...")
        tasks = []
        for inst in self._pytg_instances:
            if inst:
                try:
                    tasks.append(inst.start())
                except Exception as e:
                    LOGGER(__name__).warning(f"Failed to start one PyTgCalls instance: {e}")
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        await self.decorators()

    async def decorators(self):
        """
        ربط معالج موحد لتحديثات ChatUpdate و StreamEnded.
        نستخدم on_update() لكل instance ونتعامل مع اختلافات update object.
        """
        async def unified_update_handler(client, update: Update):
            # استخرج chat_id بشكل آمن
            chat_id = getattr(update, "chat_id", None)
            if not chat_id:
                chat_obj = getattr(update, "chat", None)
                if chat_obj:
                    chat_id = getattr(chat_obj, "id", None)
            if not chat_id:
                return

            try:
                # StreamEnded قد يكون من نوع StreamEnded أو Update تبع المكتبة
                if isinstance(update, StreamEnded):
                    # نتأكد انها صوتية فقط قبل التبديل
                    try:
                        if update.stream_type == StreamEnded.Type.AUDIO:
                            await self.change_stream(client, chat_id)
                    except Exception:
                        # في بعض الإصدارات شكل Update مختلف؛ نجرب التعامل العام
                        await self.change_stream(client, chat_id)
                elif isinstance(update, ChatUpdate):
                    status = update.status
                    # تحقق من حالات LEFT / KICKED / CLOSED_VOICE_CHAT
                    if (status == ChatUpdate.Status.LEFT_CALL) or (status == ChatUpdate.Status.CLOSED_VOICE_CHAT) or (status == ChatUpdate.Status.KICKED):
                        await self.stop_stream(chat_id)
                else:
                    # بعض نسخ pytgcalls ترسل أنواع أخرى من Update؛ نتعامل بحذر
                    # لو الكائن يحتوي على attr stream_type أو status نتعالجو نفسياً
                    if hasattr(update, "stream_type"):
                        with contextlib.suppress(Exception):
                            await self.change_stream(client, chat_id)
                    elif hasattr(update, "status"):
                        with contextlib.suppress(Exception):
                            await self.stop_stream(chat_id)
            except Exception as e:
                LOGGER(__name__).error(f"unified_update_handler exception for chat {chat_id}: {e}")

        # سجل المعالج على كل instance متاحة
        for inst in self._pytg_instances:
            if inst:
                try:
                    inst.on_update()(unified_update_handler)
                except Exception as e:
                    LOGGER(__name__).warning(f"Failed to attach on_update handler: {e}")


# instance جاهز للاستخدام
Hotty = Call()
