import os
import re
import asyncio
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from youtubesearchpython.__future__ import VideosSearch
from config import YOUTUBE_IMG_URL

# ==========================================
# 🛑 الإحداثيات (مظبوطة لتظهر فوق القالب)
# ==========================================
CIRCLE_X = 175; CIRCLE_Y = 160
IMG_W = 355; IMG_H = 355

NAME_X = 735; NAME_Y = 190          
BY_X = 670; BY_Y = 255
VIEWS_X = 731; VIEWS_Y = 310        
TIME_START_X = 580; TIME_END_X = 1055; TIME_Y = 368 
# ==========================================

if hasattr(Image, "Resampling"):
    LANCZOS = Image.Resampling.LANCZOS
else:
    LANCZOS = Image.LANCZOS

def get_font(size):
    possible_fonts = ["BrandrdXMusic/assets/font.ttf", "assets/font.ttf", "font.ttf"]
    for font_path in possible_fonts:
        if os.path.isfile(font_path): return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()

def truncate_text(draw, text, font, max_width):
    try: w = draw.textlength(text, font=font)
    except: w = draw.textsize(text, font=font)[0]
    if w <= max_width: return text
    for i in range(len(text), 0, -1):
        if draw.textlength(text[:i] + "...", font=font) <= max_width: return text[:i] + "..."
    return "..."

def format_views(views):
    try:
        v = str(views).lower().replace("views","").strip()
        if "m" in v or "k" in v: return v.upper()
        val = int(re.sub(r'\D', '', v))
        return f"{val/1_000_000:.1f}M" if val >= 1e6 else (f"{val/1_000:.1f}K" if val >= 1e3 else str(val))
    except: return str(views)

def draw_text_with_shadow(draw, pos, text, font, fill="white", shadow="black"):
    x, y = pos
    draw.text((x+2, y+2), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=fill)

# ============================================================
# 🎨 الرسام (بيحط الصورة غصب فوق القالب)
# ============================================================
async def draw_thumb(thumbnail_path, title, userid, theme, duration, views, videoid):
    try:
        # ضمان البيانات (Anti-TypeError)
        title = str(title or "Unknown Track")
        userid = str(userid or "Unknown Artist")
        views = str(views or "0")
        duration = str(duration or "00:00")

        # 1. الخلفية
        try: source = Image.open(thumbnail_path).convert("RGBA")
        except: source = Image.new('RGBA', (1280, 720), (30, 30, 30))
        
        background = source.resize((1280, 720), resample=LANCZOS)
        background = background.filter(ImageFilter.GaussianBlur(3))
        background = Image.alpha_composite(background, Image.new('RGBA', (1280, 720), (0,0,0,100)))

        # 2. القالب (Overlay) - بيتحط تحت عشان الصورة تغطيه
        if os.path.isfile("BrandrdXMusic/assets/overlay.png"):
            try:
                ov = Image.open("BrandrdXMusic/assets/overlay.png").convert("RGBA")
                background.paste(ov.resize((1280, 720), resample=LANCZOS), (0, 0), ov)
            except: pass

        # 3. الصورة الدائرية (الأهم)
        try:
            big_w, big_h = IMG_W*3, IMG_H*3
            # بنستخدم الـ source اللي هو صورة الأغنية الأصلية
            art = ImageOps.fit(source, (big_w, big_h), centering=(0.5, 0.5), method=LANCZOS)
            mask = Image.new('L', (big_w, big_h), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, big_w, big_h), fill=255)
            
            art = art.resize((IMG_W, IMG_H), resample=LANCZOS)
            mask = mask.resize((IMG_W, IMG_H), resample=LANCZOS)
            
            # اللصق
            background.paste(art, (CIRCLE_X, CIRCLE_Y), mask)
        except Exception as e:
            print(f"Circle Error: {e}")

        # 4. الكتابة
        d = ImageDraw.Draw(background)
        ft, fi, ftm = get_font(40), get_font(30), get_font(26)
        
        draw_text_with_shadow(d, (NAME_X, NAME_Y), truncate_text(d, title, ft, 460), ft)
        draw_text_with_shadow(d, (BY_X, BY_Y), truncate_text(d, userid, fi, 400), fi, "#dddddd")
        draw_text_with_shadow(d, (VIEWS_X, VIEWS_Y), format_views(views), fi, "#aaaaaa")
        draw_text_with_shadow(d, (TIME_START_X, TIME_Y), "00:00", ftm)
        draw_text_with_shadow(d, (TIME_END_X, TIME_Y), duration, ftm)

        out = f"cache/{videoid}_final.png"
        background.save(out)
        return out
    except Exception as e:
        print(f"Draw Error: {e}")
        return thumbnail_path

