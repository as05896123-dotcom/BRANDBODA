import os
import yt_dlp
from BrandrdXMusic import LOGGER

def download(url: str, my_hook) -> str:
    # البحث عن ملف الكوكيز (جربنا الاسمين لضمان العمل)
    if os.path.isfile("cookies/cookies.txt"):
        active_cookie = "cookies/cookies.txt"
    elif os.path.isfile("cookies/BrandrdXMusic.txt"):
        active_cookie = "cookies/BrandrdXMusic.txt"
    else:
        active_cookie = None
        LOGGER(__name__).warning("لم يتم العثور على ملف الكوكيز. قد تفشل بعض روابط يوتيوب.")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "geo_bypass": True,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
        "cookiefile": active_cookie,
        "source_address": "0.0.0.0", # يساعد في تجنب مشاكل الآي بي
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.add_progress_hook(my_hook)
            
            # بـدء عـمـلـيـة الـتـحـمـيـل
            info = ydl.extract_info(url, download=True)
            
            # إرجـاع الـمـسـار الـحـقـيـقـي لـلـمـلـف
            return ydl.prepare_filename(info)
            
    except Exception as e:
        LOGGER(__name__).error(f"فشل التحميل عبر Yt-Dlp: {e}")
        return None
