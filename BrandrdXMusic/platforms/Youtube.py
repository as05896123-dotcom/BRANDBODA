import asyncio
import os
import re
from typing import Union
import yt_dlp
import aiohttp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch
from BrandrdXMusic.utils.formatters import time_to_seconds
from BrandrdXMusic import LOGGER

# --- إعدادات المجلد ---
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- إعدادات الـ API ---
YOUR_API_URL = None
FALLBACK_API_URL = "https://shrutibots.site"

async def load_api_url():
    global YOUR_API_URL
    logger = LOGGER("BrandrdXMusic.platforms.Youtube.py")
    
    try:
        async with aiohttp.ClientSession() as session:
            # محاولة جلب رابط الـ API الأساسي
            async with session.get("https://pastebin.com/raw/rLsBhAQa", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    content = await response.text()
                    YOUR_API_URL = content.strip()
                    logger.info("API URL loaded successfully")
                else:
                    YOUR_API_URL = FALLBACK_API_URL
                    logger.info("Using fallback API URL (Status != 200)")
    except Exception:
        YOUR_API_URL = FALLBACK_API_URL
        logger.info("Using fallback API URL (Exception)")

# تشغيل دالة تحميل الـ API عند بدء التشغيل
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(load_api_url())
    else:
        loop.run_until_complete(load_api_url())
except RuntimeError:
    pass


# --- دوال التحميل المحلية (YT-DLP) ---

async def download_song_ytdlp(link: str) -> Union[str, None]:
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            video_id = info.get("id")

        file_path = f"{DOWNLOAD_DIR}/{video_id}.mp3"
        if os.path.exists(file_path):
            return file_path
        return None

    except Exception as e:
        LOGGER(__name__).error(f"yt-dlp audio error: {e}")
        return None


async def download_video_ytdlp(link: str) -> Union[str, None]:
    try:
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "merge_output_format": "mp4",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            video_id = info.get("id")
            ext = info.get("ext", "mp4")

        file_path = f"{DOWNLOAD_DIR}/{video_id}.{ext}"
        if os.path.exists(file_path):
            return file_path
        return None

    except Exception as e:
        LOGGER(__name__).error(f"yt-dlp video error: {e}")
        return None


# --- دوال التحميل الهجينة (API + Fallback) ---

async def download_song(link: str) -> str:
    global YOUR_API_URL
    
    # 1. محاولة التحميل عبر الـ API
    if not YOUR_API_URL:
        await load_api_url()
        if not YOUR_API_URL:
            YOUR_API_URL = FALLBACK_API_URL
    
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link

    if not video_id or len(video_id) < 3:
        return await download_song_ytdlp(link) # Fallback immediately

    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")

    # لو الملف موجود بالفعل، لا داعي لإعادة تحميله
    if os.path.exists(file_path):
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            params = {"url": video_id, "type": "audio"}
            
            async with session.get(
                f"{YOUR_API_URL}/download",
                params=params,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    download_token = data.get("download_token")
                    
                    if download_token:
                        stream_url = f"{YOUR_API_URL}/stream/{video_id}?type=audio&token={download_token}"
                        
                        async with session.get(
                            stream_url,
                            timeout=aiohttp.ClientTimeout(total=300)
                        ) as file_response:
                            if file_response.status == 302:
                                redirect_url = file_response.headers.get('Location')
                                if redirect_url:
                                    async with session.get(redirect_url) as final_response:
                                        if final_response.status == 200:
                                            with open(file_path, "wb") as f:
                                                async for chunk in final_response.content.iter_chunked(16384):
                                                    f.write(chunk)
                                            return file_path
                            elif file_response.status == 200:
                                with open(file_path, "wb") as f:
                                    async for chunk in file_response.content.iter_chunked(16384):
                                        f.write(chunk)
                                return file_path
    except Exception:
        pass

    # 2. إذا فشل الـ API، نستخدم yt-dlp المحلي (Fallback)
    return await download_song_ytdlp(link)


async def download_video(link: str) -> str:
    global YOUR_API_URL
    
    # 1. محاولة التحميل عبر الـ API
    if not YOUR_API_URL:
        await load_api_url()
        if not YOUR_API_URL:
            YOUR_API_URL = FALLBACK_API_URL
    
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link

    if not video_id or len(video_id) < 3:
        return await download_video_ytdlp(link)

    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")

    if os.path.exists(file_path):
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            params = {"url": video_id, "type": "video"}
            
            async with session.get(
                f"{YOUR_API_URL}/download",
                params=params,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    download_token = data.get("download_token")
                    
                    if download_token:
                        stream_url = f"{YOUR_API_URL}/stream/{video_id}?type=video&token={download_token}"
                        
                        async with session.get(
                            stream_url,
                            timeout=aiohttp.ClientTimeout(total=600)
                        ) as file_response:
                            if file_response.status == 302:
                                redirect_url = file_response.headers.get('Location')
                                if redirect_url:
                                    async with session.get(redirect_url) as final_response:
                                        if final_response.status == 200:
                                            with open(file_path, "wb") as f:
                                                async for chunk in final_response.content.iter_chunked(16384):
                                                    f.write(chunk)
                                            return file_path
                            elif file_response.status == 200:
                                with open(file_path, "wb") as f:
                                    async for chunk in file_response.content.iter_chunked(16384):
                                        f.write(chunk)
                                return file_path
    except Exception:
        pass

    # 2. إذا فشل الـ API، نستخدم yt-dlp المحلي (Fallback)
    return await download_video_ytdlp(link)


# --- دوال المساعدة ---

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


# --- كلاس YouTubeAPI الأساسي ---

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
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
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"]
            vidid = result["id"]
            duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["duration"]

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["thumbnails"][0]["url"]

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        
        # استخدام دالة التحميل الهجينة (API ثم Fallback)
        downloaded_file = await download_video(link)
        if downloaded_file:
            return 1, downloaded_file
        else:
            return 0, "Video download failed"

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        # استخدام yt-dlp للتعامل مع قوائم التشغيل
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
        )
        try:
            result = [key for key in playlist.split("\n") if key]
        except:
            result = []
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"]
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            try:
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
                    except:
                        continue
            except Exception as e:
                print(f"Formats Error: {e}")
                return [], link
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        
        if not result or query_type >= len(result):
            return None, None, None, None
            
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"]
        return title, duration_min, thumbnail, vidid

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
        if videoid:
            link = self.base + link

        # استخدام دوال التحميل الهجينة
        if video:
            downloaded_file = await download_video(link)
        else:
            downloaded_file = await download_song(link)
        
        if downloaded_file:
            return downloaded_file, True
        else:
            return None, False
