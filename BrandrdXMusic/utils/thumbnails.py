import os
import re
import asyncio
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageChops
from youtubesearchpython.__future__ import VideosSearch
from config import YOUTUBE_IMG_URL

# =========================================================
# 📍 الإحداثيات الثابتة (Final Coordinates)
# =========================================================
CIRCLE_POS = (160, 153)   
CIRCLE_SIZE = (385, 355)  

NAME_POS = (715, 190)
BY_POS = (650, 255)
VIEWS_POS = (711, 310)

TIME_START = (580, 368)
TIME_END = (1055, 368)

# =========================================================
# 🛠️ أدوات التوافق (Compatibility Helpers)
# =========================================================

# 1. حل مشكلة اختلاف إصدارات Pillow في الفلاتر
if hasattr(Image, "Resampling"):
    LANCZOS = Image.Resampling.LANCZOS
else:
    LANCZOS = Image.LANCZOS

# 2. دالة جلب الخطوط بأمان
def get_font(size):
    fonts = [
        "BrandrdXMusic/assets/font.ttf", 
        "assets/font.ttf", 
        "font.ttf"
    ]
    for font in fonts:
        if os.path.isfile(font):
            return ImageFont.truetype(font, size)
    return ImageFont.load_default()

# 3. قص النصوص بأمان (يدعم كل إصدارات Pillow)
def smart_truncate(draw, text, font, max_width):
    text = str(text) # تأمين النوع
    try:
        # للإصدارات الجديدة
        w = draw.textlength(text, font=font)
    except:
        # للإصدارات القديمة
        w = draw.textsize(text, font=font)[0]

    if w <= max_width:
        return text

    for i in range(len(text), 0, -1):
        temp_text = text[:i] + "..."
        try:
            w_temp = draw.textlength(temp_text, font=font)
        except:
            w_temp = draw.textsize(temp_text, font=font)[0]
            
        if w_temp <= max_width:
            return temp_text
    return "..."

# 4. تنسيق المشاهدات بأمان
def format_views(views):
    try:
        v = str(views).lower().replace("views", "").strip()
        if "m" in v or "k" in v:
            return v.upper()
        
        # استخراج الأرقام فقط
        val = int(re.sub(r'\D', '', v))
        
        if val >= 1_000_000:
            return f"{val/1_000_000:.1f}M"
        elif val >= 1_000:
            return f"{val/1_000:.1f}K"
        else:
            return str(val)
    except:
        return str(views)

# 5. رسم النص بظل
def draw_shadowed_text(draw, pos, text, font, color="white"):
    text = str(text)
    x, y = pos
    # الظل
    draw.text((x + 2, y + 2), text, font=font, fill="black")
    # النص الأصلي
    draw.text((x, y), text, font=font, fill=color)

# 6. رسم نص نيون (Time Embedded in Glass)
def draw_neon_text(base_img, pos, text, font, glow_color="#00d4ff"):
    text = str(text)
    # طبقة شفافة
    glow_layer = Image.new('RGBA', base_img.size, (0, 0, 0, 0))
    draw_glow = ImageDraw.Draw(glow_layer)
    
    # رسم النص المضيء
    draw_glow.text(pos, text, font=font, fill=glow_color)
    
    # عمل Blur للضوء
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=5))
    
    # دمج الضوء مع الخلفية
    base_img.alpha_composite(glow_layer)
    
    # رسم النص الأبيض الشفاف فوق الضوء
    draw_final = ImageDraw.Draw(base_img)
    draw_final.text(pos, text, font=font, fill=(255, 255, 255, 230))

