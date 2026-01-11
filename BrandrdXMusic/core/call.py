import asyncio
import os
import random
import contextlib
from datetime import datetime, timedelta
from typing import Union

from pyrogram import Client
from pyrogram.raw import functions as raw_functions
from pyrogram.errors import ChatAdminRequired
from pyrogram.types import InlineKeyboardMarkup

from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality, ChatUpdate, StreamEnded, Update
from pytgcalls.exceptions import NoActiveGroupCall, TelegramServerError

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

# Import get_string for localization (fallback defined if unavailable)
try:
    from BrandrdXMusic.utils.strings import get_string
except ImportError:
    def get_string(lang):
        # Placeholder dictionary for localization keys used in code
        return {
            "call_6": "Unable to proceed with playback.",
            "call_7": "Processing request...",
            "call_8": "Failed to start the group call.",
            "call_10": "Telegram server error occurred.",
            "stream_1": "{}\nTitle: {}\nDuration: {}\nRequested by {}"
        }

# Import stream_markup2 if available
try:
    from BrandrdXMusic.utils.inline.play import stream_markup2
except ImportError:
    stream_markup2 = None

autoend = {}
counter = {}
AUTO_END_TIME = 1

def dynamic_media_stream(path: str, video: bool = False, ffmpeg_params: str = None) -> MediaStream:
    """Create a new MediaStream for audio or video streaming."""
    audio_params = AudioQuality.HIGH
    video_params = VideoQuality.SD_480p if video else None
    return MediaStream(
        media_path=path,
        audio_parameters=audio_params,
        video_parameters=video_params,
        ffmpeg_parameters=ffmpeg_params,
        video_flags=MediaStream.Flags.REQUIRED if video else MediaStream.Flags.IGNORE,
    )

async def _clear_(chat_id: int) -> None:
    """Clear the active playlist and cleanup states."""
    if popped := db.pop(chat_id, None):
        await auto_clean(popped)
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)
    await set_loop(chat_id, 0)

