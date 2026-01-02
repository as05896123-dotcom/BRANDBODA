import os
from yt_dlp import YoutubeDL

# تـحـديـد مـسـار مـلـف الـكـوكـيـز
cookie_path = "cookies/BrandedXMusic.txt"

# الـتـحـقـق مـن وجـود الـمـلـف لـضـمـان الـعـمـل
if os.path.isfile(cookie_path):
    active_cookie = cookie_path
else:
    active_cookie = None
    print(f"تـنـبـيـه: مـلـف الـكـوكـيـز غـيـر مـوجـود فـي: {cookie_path}")

ydl_opts = {
    "format": "bestaudio/best",
    "outtmpl": "downloads/%(id)s.%(ext)s",
    "geo_bypass": True,
    "nocheckcertificate": True,
    "quiet": True,
    "no_warnings": True,
    "cookiefile": active_cookie,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "320",
        }
    ],
}

def audio_dl(url: str) -> str:
    # تـشـغـيـل الأداة مـع الإعـدادات الـمـحـدثـة
    with YoutubeDL(ydl_opts) as ydl:
        # جـلـب الـمـعـلـومـات فـقـط لـلـتـأكـد مـن الاسـم
        sin = ydl.extract_info(url, download=False)
        
        # تـحـديـد الـمـسـار الـنـهـائـي بـعـد الـتـحـويـل
        x_file = os.path.join("downloads", f"{sin['id']}.mp3")
        
        # إذا كـان الـمـلـف مـوجـوداً مـسـبـقـاً نـرجـعـه مـبـاشـرة
        if os.path.exists(x_file):
            return x_file
            
        # بـدء الـتـحـمـيـل والـتـحـويـل إلـى mp3
        ydl.download([url])
        return x_file