# ============================================================
# 🎨 دالة الرسم (The Artist)
# ============================================================
async def draw_thumb(thumbnail_path, title, userid, theme, duration, views, videoid):
    try:
        # تحويل كل المدخلات لنصوص لمنع TypeError
        title = str(title or "Unknown Track")
        userid = str(userid or "Unknown Artist")
        views = str(views or "0")
        duration = str(duration or "00:00")

        # 1. تجهيز الخلفية
        if os.path.exists(thumbnail_path):
            try:
                source = Image.open(thumbnail_path).convert("RGBA")
            except:
                source = Image.new('RGBA', (1280, 720), (30, 30, 30))
        else:
            source = Image.new('RGBA', (1280, 720), (30, 30, 30))

        background = source.resize((1280, 720), resample=LANCZOS)
        background = background.filter(ImageFilter.GaussianBlur(3))
        
        # تغميق بسيط
        darkener = Image.new('RGBA', (1280, 720), (0, 0, 0, 60))
        background = Image.alpha_composite(background, darkener)

        # 2. دمج القالب (Overlay)
        overlay_path = "BrandrdXMusic/assets/overlay.png"
        if not os.path.isfile(overlay_path):
            overlay_path = "assets/overlay.png"

        if os.path.isfile(overlay_path):
            try:
                overlay = Image.open(overlay_path).convert("RGBA")
                overlay = overlay.resize((1280, 720), resample=LANCZOS)
                
                # Screen Blend Logic
                bg_rgb = background.convert("RGB")
                ov_rgb = overlay.convert("RGB")
                merged = ImageChops.screen(bg_rgb, ov_rgb)
                background = merged.convert("RGBA")
            except:
                # Fallback if blending fails
                background.paste(overlay, (0, 0), overlay)

        # 3. الدائرة الذكية (Smart Circle)
        try:
            big_w, big_h = CIRCLE_SIZE[0] * 3, CIRCLE_SIZE[1] * 3
            smart_circle = ImageOps.fit(source, (big_w, big_h), centering=(0.5, 0.5), method=LANCZOS)
            
            mask = Image.new('L', (big_w, big_h), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, big_w, big_h), fill=255)
            
            smart_circle = smart_circle.resize(CIRCLE_SIZE, resample=LANCZOS)
            mask = mask.resize(CIRCLE_SIZE, resample=LANCZOS)
            
            background.paste(smart_circle, CIRCLE_POS, mask)
        except Exception as e:
            print(f"Circle Error: {e}")

        # 4. الكتابة
        draw = ImageDraw.Draw(background)
        f_45 = get_font(45)
        f_30 = get_font(30)
        f_26 = get_font(26)

        # Name
        trunc_title = smart_truncate(draw, title, f_45, 500)
        draw_shadowed_text(draw, NAME_POS, f"Name: {trunc_title}", f_45, "white")
        
        # By
        trunc_by = smart_truncate(draw, userid, f_30, 450)
        draw_shadowed_text(draw, BY_POS, f"By: {trunc_by}", f_30, "#dddddd")
        
        # Views (Cyan Color)
        fmt_views = format_views(views)
        draw_shadowed_text(draw, VIEWS_POS, f"Views: {fmt_views}", f_30, "#00d4ff")

        # Time (Neon Effect - Embedded in Glass)
        draw_neon_text(background, TIME_START, "00:00", f_26)
        draw_neon_text(background, TIME_END, duration, f_26)

        # حفظ الناتج
        if not os.path.exists("cache"):
            os.makedirs("cache")
            
        output = f"cache/{videoid}_final.png"
        background.save(output)
        return output

    except Exception as e:
        print(f"Draw Error: {e}")
        return thumbnail_path

# ============================================================
# 🦅 الصياد (The Fetcher)
# ============================================================
async def gen_thumb(videoid, user_id=None):
    if not os.path.exists("cache"):
        os.makedirs("cache")
        
    final_path = f"cache/{videoid}_final.png"
    if os.path.isfile(final_path):
        return final_path

    temp_path = f"cache/temp_{videoid}.png"
    url = f"https://www.youtube.com/watch?v={videoid}"

    try:
        search = VideosSearch(url, limit=1)
        search_result = await search.next()
        res = search_result["result"][0]
        
        title = res.get("title", "Unknown Track")
        title = re.sub(r"\W+", " ", title).title()
        
        duration = res.get("duration", "00:00")
        views = res.get("viewCount", {}).get("short", "0")
        channel = res.get("channel", {}).get("name", "Unknown Artist")
        
        candidates = [
            f"https://img.youtube.com/vi/{videoid}/maxresdefault.jpg",
            f"https://img.youtube.com/vi/{videoid}/hqdefault.jpg",
            f"https://img.youtube.com/vi/{videoid}/sddefault.jpg"
        ]
        if res.get("thumbnails"):
            candidates.append(res["thumbnails"][-1]["url"])

        downloaded = False
        async with aiohttp.ClientSession() as session:
            for img_url in candidates:
                try:
                    async with session.get(img_url, timeout=5) as resp:
                        if resp.status == 200:
                            data = await resp.read()
                            if len(data) > 1000:
                                async with aiofiles.open(temp_path, mode="wb") as f:
                                    await f.write(data)
                                downloaded = True
                                break
                except:
                    continue
                if downloaded:
                    break
        
        if not downloaded:
            return YOUTUBE_IMG_URL

        final_img = await draw_thumb(temp_path, title, channel, None, duration, views, videoid)
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return final_img

    except Exception as e:
        print(f"Gen Error: {e}")
        return YOUTUBE_IMG_URL

# تصدير الدالة الأساسية
get_thumb = gen_thumb
