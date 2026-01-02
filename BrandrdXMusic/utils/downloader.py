import os
from os import path
import yt_dlp

def download(url: str, my_hook) -> str:
    # تـحـديـد مـسـار مـلـف الـكـوكـيـز داخـل الـمـجـلـد
    cookie_path = "cookies/BrandedXMusic.txt"
    
    # الـتـحـقـق مـن وجـود الـمـلـف لـضـمـان الـعـمـل
    if os.path.isfile(cookie_path):
        active_cookie = cookie_path
    else:
        active_cookie = None
        print(f"تـنـبـيـه: لـم يـتـم الـعـثـور عـلـى الـكـوكـيـز فـي: {cookie_path}")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "geo_bypass": True,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
        "cookiefile": active_cookie,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.add_progress_hook(my_hook)
            # بـدء عـمـلـيـة الـتـحـمـيـل واسـتـخـراج الـبـيـانـات
            info = ydl.extract_info(url, download=True)
            # إرجـاع الـمـسـار الـحـقـيـقـي لـلـمـلـف الـمـحـمـل
            return ydl.prepare_filename(info)
            
    except Exception as e:
        print(f"خـطـأ أثـنـاء الـتـحـمـيـل: {e}")
        return None
