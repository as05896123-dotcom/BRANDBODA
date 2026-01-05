import os
import re
import aiofiles
import aiohttp
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from youtubesearchpython.__future__ import VideosSearch
from config import YOUTUBE_IMG_URL

# ==========================================
# 🛑 الإحداثيات (مكان بداية الكلام أمام الخانات)
# ==========================================
CIRCLE_X = 160; CIRCLE_Y = 146
IMG_W = 385; IMG_H = 355

# دي الأماكن اللي هيبدأ فيها كتابة "القيمة"
NAME_X = 715; NAME_Y = 190          
BY_X = 650; BY_Y = 255
VIEWS_X = 711; VIEWS_Y = 310        

TIME_START_X = 580; TIME_END_X = 1055; TIME_Y = 368 
# ==========================================

if hasattr(Image, "Resampling"):
    LANCZOS = Image.Resampling.LANCZOS
else:
    LANCZOS = Image.LANCZOS

def get_font(size):
    possible_fonts = [
        "BrandrdXMusic/assets/font.ttf",
        "assets/font.ttf",
        "font.ttf"
    ]
    for font_path in possible_fonts:
        if os.path.isfile(font_path):
            return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()

# دالة قص النص بذكاء عشان ميبوظش التصميم
def truncate_text(draw, text, font, max_width):
    try:
        w = draw.textlength(text, font=font)
    except AttributeError:
        w = draw.textsize(text, font=font)[0]
    if w <= max_width:
        return text
    for i in range(len(text), 0, -1):
        temp_text = text[:i] + "..."
        try:
            w_temp = draw.textlength(temp_text, font=font)
        except AttributeError:
            w_temp = draw.textsize(temp_text, font=font)[0]
        if w_temp <= max_width:
            return temp_text
    return "..."

# دالة تحويل المشاهدات (1.5M - 500K)
def format_views(views):
    try:
        # لو القيمة جاية أصلاً نص وفيها حروف زي M أو K نرجعها زي ما هي بس نشيل كلمة views
        views_str = str(views).lower().replace("views", "").replace("view", "").strip()
        if "m" in views_str or "k" in views_str:
            return views_str.upper()
        
        # لو رقم خام، نحوله احنا
        val = int(re.sub(r'\D', '', views_str)) # استخراج الأرقام فقط
        
        if val >= 1_000_000:
            return f"{val/1_000_000:.1f}M"
        elif val >= 1_000:
            return f"{val/1_000:.1f}K"
        else:
            return str(val)
    except:
        return str(views).replace("views", "").strip()

async def draw_thumb(thumbnail, title, userid, theme, duration, views, videoid):
    try:
        # 1. تجهيز الصورة والبلور الخفيف
        if os.path.isfile(thumbnail):
            source = Image.open(thumbnail).convert("RGBA")
        else:
            source = Image.new('RGBA', (1280, 720), (30, 30, 30))

        background = source.resize((1280, 720), resample=LANCZOS)
        background = background.filter(ImageFilter.GaussianBlur(2)) # بلور خفيف 2
        
        dark_layer = Image.new('RGBA', (1280, 720), (0, 0, 0, 50))
        background = Image.alpha_composite(background, dark_layer)

        # 2. الدائرة
        art_circle = ImageOps.fit(source, (IMG_W, IMG_H), centering=(0.5, 0.5), method=LANCZOS)
        mask = Image.new('L', (IMG_W, IMG_H), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, IMG_W, IMG_H), fill=255)
        background.paste(art_circle, (CIRCLE_X, CIRCLE_Y), mask)

        # 3. القالب (overlay.png)
        overlay_path = "BrandrdXMusic/assets/overlay.png"
        if os.path.isfile(overlay_path):
            overlay = Image.open(overlay_path).convert("RGBA")
            overlay = overlay.resize((1280, 720), resample=LANCZOS)
            background.paste(overlay, (0, 0), overlay)

        # 4. الكتابة (تعبئة البيانات فقط)
        draw = ImageDraw.Draw(background)
        f_title = get_font(45)  # خط الاسم
        f_info = get_font(30)   # خط الفنان والمشاهدات
        f_time = get_font(26)   # خط الوقت

        # --- أ. اسم الأغنية (Title) ---
        # بنحدد أقصى عرض للنص عشان ميبوظش (مثلاً 500 بكسل من نقطة البداية)
        safe_title = truncate_text(draw, title, f_title, max_width=500)
        draw.text((NAME_X, NAME_Y), safe_title, font=f_title, fill="white")

        # --- ب. اسم الفنان (Artist / By) ---
        safe_artist = truncate_text(draw, userid, f_info, max_width=450)
        draw.text((BY_X, BY_Y), safe_artist, font=f_info, fill="#cccccc")

        # --- ج. المشاهدات (Smart Views) ---
        smart_views = format_views(views)
        draw.text((VIEWS_X, VIEWS_Y), smart_views, font=f_info, fill="#aaaaaa")

        # --- د. الوقت ---
        draw.text((TIME_START_X, TIME_Y), "00:00", font=f_time, fill="white")
        draw.text((TIME_END_X, TIME_Y), duration, font=f_time, fill="white")

        # الحفظ
        output = f"cache/{videoid}_final.png"
        background.save(output)
        return output
        
    except Exception as e:
        print(f"Error in draw_thumb: {e}")
        return thumbnail

async def get_thumb(videoid):
    if not os.path.exists("cache"):
        os.makedirs("cache")
        
    if os.path.isfile(f"cache/{videoid}_final.png"):
        return f"cache/{videoid}_final.png"

    url = f"https://www.youtube.com/watch?v={videoid}"
    try:
        results = VideosSearch(url, limit=1)
        res_dict = (await results.next())["result"][0]
        
        title = res_dict.get("title", "Unknown Title")
        title = re.sub(r"\W+", " ", title).title()
        
        duration = res_dict.get("duration", "00:00")
        
        thumbnails = res_dict.get("thumbnails", [])
        thumbnail_url = thumbnails[0]["url"] if thumbnails else YOUTUBE_IMG_URL
        if len(thumbnails) > 1:
            thumbnail_url = thumbnails[-1]["url"]

        views = res_dict.get("viewCount", {}).get("short", "0") # هنا بيجيب الرقم الخام أو المختصر
        channel = res_dict.get("channel", {}).get("name", "Unknown Artist")

        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url) as resp:
                if resp.status == 200:
                    temp_path = f"cache/temp_{videoid}.png"
                    f = await aiofiles.open(temp_path, mode="wb")
                    await f.write(await resp.read())
                    await f.close()
                else:
                    return YOUTUBE_IMG_URL

        final_image = await draw_thumb(temp_path, title, channel, None, duration, views, videoid)
        
        try: os.remove(temp_path)
        except: pass
        
        return final_image

    except Exception as e:
        print(f"Error in get_thumb: {e}")
        return YOUTUBE_IMG_URL
