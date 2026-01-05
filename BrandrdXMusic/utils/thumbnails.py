import os
import re
import asyncio
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from youtubesearchpython.__future__ import VideosSearch
from config import YOUTUBE_IMG_URL

# ==========================================
# 🛑 الإحداثيات (Name, By, Views, Time)
# ==========================================
CIRCLE_X = 160; CIRCLE_Y = 146
IMG_W = 385; IMG_H = 355

NAME_X = 715; NAME_Y = 190          
BY_X = 650; BY_Y = 255
VIEWS_X = 711; VIEWS_Y = 310        
TIME_START_X = 580; TIME_END_X = 1055; TIME_Y = 368 
# ==========================================

# تحسين جودة الصورة لأقصى درجة
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

def format_views(views):
    try:
        views_str = str(views).lower().replace("views", "").replace("view", "").strip()
        if "m" in views_str or "k" in views_str:
            return views_str.upper()
        val = int(re.sub(r'\D', '', views_str))
        if val >= 1_000_000: return f"{val/1_000_000:.1f}M"
        elif val >= 1_000: return f"{val/1_000:.1f}K"
        return str(val)
    except:
        return str(views).replace("views", "").strip()

# دالة مساعدة لرسم النص بظل خفيف (عشان يظهر بوضوح)
def draw_text_with_shadow(draw, pos, text, font, fill="white", shadow_color="black"):
    x, y = pos
    # رسم الظل أولاً (مزاح قليلاً)
    draw.text((x + 2, y + 2), text, font=font, fill=shadow_color)
    # رسم النص الأصلي فوقه
    draw.text((x, y), text, font=font, fill=fill)

async def draw_thumb(thumbnail, title, userid, theme, duration, views, videoid):
    try:
        # 1. تجهيز الصورة الأساسية
        if os.path.isfile(thumbnail):
            source = Image.open(thumbnail).convert("RGBA")
        else:
            source = Image.new('RGBA', (1280, 720), (30, 30, 30))

        # 2. عمل الخلفية (تغبيش)
        background = source.resize((1280, 720), resample=LANCZOS)
        background = background.filter(ImageFilter.GaussianBlur(3)) # زيادة التغبيش لـ 3 لتركيز النظر ع المنتصف
        
        # طبقة سوداء شفافة لتقليل سطوع الخلفية
        dark_layer = Image.new('RGBA', (1280, 720), (0, 0, 0, 90)) # زودت السواد شوية عشان الكلام يوضح
        background = Image.alpha_composite(background, dark_layer)

        # 3. قص الدائرة باحترافية
        # بنعمل الصورة 3 أضعاف الحجم ثم نصغرها عشان الحواف تبقى ناعمة (Anti-aliasing Trick)
        big_w, big_h = IMG_W * 3, IMG_H * 3
        art_circle = ImageOps.fit(source, (big_w, big_h), centering=(0.5, 0.5), method=LANCZOS)
        
        mask = Image.new('L', (big_w, big_h), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, big_w, big_h), fill=255)
        
        # تصغير الدائرة للحجم المطلوب
        art_circle = art_circle.resize((IMG_W, IMG_H), resample=LANCZOS)
        mask = mask.resize((IMG_W, IMG_H), resample=LANCZOS)
        
        background.paste(art_circle, (CIRCLE_X, CIRCLE_Y), mask)

        # 4. وضع القالب (Overlay)
        overlay_path = "BrandrdXMusic/assets/overlay.png"
        if os.path.isfile(overlay_path):
            overlay = Image.open(overlay_path).convert("RGBA")
            overlay = overlay.resize((1280, 720), resample=LANCZOS)
            background.paste(overlay, (0, 0), overlay)

        # 5. الكتابة
        draw = ImageDraw.Draw(background)
        f_title = get_font(45)
        f_info = get_font(30)
        f_time = get_font(26)

        title = str(title); userid = str(userid); views = str(views); duration = str(duration)

        # العنوان (مع ظل)
        safe_title = truncate_text(draw, title, f_title, max_width=500)
        draw_text_with_shadow(draw, (NAME_X, NAME_Y), safe_title, f_title, fill="white")

        # الفنان (لون مميز)
        safe_artist = truncate_text(draw, userid, f_info, max_width=450)
        draw_text_with_shadow(draw, (BY_X, BY_Y), safe_artist, f_info, fill="#dddddd")

        # المشاهدات
        smart_views = format_views(views)
        draw_text_with_shadow(draw, (VIEWS_X, VIEWS_Y), smart_views, f_info, fill="#dddddd")

        # الوقت
        draw_text_with_shadow(draw, (TIME_START_X, TIME_Y), "00:00", f_time, fill="white")
        draw_text_with_shadow(draw, (TIME_END_X, TIME_Y), duration, f_time, fill="white")

        output = f"cache/{videoid}_final.png"
        background.save(output)
        return output
        
    except Exception as e:
        print(f"Error in draw_thumb: {e}")
        return thumbnail

async def gen_thumb(videoid, user_id=None):
    if not os.path.exists("cache"):
        os.makedirs("cache")
        
    if os.path.isfile(f"cache/{videoid}_final.png"):
        return f"cache/{videoid}_final.png"

    url = f"https://www.youtube.com/watch?v={videoid}"
    temp_path = f"cache/temp_{videoid}.png"
    
    try:
        results = VideosSearch(url, limit=1)
        res_dict = (await results.next())["result"][0]
        
        title = res_dict.get("title", "Unknown Title")
        title = re.sub(r"\W+", " ", title).title()
        
        duration = res_dict.get("duration", "00:00")
        thumbnails = res_dict.get("thumbnails", [])
        
        # اختيار أفضل صورة
        thumbnail_url = thumbnails[-1]["url"] if thumbnails else YOUTUBE_IMG_URL
        
        views = res_dict.get("viewCount", {}).get("short", "0")
        channel = res_dict.get("channel", {}).get("name", "Unknown Artist")

        # تحميل الصورة مع Timeout عشان البوت ميعلقش
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(thumbnail_url) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(temp_path, mode="wb")
                    await f.write(await resp.read())
                    await f.close()
                else:
                    return YOUTUBE_IMG_URL

        final_image = await draw_thumb(temp_path, title, channel, None, duration, views, videoid)
        return final_image

    except Exception as e:
        print(f"Error in gen_thumb: {e}")
        return YOUTUBE_IMG_URL
    finally:
        # تنظيف الملف المؤقت دائماً
        if os.path.isfile(temp_path):
            try: os.remove(temp_path)
            except: pass

# ✅ الحل السحري لمشاكل الاستيراد (ImportError)
get_thumb = gen_thumb
