import asyncio
import os
import gc
import random
from datetime import datetime, timedelta
from typing import Union, List, Dict, Optional

from pyrogram import Client
from pyrogram.errors import (
    FloodWait,
    ChatAdminRequired,
    UserAlreadyParticipant,
    UserNotParticipant,
    PeerIdInvalid
)
from pyrogram.types import InlineKeyboardMarkup

from pytgcalls import PyTgCalls
from pytgcalls.types import (
    MediaStream,
    AudioQuality,
    VideoQuality,
    StreamEnded,
    ChatUpdate,
    Update,
    GroupCallConfig
)
from pytgcalls.exceptions import (
    NoActiveGroupCall,
    NoAudioSourceFound,
    NoVideoSourceFound,
    InvalidStreamMode,
    AlreadyJoined
)

# Exception Compatibility Layer
try:
    from pytgcalls.exceptions import TelegramServerError, ConnectionNotFound
except ImportError:
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

# =======================================================================
# ⚙️ DYNAMIC FFMPEG GENERATOR (The Core)
# =======================================================================
# This function generates optimized flags based on content type

def get_ffmpeg_flags(is_video: bool, is_live: bool) -> str:
    base_flags = (
        "-re -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 "
        "-reconnect_on_network_error 1 " # Reconnect on packet loss
        "-bg 0 "
        "-max_muxing_queue_size 4096 "
        "-headers 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)' "
    )
    
    audio_flags = "-ar 48000 -ac 2 -f s16le "
    
    if is_live:
        # Live streams need zero latency tuning
        return base_flags + "-tune zerolatency -preset ultrafast -bufsize 512k " + audio_flags
    else:
        # Static files benefit from larger buffers
        return base_flags + "-preset veryfast -bufsize 8192k " + audio_flags

def build_stream(path: str, video: bool = False, live: bool = False, ffmpeg: str = None) -> MediaStream:
    custom_ffmpeg = ffmpeg if ffmpeg else get_ffmpeg_flags(video, live)
    
    if video:
        return MediaStream(
            media_path=path,
            audio_parameters=AudioQuality.STUDIO,
            video_parameters=VideoQuality.HD_720p,
            audio_flags=MediaStream.Flags.REQUIRED,
            video_flags=MediaStream.Flags.REQUIRED,
            ffmpeg_parameters=custom_ffmpeg,
        )
    else:
        return MediaStream(
            media_path=path,
            audio_parameters=AudioQuality.STUDIO,
            audio_flags=MediaStream.Flags.REQUIRED,
            video_flags=MediaStream.Flags.IGNORE,
            ffmpeg_parameters=custom_ffmpeg,
        )

# =======================================================================
# 🧹 MEMORY MANAGEMENT
# =======================================================================

async def _aggressive_clean_(chat_id: int):
    """Deep cleaning for chat data to prevent memory leaks."""
    try:
        popped = db.pop(chat_id, None)
        if popped:
            await auto_clean(popped)
        
        # Concurrent DB operations
        await asyncio.gather(
            remove_active_video_chat(chat_id),
            remove_active_chat(chat_id),
            set_loop(chat_id, 0)
        )
    except Exception:
        pass
    finally:
        gc.collect()

# =======================================================================
# 💎 THE TITAN ENGINE (Class Call)
# =======================================================================

