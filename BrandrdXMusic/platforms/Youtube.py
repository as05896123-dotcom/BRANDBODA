"""
███████╗██╗   ██╗███████╗████████╗███████╗███╗   ███╗
██╔════╝╚██╗ ██╔╝██╔════╝╚══██╔══╝██╔════╝████╗ ████║
███████╗ ╚████╔╝ ███████╗   ██║   █████╗  ██╔████╔██║
╚════██║  ╚██╔╝  ╚════██║   ██║   ██╔══╝  ██║╚██╔╝██║
███████║   ██║   ███████║   ██║   ███████╗██║ ╚═╝ ██║
╚══════╝   ╚═╝   ╚══════╝   ╚═╝   ╚══════╝╚═╝     ╚═╝

[النظام: التناغم التام - Harmonized Relay]
[الآلية: تسليم الراية (Waterfall Strategy)]
[الميزة: لا تضارب، لا ملفات تالفة، أقصى سرعة]
"""

import asyncio
import os
import re
import json
import random
import logging
import time
import shutil
import ssl
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from typing import Union

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch

# =======================================================================
# 🩹 1. باتش الحماية (Anti-Crash Patch)
# =======================================================================
try:
    from pytgcalls import types as pt
    def get_chat_id_safe(self):
        if hasattr(self, 'chat') and hasattr(self.chat, 'id'): return self.chat.id
        return 0
    for name in dir(pt):
        obj = getattr(pt, name)
        if isinstance(obj, type) and "Update" in name:
            if not hasattr(obj, "chat_id"):
                setattr(obj, "chat_id", property(get_chat_id_safe))
except: pass

# =======================================================================
# ⚙️ 2. الإعدادات
# =======================================================================
try:
    from BrandrdXMusic.utils.database import is_on_off
    from BrandrdXMusic.utils.formatters import time_to_seconds
    from BrandrdXMusic import LOGGER
except ImportError:
    logging.basicConfig(level=logging.ERROR)
    def LOGGER(name): return logging.getLogger(name)
    async def is_on_off(x): return True
    def time_to_seconds(t): return 0

سجل = LOGGER("Harmony_Core")
logging.getLogger("yt_dlp").setLevel(logging.ERROR)

class Config:
    DOWNLOAD_PATH = "downloads"
    MAX_WORKERS = 10
    SERVERS = [
        {"url": "https://shrutibots.site", "weight": 10},
        {"url": "https://myapi-i-bwca.fly.dev", "weight": 100},
    ]

if not os.path.exists(Config.DOWNLOAD_PATH):
    os.makedirs(Config.DOWNLOAD_PATH)

# =======================================================================
# 🛠️ 3. الأدوات
# =======================================================================
def get_cookie():
    if os.path.exists("cookies.txt"): return "cookies.txt"
    if os.path.exists("cookies"):
        files = [f for f in os.listdir("cookies") if f.endswith(".txt")]
        if files: return os.path.join("cookies", random.choice(files))
    return None

def clean_file(path):
    """تنظيف الملف التالف فوراً لإفساح الطريق للمحرك التالي"""
    try:
        if os.path.exists(path): os.remove(path)
        # تنظيف ملفات التجزئة الخاصة بـ Aria2
        if os.path.exists(path + ".aria2"): os.remove(path + ".aria2")
        if os.path.exists(path + ".part"): os.remove(path + ".part")
    except: pass

