import asyncio
import os
import re
import logging
import aiohttp
import yt_dlp
from typing import Union, Optional, Tuple

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch
from BrandrdXMusic.utils.formatters import time_to_seconds
from BrandrdXMusic import LOGGER

# =======================================================================
# 🔧 المعالج الذكي (Smart Handler) لإصلاح أخطاء الاتصال والمكتبات
# وظيفته: إجبار المكتبات على التعرف على Chat ID لتفادي الـ Crash
# =======================================================================
try:
    from pytgcalls.types import Update
    # محاولة إضافة خاصية chat_id يدوياً لو كانت ناقصة
    if not hasattr(Update, "chat_id"):
        @property
        def chat_id_patch(self):
            return self.chat.id if hasattr(self, "chat") else getattr(self, "chat_id", None)
        setattr(Update, "chat_id", chat_id_patch)
except ImportError:
    pass
except Exception as e:
    logging.error(f"Failed to patch Update object: {e}")

# =======================================================================
# 🌐 إعدادات API التحميل (Fallbacks)
# =======================================================================
YOUR_API_URL = None
FALLBACK_API_URL = "https://shrutibots.site"

async def load_api_url():
    global YOUR_API_URL
    logger = LOGGER("BrandrdXMusic.platforms.Youtube.py")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://pastebin.com/raw/rLsBhAQa", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    content = await response.text()
                    YOUR_API_URL = content.strip()
                    logger.info("API URL loaded successfully")
                else:
                    YOUR_API_URL = FALLBACK_API_URL
                    logger.info("Using fallback API URL")
    except Exception:
        YOUR_API_URL = FALLBACK_API_URL
        logger.info("Using fallback API URL (Error in loading)")

# تشغيل الـ Loop مرة واحدة عند البدء
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(load_api_url())
    else:
        loop.run_until_complete(load_api_url())
except RuntimeError:
    pass

# =======================================================================
# 📥 دوال التحميل (Download Functions)
# =======================================================================

async def download_song(link: str) -> str:
    global YOUR_API_URL
    if not YOUR_API_URL:
        await load_api_url()
    
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link
    if not video_id or len(video_id) < 3: return None

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")

    if os.path.exists(file_path): return file_path

    try:
        async with aiohttp.ClientSession() as session:
            params = {"url": video_id, "type": "audio"}
            async with session.get(f"{YOUR_API_URL}/download", params=params, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status != 200: return None
                data = await response.json()
                download_token = data.get("download_token")
                if not download_token: return None
                
                stream_url = f"{YOUR_API_URL}/stream/{video_id}?type=audio&token={download_token}"
                async with session.get(stream_url, timeout=aiohttp.ClientTimeout(total=300)) as file_response:
                    if file_response.status in [200, 302]:
                        redirect_url = file_response.headers.get('Location') if file_response.status == 302 else None
                        target_url = redirect_url if redirect_url else stream_url
                        
                        async with session.get(target_url) as final_response:
                            if final_response.status != 200: return None
                            with open(file_path, "wb") as f:
                                async for chunk in final_response.content.iter_chunked(16384):
                                    f.write(chunk)
                            return file_path
                    return None
    except Exception:
        return None

async def download_video(link: str) -> str:
    global YOUR_API_URL
    if not YOUR_API_URL:
        await load_api_url()
    
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link
    if not video_id or len(video_id) < 3: return None

    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")

    if os.path.exists(file_path): return file_path

    try:
        async with aiohttp.ClientSession() as session:
            params = {"url": video_id, "type": "video"}
            async with session.get(f"{YOUR_API_URL}/download", params=params, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status != 200: return None
                data = await response.json()
                download_token = data.get("download_token")
                if not download_token: return None
                
                stream_url = f"{YOUR_API_URL}/stream/{video_id}?type=video&token={download_token}"
                async with session.get(stream_url, timeout=aiohttp.ClientTimeout(total=600)) as file_response:
                    if file_response.status in [200, 302]:
                        redirect_url = file_response.headers.get('Location') if file_response.status == 302 else None
                        target_url = redirect_url if redirect_url else stream_url
                        
                        async with session.get(target_url) as final_response:
                            if final_response.status != 200: return None
                            with open(file_path, "wb") as f:
                                async for chunk in final_response.content.iter_chunked(16384):
                                    f.write(chunk)
                            return file_path
                    return None
    except Exception:
        return None

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")

# =======================================================================
# 🧠 كلاس اليوتيوب الأساسي (YouTube API)
# =======================================================================

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset: entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]
        try:
            results = VideosSearch(link, limit=1)
            for result in (await results.next())["result"]:
                title = result["title"]
                duration_min = result["duration"]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                vidid = result["id"]
                duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
                return title, duration_min, duration_sec, thumbnail, vidid
        except Exception as e:
            # معالج ذكي للخطأ: بدل الكراش يرجع قيم افتراضية أو يرفع خطأ بسيط
            LOGGER(__name__).warning(f"Details fetch failed: {e}")
            return None

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]
        try:
            results = VideosSearch(link, limit=1)
            for result in (await results.next())["result"]:
                return result["title"]
        except Exception: return None

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]
        try:
            results = VideosSearch(link, limit=1)
            for result in (await results.next())["result"]:
                return result["duration"]
        except Exception: return None

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]
        try:
            results = VideosSearch(link, limit=1)
            for result in (await results.next())["result"]:
                return result["thumbnails"][0]["url"].split("?")[0]
        except Exception: return None

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]
        try:
            downloaded_file = await download_video(link)
            if downloaded_file:
                return 1, downloaded_file
            else:
                return 0, "Video download failed"
        except Exception as e:
            return 0, f"Video download error: {e}"

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid: link = self.listbase + link
        if "&" in link: link = link.split("&")[0]
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
        )
        try: result = [key for key in playlist.split("\n") if key]
        except: result = []
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]
        try:
            results = VideosSearch(link, limit=1)
            for result in (await results.next())["result"]:
                title = result["title"]
                duration_min = result["duration"]
                vidid = result["id"]
                yturl = result["link"]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                track_details = {
                    "title": title,
                    "link": yturl,
                    "vidid": vidid,
                    "duration_min": duration_min,
                    "thumb": thumbnail,
                }
                return track_details, vidid
        except Exception as e:
            LOGGER(__name__).error(f"Track fetch error: {e}")
            return None, None

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]
        ytdl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        try:
            with ydl:
                formats_available = []
                r = ydl.extract_info(link, download=False)
                for format in r["formats"]:
                    try:
                        if "dash" not in str(format["format"]).lower():
                            formats_available.append(
                                {
                                    "format": format["format"],
                                    "filesize": format.get("filesize"),
                                    "format_id": format["format_id"],
                                    "ext": format["ext"],
                                    "format_note": format["format_note"],
                                    "yturl": link,
                                }
                            )
                    except: continue
            return formats_available, link
        except Exception: return [], link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]
        try:
            a = VideosSearch(link, limit=10)
            result = (await a.next()).get("result")
            if not result or len(result) <= query_type:
                 raise ValueError("Slider index out of range")
            title = result[query_type]["title"]
            duration_min = result[query_type]["duration"]
            vidid = result[query_type]["id"]
            thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
            return title, duration_min, thumbnail, vidid
        except Exception as e:
             LOGGER(__name__).warning(f"Slider fetch error: {e}")
             return None

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid: link = self.base + link

        try:
            if video: downloaded_file = await download_video(link)
            else: downloaded_file = await download_song(link)
            
            if downloaded_file: return downloaded_file, True
            else: return None, False
        except Exception: return None, False