class Call:
    def __init__(self):
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

        # Map each Pyrogram client to its PyTgCalls counterpart
        self.pytgcalls_map = {}
        if self.userbot1: self.pytgcalls_map[id(self.userbot1)] = self.one
        if self.userbot2: self.pytgcalls_map[id(self.userbot2)] = self.two
        if self.userbot3: self.pytgcalls_map[id(self.userbot3)] = self.three
        if self.userbot4: self.pytgcalls_map[id(self.userbot4)] = self.four
        if self.userbot5: self.pytgcalls_map[id(self.userbot5)] = self.five

        self.active_calls = set()

    async def get_tgcalls(self, chat_id: int):
        """Get the appropriate PyTgCalls client for the chat."""
        assistant = await group_assistant(self, chat_id)
        return self.pytgcalls_map.get(id(assistant), self.one)

    async def pause_stream(self, chat_id: int):
        try:
            client = await self.get_tgcalls(chat_id)
            await client.pause(chat_id)
        except Exception:
            pass

    async def resume_stream(self, chat_id: int):
        try:
            client = await self.get_tgcalls(chat_id)
            await client.resume(chat_id)
        except Exception:
            pass

    async def mute_stream(self, chat_id: int):
        try:
            client = await self.get_tgcalls(chat_id)
            await client.mute(chat_id)
        except Exception:
            pass

    async def unmute_stream(self, chat_id: int):
        try:
            client = await self.get_tgcalls(chat_id)
            await client.unmute(chat_id)
        except Exception:
            pass

    async def stop_stream(self, chat_id: int):
        """Stop the current stream and leave the voice chat."""
        client = await self.get_tgcalls(chat_id)
        try:
            await _clear_(chat_id)
            await client.leave_call(chat_id)
        except Exception:
            pass
        finally:
            self.active_calls.discard(chat_id)

    async def force_stop_stream(self, chat_id: int):
        """Force stop the stream and clean playlist."""
        client = await self.get_tgcalls(chat_id)
        try:
            if queue := db.get(chat_id):
                queue.pop(0)
        except Exception:
            pass
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        await _clear_(chat_id)
        try:
            await client.leave_call(chat_id)
        except Exception:
            pass
        finally:
            self.active_calls.discard(chat_id)

    async def skip_stream(self, chat_id: int, link: str, video: Union[bool, str] = None, image: Union[bool, str] = None):
        """Skip the current track and immediately play a new one."""
        client = await self.get_tgcalls(chat_id)
        if not link.startswith("http"):
            link = os.path.abspath(link)
        stream = MediaStream(link,
                             audio_parameters=AudioQuality.HIGH,
                             video_parameters=VideoQuality.SD_480p if video else None,
                             video_flags=MediaStream.Flags.REQUIRED if video else MediaStream.Flags.IGNORE)
        await client.change_stream(chat_id, stream)

    async def seek_stream(self, chat_id: int, file_path: str, to_seek: str, duration: str, mode):
        """Seek to a specific point in the currently playing file."""
        client = await self.get_tgcalls(chat_id)
        ffmpeg_params = f"-ss {to_seek} -to {duration}"
        stream = MediaStream(file_path,
                             audio_parameters=AudioQuality.HIGH,
                             video_parameters=VideoQuality.SD_480p if mode == "video" else None,
                             video_flags=MediaStream.Flags.REQUIRED if mode == "video" else MediaStream.Flags.IGNORE,
                             ffmpeg_parameters=ffmpeg_params)
        await client.change_stream(chat_id, stream)

    async def speedup_stream(self, chat_id: int, file_path: str, speed: float, playing: list):
        """Speed up or slow down playback by re-encoding the file temporarily."""
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
        duration_min = seconds_to_min(dur)
        ffmpeg_params = f"-ss {played} -to {duration_min}"
        video_flag = (playing[0]["streamtype"] == "video")
        stream = MediaStream(out,
                             audio_parameters=AudioQuality.HIGH,
                             video_parameters=VideoQuality.SD_480p if video_flag else None,
                             video_flags=MediaStream.Flags.REQUIRED if video_flag else MediaStream.Flags.IGNORE,
                             ffmpeg_parameters=ffmpeg_params)

        if chat_id in db and db[chat_id] and db[chat_id][0].get("file") == file_path:
            await client.change_stream(chat_id, stream)
            db[chat_id][0].update({
                "played": con_seconds,
                "dur": duration_min,
                "seconds": dur,
                "speed_path": out,
                "speed": speed
            })
        else:
            raise AssistantErr("Stream mismatch during speedup.")

    async def join_call(self, chat_id: int, original_chat_id: int, link: str, video: Union[bool, str] = None, image: Union[bool, str] = None):
        """Join the voice chat and start playing the specified track."""
        client = await self.get_tgcalls(chat_id)
        assistant = await group_assistant(self, chat_id)
        lang = await get_lang(chat_id)
        _ = get_string(lang)
        if not link.startswith("http"):
            link = os.path.abspath(link)
        # Prepare media stream
        if video:
            stream = MediaStream(link, audio_parameters=AudioQuality.HIGH, video_parameters=VideoQuality.SD_480p)
        else:
            stream = MediaStream(link, audio_parameters=AudioQuality.HIGH, video_flags=MediaStream.Flags.IGNORE)
        try:
            await client.play(chat_id, stream)
        except (ChatAdminRequired, NoActiveGroupCall):
            try:
                # Create a new group call if one doesn't exist
                peer = await assistant.resolve_peer(chat_id)
                random_id = random.getrandbits(32)
                await assistant.send(raw_functions.phone.CreateGroupCall(peer=peer, random_id=random_id))
                await asyncio.sleep(1)
                await client.play(chat_id, stream)
            except Exception:
                raise AssistantErr(_["call_8"])
        except TelegramServerError:
            raise AssistantErr(_["call_10"])
        except Exception:
            raise AssistantErr(_["call_8"])

        self.active_calls.add(chat_id)
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video:
            await add_active_video_chat(chat_id)
        if await is_autoend():
            try:
                members = await assistant.get_chat_members_count(chat_id)
                if members <= 1:
                    autoend[chat_id] = datetime.now() + timedelta(minutes=AUTO_END_TIME)
            except Exception:
                pass

    async def change_stream(self, client, chat_id: int):
        """Automatically move to the next track when the current stream ends."""
        queue = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)

        try:
            if loop == 0:
                popped = queue.pop(0)
            else:
                loop -= 1
                await set_loop(chat_id, loop)
            if popped:
                await auto_clean(popped)
            if not queue:
                await _clear_(chat_id)
                await client.leave_call(chat_id)
                self.active_calls.discard(chat_id)
                return
        except Exception:
            try:
                await _clear_(chat_id)
                await client.leave_call(chat_id)
            except:
                pass
            self.active_calls.discard(chat_id)
            return

        queued = queue[0]["file"]
        lang = await get_lang(chat_id)
        _ = get_string(lang)
        title = queue[0]["title"].title()
        user = queue[0]["by"]
        original_chat_id = queue[0]["chat_id"]
        streamtype = queue[0]["streamtype"]
        videoid = queue[0]["vidid"]
        queue[0]["played"] = 0
        exis = queue[0].get("old_dur")
        if exis:
            queue[0]["dur"] = exis
            queue[0]["seconds"] = queue[0].get("old_second", queue[0].get("seconds"))

        is_video = (streamtype == "video")

        try:
            if "live_" in queued:
                n, link = await YouTube.video(videoid, True)
                if n == 0:
                    return await app.send_message(original_chat_id, _["call_6"])
                stream = MediaStream(link,
                                     audio_parameters=AudioQuality.HIGH,
                                     video_parameters=VideoQuality.SD_480p if is_video else None,
                                     video_flags=MediaStream.Flags.REQUIRED if is_video else MediaStream.Flags.IGNORE)
                try:
                    await client.change_stream(chat_id, stream)
                except Exception:
                    return await app.send_message(original_chat_id, _["call_6"])
                img = await get_thumb(videoid)
                button = stream_markup2(_, chat_id) if stream_markup2 else stream_markup(_, videoid, chat_id)
                run = await app.send_photo(chat_id=original_chat_id, photo=img,
                                           caption=_["stream_1"].format(
                                               f"https://t.me/{app.username}?start=info_{videoid}",
                                               title[:23], queue[0]["dur"], user),
                                           reply_markup=InlineKeyboardMarkup(button))
                queue[0]["mystic"] = run
                queue[0]["markup"] = "tg"
            elif "vid_" in queued:
                mystic = await app.send_message(original_chat_id, _["call_7"])
                try:
                    file_path, _ = await YouTube.download(videoid, mystic, videoid=True, video=is_video)
                except Exception:
                    return await mystic.edit_text(_["call_6"], disable_web_page_preview=True)
                stream = MediaStream(file_path,
                                     audio_parameters=AudioQuality.HIGH,
                                     video_parameters=VideoQuality.SD_480p if is_video else None,
                                     video_flags=MediaStream.Flags.REQUIRED if is_video else MediaStream.Flags.IGNORE)
                try:
                    await client.change_stream(chat_id, stream)
                except:
                    return await app.send_message(original_chat_id, _["call_6"])
                img = await get_thumb(videoid)
                await mystic.delete()
                button = stream_markup(_, videoid, chat_id)
                run = await app.send_photo(chat_id=original_chat_id, photo=img,
                                           caption=_["stream_1"].format(
                                               f"https://t.me/{app.username}?start=info_{videoid}",
                                               title[:23], queue[0]["dur"], user),
                                           reply_markup=InlineKeyboardMarkup(button))
                queue[0]["mystic"] = run
                queue[0]["markup"] = "stream"
            else:
                stream = MediaStream(queued,
                                     audio_parameters=AudioQuality.HIGH,
                                     video_parameters=VideoQuality.SD_480p if is_video else None,
                                     video_flags=MediaStream.Flags.REQUIRED if is_video else MediaStream.Flags.IGNORE)
                try:
                    await client.change_stream(chat_id, stream)
                except:
                    return await app.send_message(original_chat_id, _["call_6"])
                if videoid == "telegram":
                    button = stream_markup2(_, chat_id) if stream_markup2 else stream_markup(_, videoid, chat_id)
                    img = config.TELEGRAM_AUDIO_URL if streamtype == "audio" else config.TELEGRAM_VIDEO_URL
                    run = await app.send_photo(chat_id=original_chat_id, photo=img,
                                               caption=_["stream_1"].format(config.SUPPORT_CHAT,
                                                                           title[:23], queue[0]["dur"], user),
                                               reply_markup=InlineKeyboardMarkup(button))
                    queue[0]["mystic"] = run
                    queue[0]["markup"] = "tg"
                elif videoid == "soundcloud":
                    button = stream_markup2(_, chat_id) if stream_markup2 else stream_markup(_, videoid, chat_id)
                    run = await app.send_photo(chat_id=original_chat_id, photo=config.SOUNCLOUD_IMG_URL,
                                               caption=_["stream_1"].format(config.SUPPORT_CHAT,
                                                                           title[:23], queue[0]["dur"], user),
                                               reply_markup=InlineKeyboardMarkup(button))
                    queue[0]["mystic"] = run
                    queue[0]["markup"] = "tg"
                else:
                    img = await get_thumb(videoid)
                    button = stream_markup(_, videoid, chat_id)
                    try:
                        run = await app.send_photo(chat_id=original_chat_id, photo=img,
                                                   caption=_["stream_1"].format(
                                                       f"https://t.me/{app.username}?start=info_{videoid}",
                                                       title[:23], queue[0]["dur"], user),
                                                   reply_markup=InlineKeyboardMarkup(button))
                    except Exception:
                        run = None
                    queue[0]["mystic"] = run
                    queue[0]["markup"] = "stream"
        except Exception as e:
            LOGGER(__name__).error(f"Error in change_stream: {e}")
            try:
                await self.change_stream(client, chat_id)
            except Exception:
                pass

    async def ping(self):
        pings = []
        for inst in [self.one, self.two, self.three, self.four, self.five]:
            if inst:
                try:
                    pings.append(inst.ping)
                except Exception:
                    pass
        return str(round(sum(pings) / len(pings), 3)) if pings else "0.0"

    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls clients...")
        tasks = []
        for inst in [self.one, self.two, self.three, self.four, self.five]:
            if inst:
                tasks.append(inst.start())
        if tasks:
            await asyncio.gather(*tasks)
        await self.decorators()

    async def decorators(self):
        """Unified handler for StreamEnded and ChatUpdate events."""
        async def unified_update_handler(client, update: Update):
            chat_id = getattr(update, "chat_id", None)
            if not chat_id:
                chat_obj = getattr(update, "chat", None)
                if chat_obj:
                    chat_id = getattr(chat_obj, "id", None)
            if not chat_id:
                return
            if isinstance(update, StreamEnded):
                if update.stream_type == StreamEnded.Type.AUDIO:
                    try:
                        await self.change_stream(client, chat_id)
                    except Exception as e:
                        LOGGER(__name__).error(f"Error on stream end: {e}")
            elif isinstance(update, ChatUpdate):
                status = update.status
                if (status == ChatUpdate.Status.LEFT_CALL) or (status == ChatUpdate.Status.CLOSED_VOICE_CHAT) or (status == ChatUpdate.Status.KICKED):
                    await self.stop_stream(chat_id)

        for assistant in [self.one, self.two, self.three, self.four, self.five]:
            if assistant:
                assistant.on_update()(unified_update_handler)

Hotty = Call()
