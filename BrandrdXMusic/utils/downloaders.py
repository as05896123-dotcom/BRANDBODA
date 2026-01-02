import os
from yt_dlp import YoutubeDL
from BrandrdXMusic import LOGGER

def audio_dl(url: str) -> str:
    # التحقق من الكوكيز
    if os.path.isfile("cookies/cookies.txt"):
        active_cookie = "cookies/cookies.txt"
    elif os.path.isfile("cookies/BrandrdXMusic.txt"):
        active_cookie = "cookies/BrandrdXMusic.txt"
    else:
        active_cookie = None
        # لن نوقف العملية، لكن سننبه فقط
    
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "geo_bypass": True,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
        "cookiefile": active_cookie,
        "source_address": "0.0.0.0",
        # إعدادات التحويل لـ MP3
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192", # 192 كافية جداً للبوتات وأسرع من 320
            }
        ],
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            # استخراج المعلومات أولاً بدون تحميل
            info = ydl.extract_info(url, download=False)
            
            # تحديد المسار النهائي المتوقع
            file_path = os.path.join("downloads", f"{info['id']}.mp3")
            
            # إذا كان الملف موجوداً بالفعل، لا داعي لإعادة التحميل
            if os.path.exists(file_path):
                return file_path
            
            # البدء بالتحميل الفعلي
            ydl.download([url])
            return file_path
            
    except Exception as e:
        LOGGER(__name__).error(f"فشل تحميل وتحويل الصوت: {e}")
        return None