# =======================================================================
# 🚀 4. الكلاس الرئيسي
# =======================================================================
class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="
        self.pool = ThreadPoolExecutor(max_workers=Config.MAX_WORKERS)
        self.has_aria2 = os.system("which aria2c > /dev/null 2>&1") == 0
        
        # تنظيف قديم عند البدء
        try:
            for f in os.listdir(Config.DOWNLOAD_PATH):
                if os.stat(os.path.join(Config.DOWNLOAD_PATH, f)).st_mtime < time.time() - 3600:
                    os.remove(os.path.join(Config.DOWNLOAD_PATH, f))
        except: pass

    # -----------------------------------------------------------------
    # 🔍 محرك البحث (ثابت ومستقر)
    # -----------------------------------------------------------------
    async def track(self, link: str, videoid: bool = False):
        if videoid: link = self.base + link
        link = link.split("&")[0]

        # نعتمد على VideosSearch لأنه الأسرع والأدق حالياً
        try:
            s = VideosSearch(link, limit=1)
            r = (await s.next())["result"][0]
            return {
                "title": r["title"], "link": r["link"], "vidid": r["id"],
                "duration_min": r["duration"], "thumb": r["thumbnails"][0]["url"].split("?")[0],
                "cookiefile": get_cookie()
            }, r["id"]
        except:
            return {"title": "Error", "link": link, "vidid": "error", "duration_min": "0:00", "thumb": ""}, "error"

    # -----------------------------------------------------------------
    # 📥 محرك التحميل المتناغم (Harmonized Relay Downloader)
    # -----------------------------------------------------------------
    async def download(self, link: str, mystic, video: bool = False, videoid: bool = False, songaudio: bool = False, songvideo: bool = False, format_id: str = None, title: str = None) -> str:
        
        if videoid: link = self.base + link
        loop = asyncio.get_running_loop()
        
        if "v=" in link: vid_id = link.split("v=")[1].split("&")[0]
        elif "youtu.be/" in link: vid_id = link.split("youtu.be/")[1].split("?")[0]
        else: vid_id = str(int(time.time()))

        safe_title = re.sub(r'[\\/*?:"<>|]', "", title if title else vid_id)
        ext = "mp4" if (video or songvideo) else "mp3"
        final_path = os.path.join(Config.DOWNLOAD_PATH, f"{safe_title}.{ext}")

        # 1. مرحلة الكاش (توفير الوقت)
        if os.path.exists(final_path) and os.path.getsize(final_path) > 50000:
            return final_path, True

        # تحديد نوع المهمة
        is_video_task = video or songvideo
        
        # =======================================================
        # 🏁 المرحلة الأولى: التيربو (Aria2c)
        # =======================================================
        # يحاول التحميل بأقصى سرعة. لو فشل، ينسحب بهدوء.
        if self.has_aria2:
            try:
                # سجل.info("Pass 1: Aria2 Turbo...")
                res = await loop.run_in_executor(
                    self.pool, 
                    lambda: self._attempt_download(link, final_path, is_video_task, format_id, use_aria2=True)
                )
                if res: return res, True
            except:
                # تنظيف مكان Aria2 عشان المحرك اللي بعده ميتلخبطش
                clean_file(final_path)

        # =======================================================
        # 🛡️ المرحلة الثانية: المحرك الأصلي (Native yt-dlp)
        # =======================================================
        # ده "الحصان الأسود"، بيحل مشاكل Error 24 وتصاريح يوتيوب المعقدة
        try:
            # سجل.info("Pass 2: Native Fallback...")
            res = await loop.run_in_executor(
                self.pool, 
                lambda: self._attempt_download(link, final_path, is_video_task, format_id, use_aria2=False)
            )
            if res: return res, True
        except:
            clean_file(final_path)

        # =======================================================
        # ☁️ المرحلة الثالثة: السحابة (API Backup)
        # =======================================================
        # لو الـ IP بتاعك محظور، نستخدم سيرفر خارجي
        if not (songaudio or songvideo): # الـ API مش بيدعم الصيغ المخصصة
            try:
                # سجل.info("Pass 3: Cloud API...")
                res = await self._attempt_api(link, vid_id, final_path, video)
                if res: return res, True
            except:
                clean_file(final_path)

        return None, False

    # -----------------------------------------------------------------
    # 🔧 التروس الداخلية (Logic)
    # -----------------------------------------------------------------
    def _attempt_download(self, link, path, is_video, fmt_id, use_aria2):
        """دالة موحدة للتحميل (محلي/تيربو)"""
        
        # إعدادات أساسية
        opts = {
            "outtmpl": path,
            "cookiefile": get_cookie(),
            "geo_bypass": True, "nocheckcertificate": True,
            "quiet": True, "no_warnings": True,
            "socket_timeout": 10,
        }

        # تفعيل Aria2 لو مطلوب
        if use_aria2:
            opts.update({
                "external_downloader": "aria2c",
                "external_downloader_args": ["-x", "16", "-s", "16", "-k", "1M", "--file-allocation=none"]
            })

        # ضبط الصيغ
        if is_video:
            if fmt_id:
                 opts["format"] = f"{fmt_id}+140"
            else:
                 opts["format"] = "bestvideo[height<=720]+bestaudio/best[height<=720]"
            opts["merge_output_format"] = "mp4"
        else:
            opts["format"] = fmt_id or "bestaudio/best"
            opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]

        # التنفيذ
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([link])
            
            if os.path.exists(path) and os.path.getsize(path) > 1024:
                return path
        except Exception:
            return None # فشل، ارجع عشان اللي بعدك يشتغل
        return None

    async def _attempt_api(self, link, vid_id, path, is_video):
        """دالة التحميل من السحابة"""
        ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
        
        # اختيار السيرفر
        url = None
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ctx)) as s:
            for srv in sorted(Config.SERVERS, key=lambda x: x["weight"], reverse=True):
                try:
                    async with s.head(srv["url"], timeout=2) as r:
                        if r.status < 500: 
                            url = srv["url"]; break
                except: continue
        
        if not url: return None

        # التحميل
        t = "video" if is_video else "audio"
        is_priv = "fly.dev" in url
        q = link if is_priv else vid_id
        
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ctx)) as s:
            async with s.get(f"{url}/download", params={"url": q, "type": t}, timeout=10) as r:
                if r.status != 200: return None
                d = await r.json()
                dl_url = d.get("url")
                if not dl_url and not is_priv:
                    tok = d.get("download_token")
                    if tok: dl_url = f"{url}/stream/{q}?type={t}&token={tok}"
                
                if not dl_url: return None

                # استخدام Stream عادي عشان نتجنب مشاكل Aria2 مع الروابط المؤقتة
                async with s.get(dl_url, timeout=600) as stream:
                    if stream.status == 200:
                        with open(path, "wb") as f:
                            async for chunk in stream.content.iter_chunked(65536):
                                f.write(chunk)
                        return path
        return None

    # -----------------------------------------------------------------
    # 📡 Metadata Utils (متوافقة)
    # -----------------------------------------------------------------
    async def url(self, message: Message) -> Union[str, None]:
        msgs = [message]
        if message.reply_to_message: msgs.append(message.reply_to_message)
        for m in msgs:
            txt = m.text or m.caption
            if not txt: continue
            if m.entities:
                for e in m.entities:
                    if e.type == MessageEntityType.URL: return txt[e.offset:e.offset+e.length]
            match = re.search(self.regex, txt)
            if match: return match.group(0)
        return None

    async def details(self, link: str, videoid: bool = None):
        d, i = await self.track(link, videoid)
        if i == "error": return None
        return d["title"], d["duration_min"], time_to_seconds(d["duration_min"]), d["thumb"], i

    async def title(self, link: str, videoid: bool = None):
        d, _ = await self.track(link, videoid)
        return d.get("title")

    async def duration(self, link: str, videoid: bool = None):
        d, _ = await self.track(link, videoid)
        return d.get("duration_min")

    async def thumbnail(self, link: str, videoid: bool = None):
        d, _ = await self.track(link, videoid)
        return d.get("thumb")

    async def video(self, link: str, videoid: bool = None):
        if videoid: link = self.base + link
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "--cookies", get_cookie() or "", "-g", "-f", "best[height<=?720]", link,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        return (1, stdout.decode().split("\n")[0]) if stdout else (0, "Fail")

    async def playlist(self, link, limit, user_id, videoid: bool = None):
        if videoid: link = self.listbase + link
        cmd = ["yt-dlp", "-i", "--flat-playlist", "--print", "id", "--playlist-end", str(limit), "--skip-download", link]
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        out, _ = await proc.communicate()
        return [x for x in out.decode().split("\n") if x]

    async def formats(self, link: str, videoid: bool = None): return [], link
    
    async def slider(self, link: str, query_type: int, videoid: bool = None):
        if videoid: link = self.base + link
        a = VideosSearch(link, limit=10)
        res = (await a.next()).get("result")[query_type]
        return res["title"], res["duration"], res["thumbnails"][0]["url"].split("?")[0], res["id"]

# =======================================================================
# 🏁 التصدير
# =======================================================================
YouTube = YouTubeAPI()
