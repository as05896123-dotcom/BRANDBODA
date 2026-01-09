import asyncio
import os
import gc
import sys
from datetime import datetime, timedelta
from typing import Union, List, Dict, Any

from pyrogram import Client
from pyrogram.errors import FloodWait, ChatAdminRequired, UserAlreadyParticipant, InviteHashExpired
from pyrogram.types import InlineKeyboardMarkup

# ============================================================
# 🛡️ IMPORT SAFETY (تأكد من وجود المكتبات)
# ============================================================
try:
    from pytgcalls import PyTgCalls
    from pytgcalls.types import (
        MediaStream, AudioQuality, VideoQuality,
        StreamEnded, ChatUpdate, Update
    )
    from pytgcalls.exceptions import (
        NoActiveGroupCall, NoAudioSourceFound, NoVideoSourceFound
    )
except ImportError as e:
    print(f"CRITICAL ERROR: PyTgCalls import failed! {e}")
    sys.exit()

import config
from strings import get_string
from BrandrdXMusic import LOGGER, YouTube, app
from BrandrdXMusic.misc import db
from BrandrdXMusic.utils.database import (
    add_active_chat, add_active_video_chat, get_lang, get_loop,
    group_assistant, is_autoend, music_on, remove_active_chat,
    remove_active_video_chat, set_loop,
)
from BrandrdXMusic.utils.exceptions import AssistantErr
from BrandrdXMusic.utils.formatters import check_duration, seconds_to_min, speed_converter
from BrandrdXMusic.utils.stream.autoclear import auto_clean
from BrandrdXMusic.utils.thumbnails import get_thumb
from BrandrdXMusic.utils.inline.play import stream_markup

try:
    from BrandrdXMusic.utils.inline.play import stream_markup2
except ImportError:
    stream_markup2 = None

autoend = {}
counter = {}

# =======================================================================
# 🛠️ FFMPEG SETTINGS (إعدادات الصوت والصورة الكاملة)
# =======================================================================

def build_stream(path: str, video: bool = False, live: bool = False, ffmpeg_flags: str = "") -> MediaStream:
    if not path: raise ValueError("Path is empty")
    
    # تحويل المسار لمسار كامل لو ملف محلي
    if not path.startswith("http"):
        path = os.path.abspath(path)

    # إعدادات FFMPEG الأساسية للصوت العالي والنقي
    # volume=1.5: يرفع الصوت 150%
    audio_args = "-filter:a volume=1.5"
    
    # إعدادات الفيديو (سرعة قصوى لتقليل التقطيع)
    video_args = "-filter:a volume=1.5 -preset ultrafast -tune zerolatency"
    
    # إعدادات الشبكة (للروابط فقط)
    network_args = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"

    final_args = audio_args if not video else video_args
    if path.startswith("http"):
        final_args += f" {network_args}"
    
    # إضافة أي فلاتر إضافية (زي التقديم Seek)
    if ffmpeg_flags:
        final_args += f" {ffmpeg_flags}"

    if video:
        return MediaStream(
            media_path=path,
            audio_parameters=AudioQuality.STUDIO,
            video_parameters=VideoQuality.HD_720p,
            ffmpeg_parameters=final_args
        )
    else:
        return MediaStream(
            media_path=path,
            audio_parameters=AudioQuality.STUDIO,
            video_flags=MediaStream.Flags.IGNORE,
            ffmpeg_parameters=final_args
        )

async def _safe_clean(chat_id: int):
    try:
        popped = db.pop(chat_id, None)
        if popped: await auto_clean(popped)
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        await set_loop(chat_id, 0)
    except: pass
    finally: gc.collect()

# =======================================================================
# 🏰 MAIN CALL CLASS (الكلاس الكامل)
# =======================================================================

