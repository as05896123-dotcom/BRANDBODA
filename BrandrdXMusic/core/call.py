import asyncio
import os
import gc
import sys
import traceback
from datetime import datetime, timedelta
from typing import Union, List, Dict, Any

from pyrogram import Client
from pyrogram.errors import FloodWait, ChatAdminRequired, UserAlreadyParticipant
from pyrogram.types import InlineKeyboardMarkup

# ============================================================
# 🛡️ IMPORT SAFETY SYSTEM
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
    print(f"CRITICAL ERROR: PyTgCalls not installed correctly! {e}")
    sys.exit(1)

# Fallback for Network Exceptions
try:
    from pytgcalls.exceptions import TelegramServerError, ConnectionNotFound
except ImportError:
    try:
        from ntgcalls import TelegramServerError, ConnectionNotFound
    except:
        TelegramServerError = Exception
        ConnectionNotFound = Exception

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
# 🛠️ UTILS & SAFETY HELPERS
# =======================================================================

def get_ffmpeg_flags(live: bool = False) -> str:
    """Returns optimized FFMPEG flags to prevent crashing."""
    return (
        "-re -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 "
        "-reconnect_on_network_error 1 "
        "-bg 0 "
        "-max_muxing_queue_size 4096 "
        "-headers 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)' "
        f"{'-tune zerolatency -preset ultrafast' if live else '-preset veryfast'}"
    )

def build_stream(path: str, video: bool = False, live: bool = False) -> MediaStream:
    """Builds a MediaStream object safely."""
    if not path:
        raise ValueError("Stream Path is Empty!")
    
    flags = get_ffmpeg_flags(live)
    if video:
        return MediaStream(
            media_path=path,
            audio_parameters=AudioQuality.STUDIO,
            video_parameters=VideoQuality.HD_720p,
            audio_flags=MediaStream.Flags.REQUIRED,
            video_flags=MediaStream.Flags.REQUIRED,
            ffmpeg_parameters=flags,
        )
    return MediaStream(
        media_path=path,
        audio_parameters=AudioQuality.STUDIO,
        audio_flags=MediaStream.Flags.REQUIRED,
        video_flags=MediaStream.Flags.IGNORE,
        ffmpeg_parameters=flags,
    )

async def _safe_clean(chat_id: int):
    """Safely cleans chat data without crashing."""
    try:
        popped = db.pop(chat_id, None)
        if popped: await auto_clean(popped)
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        await set_loop(chat_id, 0)
    except Exception as e:
        LOGGER(__name__).warning(f"Cleanup warning for {chat_id}: {e}")
    finally:
        gc.collect()

# =======================================================================
# 🏰 THE FORTRESS ENGINE (Class Call)
# =======================================================================