class Call:
    def __init__(self):
        self.active_calls = set()
        self.auth_chats = set()
        
        # Locks to prevent race conditions (Atomic Operations)
        self.action_locks: Dict[int, asyncio.Lock] = {}
        self.init_lock = asyncio.Lock()
        
        self.clients = []
        self.pytgcalls_map = {}
        self._initialize_assistants()

    def _initialize_assistants(self):
        """Initializes assistants with optimized cache duration."""
        configs = [
            config.STRING1, config.STRING2, config.STRING3, 
            config.STRING4, config.STRING5
        ]
        
        for index, string in enumerate(configs, 1):
            if string:
                client_name = f"Assistant{index}"
                userbot = Client(client_name, config.API_ID, config.API_HASH, session_string=string)
                # Cache Duration 100 is critical for v2.2.8 stability
                pytgcalls = PyTgCalls(userbot, cache_duration=100)
                
                self.clients.append(pytgcalls)
                
                # Attribute mapping for quick access
                setattr(self, f"userbot{index}", userbot)
                setattr(self, f"one" if index==1 else f"two" if index==2 else f"three" if index==3 else f"four" if index==4 else "five", pytgcalls)

    async def get_lock(self, chat_id: int) -> asyncio.Lock:
        """Returns a unique lock for the chat."""
        async with self.init_lock:
            if chat_id not in self.action_locks:
                self.action_locks[chat_id] = asyncio.Lock()
            return self.action_locks[chat_id]

    async def get_tgcalls(self, chat_id: int) -> PyTgCalls:
        """Intelligently selects the correct assistant."""
        assistant = await group_assistant(self, chat_id)
        for client in self.clients:
            if hasattr(client, 'app') and client.app.me.id == assistant.me.id:
                return client
        return self.clients[0]

    async def start(self):
        LOGGER(__name__).info("🚀 Titan Engine v5.0 (Atomic/Hybrid) Starting...")
        # Concurrent startup
        await asyncio.gather(*[c.start() for c in self.clients])
        await self.decorators()
        LOGGER(__name__).info("✅ Titan Engine Online: All Systems Operational.")

    # ================= CORE LOGIC: JOIN & PLAY =================
    
    async def join_call(self, chat_id: int, original_chat_id: int, link: str, video: bool = False, image: str = None):
        """The entry point. Handles joining, playing, and initial error recovery."""
        client = await self.get_tgcalls(chat_id)
        lang = await get_lang(chat_id)
        _ = get_string(lang)
        
        # Determine if source is live (for buffering strategy)
        is_live = "m3u8" in link or "live" in link
        
        stream = build_stream(link, video, is_live)
        
        async with await self.get_lock(chat_id):
            try:
                # Attempt 1: Direct Play
                await client.play(chat_id, stream)
                await asyncio.sleep(1.5) # Allow buffer to fill
                
            except (NoActiveGroupCall, ChatAdminRequired):
                raise AssistantErr(_["call_8"])
                
            except (NoAudioSourceFound, NoVideoSourceFound, ConnectionNotFound):
                # 🛑 FAILSAFE: Source invalid.
                # If it's a file path and exists, FFmpeg failed -> corrupted file.
                # If it's a link, link expired -> Needs redownload logic handled in `change_stream`.
                # For `join_call`, we propagate error to trigger clean retry.
                LOGGER(__name__).warning(f"Join failed for {chat_id}, stream invalid.")
                raise AssistantErr(_["call_11"])
                
            except Exception as e:
                # Catch-all for other PyTgCalls weirdness
                LOGGER(__name__).error(f"Critical Join Error: {e}")
                raise AssistantErr(f"Error: {e}")

            # Success State
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

    # ================= CORE LOGIC: STREAM SWAPPING =================

    async def change_stream(self, client, chat_id: int):
        """The heart of the bot. Handles Queue, Next Song, and Fallbacks."""
        
        # 🔒 Atomic Operation: Only one change per chat at a time
        async with await self.get_lock(chat_id):
            
            check = db.get(chat_id)
            
            # 1. Queue Validation
            if not check or not isinstance(check, list) or len(check) == 0:
                return await self.stop_stream_internal(chat_id, client)

            # 2. Loop Logic
            loop = await get_loop(chat_id)
            popped = None
            try:
                if loop == 0:
                    popped = check.pop(0)
                else:
                    loop -= 1
                    await set_loop(chat_id, loop)
                
                if popped: await auto_clean(popped)
                
                if not check:
                    return await self.stop_stream_internal(chat_id, client)
            except Exception:
                return await self.stop_stream_internal(chat_id, client)

            # 3. Data Extraction
            track_data = check[0]
            queued_file = track_data["file"]
            vidid = track_data["vidid"]
            title = track_data["title"]
            user = track_data["by"]
            streamtype = track_data["streamtype"]
            original_chat_id = track_data["chat_id"]
            
            is_video = (str(streamtype) == "video")
            lang = await get_lang(chat_id)
            _ = get_string(lang)

            # 4. 🧠 INTELLIGENT SOURCE RESOLUTION & FALLBACK
            final_stream_path = queued_file
            is_live = False

            # Scenario A: It's a YouTube Link (Direct) -> Refresh Link
            if "live_" in queued_file:
                n, link = await YouTube.video(vidid, True)
                if n == 0: 
                    # Failed to get live link
                    await app.send_message(original_chat_id, text=_["call_6"])
                    return await self.change_stream_recursive(client, chat_id) # Skip to next
                final_stream_path = link
                is_live = True

            # Scenario B: It's a Downloaded File -> Verify Existence
            elif "vid_" in queued_file or os.path.exists(queued_file):
                if not os.path.exists(queued_file):
                    # File deleted? Redownload immediately.
                    LOGGER(__name__).info(f"File missing: {queued_file}, Redownloading...")
                    msg = await app.send_message(original_chat_id, _["call_7"])
                    try:
                        final_stream_path, _ = await YouTube.download(vidid, msg, videoid=True, video=is_video)
                        await msg.delete()
                    except Exception as e:
                        LOGGER(__name__).error(f"Redownload failed: {e}")
                        await app.send_message(original_chat_id, _["call_6"])
                        return await self.change_stream_recursive(client, chat_id) # Skip

            # 5. Playback Execution
            stream = build_stream(final_stream_path, is_video, is_live)
            
            try:
                await client.play(chat_id, stream)
                # Success!
            except (NoAudioSourceFound, NoVideoSourceFound) as e:
                # 🛑 Critical Fallback: FFMPEG failed to read source.
                # If it was a link, try downloading it.
                LOGGER(__name__).warning(f"Playback failed for {chat_id}, forcing download.")
                try:
                    dl_msg = await app.send_message(original_chat_id, _["call_7"])
                    new_path, _ = await YouTube.download(vidid, dl_msg, videoid=True, video=is_video)
                    await dl_msg.delete()
                    
                    # Update DB with new path so Loop works
                    check[0]["file"] = new_path
                    stream = build_stream(new_path, is_video, False)
                    await client.play(chat_id, stream)
                    
                except Exception as final_e:
                    LOGGER(__name__).error(f"Fallback failed: {final_e}")
                    await app.send_message(original_chat_id, _["call_6"])
                    return await self.change_stream_recursive(client, chat_id)
            except Exception as e:
                LOGGER(__name__).error(f"Unknown Play Error: {e}")
                return await self.stop_stream_internal(chat_id, client)

            # 6. UI Update (Non-blocking)
            asyncio.create_task(self.send_ui(chat_id, original_chat_id, vidid, title, user, track_data["dur"], streamtype, is_live, _))

    async def change_stream_recursive(self, client, chat_id):
        """Helper to recursively skip songs without locking issues."""
        # We release the lock by exiting change_stream context, then call again.
        # But here we need to be careful. Ideally, just call change_stream again.
        # Since we are inside the lock in change_stream, calling it directly is deadlock.
        # We schedule it on loop.
        asyncio.create_task(self.change_stream(client, chat_id))

    async def send_ui(self, chat_id, original_chat_id, vidid, title, user, duration, streamtype, is_live, _):
        """Handles UI updates safely."""
        try:
            def get_btn(vid_id):
                if stream_markup2: return stream_markup2(_, chat_id)
                return stream_markup(_, vid_id, chat_id)

            msg_stream1 = _["stream_1"]
            img = await get_thumb(vidid)
            caption = ""
            markup = None
            
            if vidid == "telegram":
                 img = config.TELEGRAM_AUDIO_URL if str(streamtype) == "audio" else config.TELEGRAM_VIDEO_URL
                 caption = msg_stream1.format(title[:23], duration, user, config.SUPPORT_CHAT)
                 markup = InlineKeyboardMarkup(get_btn("telegram"))
            elif vidid == "soundcloud":
                 img = config.SOUNCLOUD_IMG_URL
                 caption = msg_stream1.format(title[:23], duration, user, config.SUPPORT_CHAT)
                 markup = InlineKeyboardMarkup(get_btn("soundcloud"))
            else:
                 caption = msg_stream1.format(title[:23], duration, user, f"https://t.me/{app.username}?start=info_{vidid}")
                 markup = InlineKeyboardMarkup(get_btn(vidid) if is_live else stream_markup(_, vidid, chat_id))

            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=img,
                caption=caption,
                reply_markup=markup
            )
            if chat_id in db:
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
        except:
            pass

    async def stop_stream(self, chat_id: int):
        client = await self.get_tgcalls(chat_id)
        await self.stop_stream_internal(chat_id, client)

    async def stop_stream_internal(self, chat_id: int, client):
        await _aggressive_clean_(chat_id)
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
        await self.stop_stream_internal(chat_id, client)

    # ================= STANDARD CONTROLS =================
    
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
        # Seeking requires re-streaming with offset
        ffmpeg = f"-ss {to_seek} -to {duration}"
        stream = build_stream(file_path, video=(mode == "video"), ffmpeg=ffmpeg)
        await client.play(chat_id, stream)

    async def speedup_stream(self, chat_id, file_path, speed, playing):
        client = await self.get_tgcalls(chat_id)
        # Logic for speedup remains standard as it uses local processing
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
        
        # Seek to current position in new speed
        ffmpeg = f"-ss {played} -to {seconds_to_min(dur)}"
        stream = build_stream(out, video=(playing[0]["streamtype"] == "video"), ffmpeg=ffmpeg)

        if chat_id in db:
            await client.play(chat_id, stream)
            db[chat_id][0].update({"played": con_seconds, "dur": seconds_to_min(dur), "seconds": dur, "speed_path": out, "speed": speed})

    # ================= EVENTS & DECORATORS =================

    async def decorators(self):
        async def unified_handler(client, update: Update):
            chat_id = getattr(update, "chat_id", None)
            if not chat_id: return

            if isinstance(update, StreamEnded):
                # 🔄 Auto-Next Trigger
                # Using a task to prevent blocking the event loop
                asyncio.create_task(self.change_stream(client, chat_id))
            
            elif isinstance(update, ChatUpdate):
                # 🛑 Left Call / Kicked Handling
                if update.status in [ChatUpdate.Status.LEFT_CALL, ChatUpdate.Status.KICKED, ChatUpdate.Status.CLOSED_VOICE_CHAT]:
                    await _aggressive_clean_(chat_id)
                    if chat_id in self.active_calls:
                        self.active_calls.discard(chat_id)

        for assistant in self.clients:
            try:
                if hasattr(assistant, 'on_update'):
                    assistant.on_update()(unified_handler)
            except: pass

Hotty = Call()