class Call:
    def __init__(self):
        self.active_calls = set()
        self.clients = []
        self.pytgcalls_map = {}
        self.chat_locks: Dict[int, asyncio.Lock] = {}
        self._init_clients()

    def _init_clients(self):
        configs = [
            (config.STRING1, 1), (config.STRING2, 2), 
            (config.STRING3, 3), (config.STRING4, 4), (config.STRING5, 5)
        ]
        count = 0
        for session, idx in configs:
            if session:
                try:
                    ub = Client(f"Assistant{idx}", config.API_ID, config.API_HASH, session_string=session)
                    pc = PyTgCalls(ub)
                    self.clients.append(pc)
                    setattr(self, f"userbot{idx}", ub)
                    name = ["one", "two", "three", "four", "five"][idx-1]
                    setattr(self, name, pc)
                    count += 1
                except Exception as e:
                    LOGGER(__name__).error(f"Failed to initialize Assistant {idx}: {e}")

    async def get_lock(self, chat_id: int):
        if chat_id not in self.chat_locks:
            self.chat_locks[chat_id] = asyncio.Lock()
        return self.chat_locks[chat_id]

    async def start(self):
        LOGGER(__name__).info("🚀 Starting PyTgCalls Clients...")
        if self.clients:
            await asyncio.gather(*[c.start() for c in self.clients])
            for c in self.clients:
                if hasattr(c, 'app'): self.pytgcalls_map[id(c.app)] = c
            await self.decorators()
        LOGGER(__name__).info("✅ All Assistants Started.")

    async def get_tgcalls(self, chat_id: int) -> PyTgCalls:
        assistant = await group_assistant(self, chat_id)
        for client in self.clients:
            if hasattr(client, 'app') and client.app.me.id == assistant.me.id:
                return client
        return self.clients[0]

    # ====================================================
    # 🎧 JOIN CALL (الدالة الكاملة للدخول)
    # ====================================================
    async def join_call(self, chat_id: int, original_chat_id: int, link: str, video: bool = False, image: str = None):
        client = await self.get_tgcalls(chat_id)
        
        # 1. محاولة ضم المساعد للمجموعة
        try:
            await client.join_chat(chat_id)
        except UserAlreadyParticipant:
            pass 
        except (InviteHashExpired, Exception):
            try:
                userbot = await group_assistant(self, chat_id)
                await app.add_chat_members(chat_id, userbot.me.id)
            except: pass

        # 2. بدء التشغيل
        try:
            is_live = "live" in link or "m3u8" in link
            stream = build_stream(link, video, is_live)
            
            try:
                await client.play(chat_id, stream)
            except FloodWait as f:
                LOGGER(__name__).warning(f"FloodWait: Sleeping {f.value}s")
                await asyncio.sleep(f.value)
                await client.play(chat_id, stream)
            except Exception as e:
                # لو قال إن المساعد موجود في الكول بس ساكت، نتجاهل الخطأ ونكمل
                if "already joined" in str(e).lower(): pass
                else: raise e

            # 3. استراحة قصيرة لضمان خروج الصوت
            await asyncio.sleep(1.5) 
            
            self.active_calls.add(chat_id)
            await add_active_chat(chat_id)
            await music_on(chat_id)
            if video: await add_active_video_chat(chat_id)

            # 4. تفعيل وضع الإنهاء التلقائي
            if await is_autoend():
                try:
                    if len(await client.get_participants(chat_id)) <= 1:
                        autoend[chat_id] = datetime.now() + timedelta(minutes=1)
                except: pass

        except NoActiveGroupCall:
            raise AssistantErr("المكالمة الصوتية مغلقة! يرجى فتحها أولاً.")
        except Exception as e:
            raise AssistantErr(f"حدث خطأ أثناء التشغيل: {e}")

    # ====================================================
    # 🔄 CHANGE STREAM (التغيير التلقائي واليدوي)
    # ====================================================
    async def change_stream(self, client, chat_id: int):
        lock = await self.get_lock(chat_id)
        async with lock:
            try: check = db.get(chat_id)
            except: return await self.stop_stream(chat_id)
            if not check: return await self.stop_stream(chat_id)

            try:
                loop = await get_loop(chat_id)
                if loop == 0:
                    popped = check.pop(0)
                    if popped: await auto_clean(popped)
                else:
                    loop -= 1
                    await set_loop(chat_id, loop)
                if not check: return await self.stop_stream(chat_id)
            except: return await self.stop_stream(chat_id)

            track = check[0]
            queued_file = track.get("file")
            vidid = track.get("vidid")
            title = track.get("title")
            user = track.get("by")
            streamtype = track.get("streamtype")
            original_chat_id = track.get("chat_id")
            duration = track.get("dur")
            
            if not queued_file: return await self.stop_stream(chat_id)
            is_video = str(streamtype) == "video"
            final_path = queued_file

            try:
                if "live_" in queued_file:
                    n, link = await YouTube.video(vidid, True)
                    if n == 0: return 
                    final_path = link
                elif "vid_" in queued_file:
                    abs_path = os.path.abspath(queued_file)
                    if not os.path.exists(abs_path) or os.path.getsize(abs_path) < 1024:
                        try:
                            final_path, _ = await YouTube.download(vidid, None, videoid=True, video=is_video)
                            check[0]["file"] = final_path 
                        except: return await self.stop_stream(chat_id)

                stream = build_stream(final_path, is_video)
                try:
                    await client.play(chat_id, stream)
                except FloodWait as f:
                    await asyncio.sleep(f.value)
                    await client.play(chat_id, stream)

            except Exception:
                return await self.stop_stream(chat_id)

            asyncio.create_task(self.safe_send_ui(chat_id, original_chat_id, vidid, title, user, duration))

    async def safe_send_ui(self, chat_id, original_chat_id, vidid, title, user, duration):
        try:
            await asyncio.sleep(1)
            lang = await get_lang(chat_id)
            _ = get_string(lang)
            btn = stream_markup(_, vidid, chat_id)
            markup = InlineKeyboardMarkup(btn)
            caption = _["stream_1"].format(title[:25], duration, user, config.SUPPORT_CHAT)
            img = await get_thumb(vidid)
            try:
                run = await app.send_photo(chat_id=original_chat_id, photo=img, caption=caption, reply_markup=markup)
                if chat_id in db:
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "stream"
            except: pass
        except: pass

    # ====================================================
    # ⏯️ BASIC CONTROLS (إيقاف، استئناف، كتم)
    # ====================================================
    async def stop_stream(self, chat_id: int):
        client = await self.get_tgcalls(chat_id)
        await _safe_clean(chat_id)
        try: await client.leave_call(chat_id)
        except: pass
        self.active_calls.discard(chat_id)

    async def force_stop_stream(self, chat_id: int):
        try:
            check = db.get(chat_id)
            if check: check.pop(0)
        except: pass
        await self.stop_stream(chat_id)

    async def pause_stream(self, chat_id: int):
        client = await self.get_tgcalls(chat_id)
        await client.pause(chat_id)

    async def resume_stream(self, chat_id: int):
        client = await self.get_tgcalls(chat_id)
        await client.resume(chat_id)

    async def mute_stream(self, chat_id: int):
        client = await self.get_tgcalls(chat_id)
        await client.mute(chat_id)

    async def unmute_stream(self, chat_id: int):
        client = await self.get_tgcalls(chat_id)
        await client.unmute(chat_id)

    async def skip_stream(self, chat_id, link, video=None, image=None):
        client = await self.get_tgcalls(chat_id)
        stream = build_stream(link, video=bool(video))
        await client.play(chat_id, stream)

    # ====================================================
    # ⏩ SEEK & SPEED (التقديم وتسريع الصوت)
    # ====================================================
    async def seek_stream(self, chat_id, file_path, to_seek, duration, mode):
        client = await self.get_tgcalls(chat_id)
        if not os.path.exists(file_path): return 
        
        # أمر FFMPEG للتقديم
        seek_flags = f"-ss {to_seek} -to {duration}"
        
        stream = build_stream(file_path, video=(mode=="video"), ffmpeg_flags=seek_flags)
        await client.play(chat_id, stream)

    async def speedup_stream(self, chat_id, file_path, speed, playing):
        client = await self.get_tgcalls(chat_id)
        try:
            base = os.path.basename(file_path)
            chatdir = os.path.join(os.getcwd(), "playback", str(speed))
            os.makedirs(chatdir, exist_ok=True)
            out = os.path.join(chatdir, base)

            # لو الملف المسرع مش موجود، اصنعه
            if not os.path.exists(out):
                vs = str(2.0 / float(speed))
                # فلتر التسريع
                cmd = f'ffmpeg -i "{file_path}" -filter:v "setpts={vs}*PTS" -filter:a atempo={speed} -y "{out}"'
                proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                await proc.communicate()
            
            dur = int(await asyncio.get_event_loop().run_in_executor(None, check_duration, out))
            played, con_seconds = speed_converter(playing[0]["played"], speed)
            
            # تشغيل من النقطة اللي وقفنا عندها
            seek_flags = f"-ss {played} -to {seconds_to_min(dur)}"
            is_video = playing[0]["streamtype"] == "video"
            
            stream = build_stream(out, video=is_video, ffmpeg_flags=seek_flags)

            if chat_id in db:
                await client.play(chat_id, stream)
                db[chat_id][0].update({
                    "played": con_seconds, 
                    "dur": seconds_to_min(dur), 
                    "seconds": dur, 
                    "speed_path": out, 
                    "speed": speed
                })
        except Exception as e:
             LOGGER(__name__).error(f"Speedup Error: {e}")

    # ====================================================
    # 📡 LOGGER STREAM (تشغيل في السجل)
    # ====================================================
    async def stream_call(self, link):
        assistant = await self.get_tgcalls(config.LOGGER_ID)
        try:
            await assistant.play(config.LOGGER_ID, MediaStream(link))
            await asyncio.sleep(8) # يفضل شغال 8 ثواني في السجل
        finally:
            try: await assistant.leave_call(config.LOGGER_ID)
            except: pass

    # ====================================================
    # 🔄 UPDATES DECORATOR (مراقب الأحداث)
    # ====================================================
    async def decorators(self):
        async def unified_handler(client, update: Update):
            if not isinstance(update, (StreamEnded, ChatUpdate)): return
            try:
                chat_id = getattr(update, "chat_id", None)
                if not chat_id: return

                # لو الأغنية خلصت -> شغل اللي بعدها
                if isinstance(update, StreamEnded):
                    if update.stream_type == StreamEnded.Type.AUDIO:
                        asyncio.create_task(self.change_stream(client, chat_id))
                
                # لو البوت انطرد أو الكول قفل -> وقف التشغيل
                elif isinstance(update, ChatUpdate):
                    if update.status in [ChatUpdate.Status.LEFT_CALL, ChatUpdate.Status.KICKED, ChatUpdate.Status.CLOSED_VOICE_CHAT]:
                        await self.stop_stream(chat_id)
            except: pass

        for c in self.clients:
            if hasattr(c, 'on_update'): c.on_update()(unified_handler)

Hotty = Call()