class Call:
    def __init__(self):
        self.active_calls = set()
        self.clients = []
        self.pytgcalls_map = {}
        self._init_clients()

    def _init_clients(self):
        """Initializes clients with error checking."""
        configs = [
            (config.STRING1, 1), (config.STRING2, 2), 
            (config.STRING3, 3), (config.STRING4, 4), (config.STRING5, 5)
        ]
        for session, idx in configs:
            if session:
                try:
                    ub = Client(f"Assistant{idx}", config.API_ID, config.API_HASH, session_string=session)
                    pc = PyTgCalls(ub, cache_duration=100)
                    self.clients.append(pc)
                    setattr(self, f"userbot{idx}", ub)
                    # Mapping helper
                    name = ["one", "two", "three", "four", "five"][idx-1]
                    setattr(self, name, pc)
                except Exception as e:
                    LOGGER(__name__).error(f"Failed to initialize Assistant {idx}: {e}")

    async def run_diagnostics(self):
        """Checks system health on startup."""
        LOGGER(__name__).info("🔍 RUNNING SYSTEM DIAGNOSTICS...")
        
        # 1. Check Clients
        if not self.clients:
            LOGGER(__name__).error("❌ No Assistant Clients Loaded! check config strings.")
        else:
            LOGGER(__name__).info(f"✅ {len(self.clients)} Assistants Loaded.")

        # 2. Check FFMPEG
        try:
            process = await asyncio.create_subprocess_shell(
                "ffmpeg -version", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            if process.returncode == 0:
                LOGGER(__name__).info("✅ FFMPEG is installed and working.")
            else:
                LOGGER(__name__).warning("⚠️ FFMPEG might have issues.")
        except:
            LOGGER(__name__).error("❌ FFMPEG NOT FOUND! Music will not work.")

        # 3. Check Directories
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
            LOGGER(__name__).info("✅ Created 'downloads' directory.")
        if not os.path.exists("cache"):
            os.makedirs("cache")
            LOGGER(__name__).info("✅ Created 'cache' directory.")

    async def start(self):
        await self.run_diagnostics()
        LOGGER(__name__).info("🚀 Starting PyTgCalls...")
        if self.clients:
            await asyncio.gather(*[c.start() for c in self.clients])
            # Map clients after start to ensure 'app' is ready
            for c in self.clients:
                if hasattr(c, 'app'): self.pytgcalls_map[id(c.app)] = c
            await self.decorators()
        LOGGER(__name__).info("✅ Call System Online.")

    async def get_tgcalls(self, chat_id: int) -> PyTgCalls:
        assistant = await group_assistant(self, chat_id)
        for client in self.clients:
            if hasattr(client, 'app') and client.app.me.id == assistant.me.id:
                return client
        return self.clients[0]

    # ================= 🛡️ ROBUST JOIN =================

    async def join_call(self, chat_id: int, original_chat_id: int, link: str, video: bool = False, image: str = None):
        client = await self.get_tgcalls(chat_id)
        
        try:
            # Determine if live
            is_live = "live" in link or "m3u8" in link
            stream = build_stream(link, video, is_live)
            
            await client.play(chat_id, stream)
            await asyncio.sleep(1) # Stabilization buffer

            self.active_calls.add(chat_id)
            await add_active_chat(chat_id)
            await music_on(chat_id)
            if video: await add_active_video_chat(chat_id)

            # Auto-End Monitor
            if await is_autoend():
                try:
                    if len(await client.get_participants(chat_id)) <= 1:
                        autoend[chat_id] = datetime.now() + timedelta(minutes=1)
                except: pass

        except NoActiveGroupCall:
            # Fallback message handled by caller usually, but we raise specific error
            raise AssistantErr("المكالمة الصوتية مغلقة! يرجى فتحها.")
        except (NoAudioSourceFound, NoVideoSourceFound):
            LOGGER(__name__).error(f"Stream failed for {link}")
            raise AssistantErr("فشل تشغيل الرابط، تأكد أنه صالح.")
        except Exception as e:
            LOGGER(__name__).error(f"Unknown Join Error: {e}")
            raise AssistantErr(f"خطأ غير متوقع: {e}")

    # ================= 🛡️ ROBUST CHANGE STREAM (KeyError KILLER) =================

    async def change_stream(self, client, chat_id: int):
        # 1. Safe Database Access
        try:
            check = db.get(chat_id)
        except Exception:
            return await self.stop_stream(chat_id)

        if not check:
            return await self.stop_stream(chat_id)

        # 2. Queue Logic
        try:
            loop = await get_loop(chat_id)
            if loop == 0:
                popped = check.pop(0)
                if popped: await auto_clean(popped)
            else:
                loop -= 1
                await set_loop(chat_id, loop)
            
            if not check:
                return await self.stop_stream(chat_id)
        except Exception as e:
            LOGGER(__name__).error(f"Queue Error: {e}")
            return await self.stop_stream(chat_id)

        # 3. 🔍 DATA EXTRACTION WITH FALLBACKS (The Anti-KeyError)
        track = check[0]
        
        # Use .get() to prevent crashing if keys are missing from DB
        queued_file = track.get("file")
        vidid = track.get("vidid")
        title = track.get("title", "Unknown Track")
        user = track.get("by", "Unknown")
        streamtype = track.get("streamtype", "audio")
        original_chat_id = track.get("chat_id", chat_id)
        duration = track.get("dur", "00:00")
        
        if not queued_file or not vidid:
            LOGGER(__name__).warning(f"Corrupt track data in {chat_id}, skipping...")
            return await self.change_stream(client, chat_id)

        is_video = str(streamtype) == "video"
        is_live = False
        final_path = queued_file

        # 4. Source Verification
        try:
            if "live_" in queued_file:
                n, link = await YouTube.video(vidid, True)
                if n == 0:
                    await app.send_message(original_chat_id, "فشل الحصول على رابط البث.")
                    return await self.change_stream(client, chat_id)
                final_path = link
                is_live = True
            
            elif "vid_" in queued_file:
                if not os.path.exists(queued_file):
                    LOGGER(__name__).info(f"File missing ({queued_file}), attempting re-download.")
                    msg = await app.send_message(original_chat_id, "🔄 الملف مفقود، جاري التحميل...")
                    try:
                        final_path, _ = await YouTube.download(vidid, msg, videoid=True, video=is_video)
                        # Update DB to prevent loop failure
                        check[0]["file"] = final_path
                        await msg.delete()
                    except Exception as e:
                        LOGGER(__name__).error(f"Redownload failed: {e}")
                        await msg.edit("❌ فشل تشغيل الملف.")
                        return await self.change_stream(client, chat_id)

            # 5. Playback
            stream = build_stream(final_path, is_video, is_live)
            await client.play(chat_id, stream)

        except Exception as e:
            # 🛑 Fail-Safe: Force Download if Stream Fails
            LOGGER(__name__).error(f"Playback failed: {e}. Trying Force Download.")
            try:
                 new_path, _ = await YouTube.download(vidid, None, videoid=True, video=is_video)
                 stream = build_stream(new_path, is_video, False)
                 await client.play(chat_id, stream)
            except:
                 # If everything fails, stop safely
                 return await self.stop_stream(chat_id)

        # 6. UI Update (Safe Mode)
        asyncio.create_task(self.safe_send_ui(chat_id, original_chat_id, vidid, title, user, duration, streamtype, is_live))

    async def safe_send_ui(self, chat_id, original_chat_id, vidid, title, user, duration, streamtype, is_live):
        """Sends UI without crashing on missing translation keys."""
        try:
            lang = await get_lang(chat_id)
            _ = get_string(lang)
            
            # Button Logic with Fallback
            btn = None
            try:
                if stream_markup2: btn = stream_markup2(_, chat_id)
                else: btn = stream_markup(_, vidid, chat_id)
            except Exception:
                pass # No buttons if error
            
            markup = InlineKeyboardMarkup(btn) if btn else None
            
            # Caption Logic with Fallback
            try:
                caption = _["stream_1"].format(title[:25], duration, user, config.SUPPORT_CHAT)
            except (KeyError, IndexError):
                caption = f"🎶 **Playing:** {title}\n👤 **By:** {user}"

            img = await get_thumb(vidid)
            
            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=img,
                caption=caption,
                reply_markup=markup
            )
            
            if chat_id in db:
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"

        except Exception as e:
            LOGGER(__name__).error(f"UI Error (Ignored): {e}")

    # ================= STANDARD CONTROLS =================

    async def stop_stream(self, chat_id: int):
        client = await self.get_tgcalls(chat_id)
        await _safe_clean(chat_id)
        if chat_id in self.active_calls:
            try: await client.leave_call(chat_id)
            except: pass
            self.active_calls.discard(chat_id)

    async def force_stop_stream(self, chat_id: int):
        client = await self.get_tgcalls(chat_id)
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

    async def seek_stream(self, chat_id, file_path, to_seek, duration, mode):
        client = await self.get_tgcalls(chat_id)
        # Simplified seek build to prevent errors
        ffmpeg = f"-ss {to_seek} -to {duration}"
        if mode == "video":
             stream = MediaStream(file_path, audio_parameters=AudioQuality.STUDIO, video_parameters=VideoQuality.HD_720p, ffmpeg_parameters=ffmpeg)
        else:
             stream = MediaStream(file_path, audio_parameters=AudioQuality.STUDIO, video_flags=MediaStream.Flags.IGNORE, ffmpeg_parameters=ffmpeg)
        await client.play(chat_id, stream)

    async def speedup_stream(self, chat_id, file_path, speed, playing):
        client = await self.get_tgcalls(chat_id)
        try:
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
            is_video = playing[0]["streamtype"] == "video"
            
            if is_video:
                stream = MediaStream(out, audio_parameters=AudioQuality.STUDIO, video_parameters=VideoQuality.HD_720p, ffmpeg_parameters=ffmpeg)
            else:
                stream = MediaStream(out, audio_parameters=AudioQuality.STUDIO, video_flags=MediaStream.Flags.IGNORE, ffmpeg_parameters=ffmpeg)

            if chat_id in db:
                await client.play(chat_id, stream)
                db[chat_id][0].update({"played": con_seconds, "dur": seconds_to_min(dur), "seconds": dur, "speed_path": out, "speed": speed})
        except Exception as e:
             LOGGER(__name__).error(f"Speedup Error: {e}")

    async def stream_call(self, link):
        assistant = await self.get_tgcalls(config.LOGGER_ID)
        try:
            await assistant.play(config.LOGGER_ID, MediaStream(link))
            await asyncio.sleep(8)
        finally:
            try: await assistant.leave_call(config.LOGGER_ID)
            except: pass

    async def decorators(self):
        async def unified_handler(client, update: Update):
            if not getattr(update, "chat_id", None): return
            chat_id = update.chat_id

            if isinstance(update, StreamEnded):
                if update.stream_type == StreamEnded.Type.AUDIO:
                     # Use Task to allow async execution without blocking
                    asyncio.create_task(self.change_stream(client, chat_id))
            
            elif isinstance(update, ChatUpdate):
                if update.status in [ChatUpdate.Status.LEFT_CALL, ChatUpdate.Status.KICKED, ChatUpdate.Status.CLOSED_VOICE_CHAT]:
                    await self.stop_stream(chat_id)

        for c in self.clients:
            if hasattr(c, 'on_update'): c.on_update()(unified_handler)

Hotty = Call()