# ============================================================
# 🕵️‍♂️ الصياد (الذكاء والتحميل)
# ============================================================
async def gen_thumb(videoid, user_id=None):
    if not os.path.exists("cache"): os.makedirs("cache")
    if os.path.isfile(f"cache/{videoid}_final.png"): return f"cache/{videoid}_final.png"

    temp_path = f"cache/temp_{videoid}.png"
    url = f"https://www.youtube.com/watch?v={videoid}"

    try:
        # جلب المعلومات مرة واحدة
        search = VideosSearch(url, limit=1)
        res = (await search.next())["result"][0]
        
        # تجهيز البيانات
        title = res.get("title", "Unknown")
        title = re.sub(r"\W+", " ", title).title()
        duration = res.get("duration", "00:00")
        views = res.get("viewCount", {}).get("short", "0")
        channel = res.get("channel", {}).get("name", "Unknown Artist")
        
        # 🧠 الذكاء هنا: قائمة روابط محتملة للصورة من الأفضل للأسوأ
        # الروابط المباشرة لليوتيوب أسرع وأدق من البحث
        candidate_urls = [
            f"https://img.youtube.com/vi/{videoid}/maxresdefault.jpg", # جودة خرافية
            f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg",     # جودة عالية
            f"https://img.youtube.com/vi/{videoid}/sddefault.jpg",     # جودة متوسطة
        ]
        # نضيف رابط البحث كخيار أخير
        if res.get("thumbnails"):
            candidate_urls.append(res["thumbnails"][-1]["url"])

        # 🔄 حلقة المحاولات (Retry Loop)
        success_download = False
        async with aiohttp.ClientSession() as session:
            for thumb_url in candidate_urls:
                # نحاول نحمل كل رابط 3 مرات لو فشل
                for attempt in range(2): 
                    try:
                        async with session.get(thumb_url, timeout=5) as resp:
                            if resp.status == 200:
                                data = await resp.read()
                                if len(data) > 1000: # تأكد إن الملف مش فاضي
                                    async with aiofiles.open(temp_path, mode="wb") as f:
                                        await f.write(data)
                                    # اختبار إن الصورة سليمة
                                    try:
                                        Image.open(temp_path).verify()
                                        success_download = True
                                        break # نجحنا! اخرج من حلقة المحاولات
                                    except: pass # الملف نزل بس بايظ، جرب تاني
                    except:
                        await asyncio.sleep(0.5) # استنى نص ثانية وجرب تاني
                
                if success_download: break # نجحنا! اخرج من حلقة الروابط

        # لو بعد كل ده فشل، نستخدم صورة البوت مضطرين
        if not success_download:
             return YOUTUBE_IMG_URL

        # التركيب
        final = await draw_thumb(temp_path, title, channel, None, duration, views, videoid)
        
        # التنظيف
        if os.path.exists(temp_path): os.remove(temp_path)
        
        return final

    except Exception as e:
        print(f"Gen Error: {e}")
        return YOUTUBE_IMG_URL

# توحيد الأسماء
get_thumb = gen_thumb
