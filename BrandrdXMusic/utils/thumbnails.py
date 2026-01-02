import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from youtubesearchpython.__future__ import VideosSearch
from config import YOUTUBE_IMG_URL

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دالة جلب الخطوط
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def get_font(size):
    possible_fonts = [
        "BrandrdXMusic/font.ttf",
        "BrandrdXMusic/assets/font.ttf",
        "font.ttf",
        "assets/font.ttf"
    ]
    for font_path in possible_fonts:
        if os.path.isfile(font_path):
            return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# دالة رسم الأيقونات (Play, Next, Prev)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def draw_player_icons(draw, x, y):
    white = (255, 255, 255, 255)
    
    # 1. زر التشغيل (Play) - في المنتصف
    draw.ellipse((x, y, x+64, y+64), outline=white, width=3)
    # المثلث
    draw.polygon([(x+25, y+20), (x+25, y+44), (x+48, y+32)], fill=white)

    # 2. زر التالي (Next)
    nx, ny = x + 100, y + 17
    draw.polygon([(nx, ny), (nx, ny+30), (nx+20, ny+15)], fill=white)
    draw.rectangle((nx+22, ny, nx+27, ny+30), fill=white)

    # 3. زر السابق (Prev)
    px, py = x - 100, y + 17
    draw.polygon([(px+20, py), (px+20, py+30), (px, py+15)], fill=white)
    draw.rectangle((px-7, py, px-2, py+30), fill=white)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. دالة الرسم والتصميم (Modified iPhone Style)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def draw_thumb(thumbnail, title, userid, theme, duration, views, videoid):
    try:
        # --- 1. إعداد الخلفية ---
        if os.path.isfile(thumbnail):
            source = Image.open(thumbnail).convert("RGBA")
        else:
            source = Image.new('RGBA', (1280, 720), (30, 30, 30, 255))

        # ملء الشاشة وتغبيش الخلفية
        bg = ImageOps.fit(source, (1280, 720), centering=(0.5, 0.5))
        bg = bg.filter(ImageFilter.GaussianBlur(50))
        
        # طبقة تعتيم
        dark_overlay = Image.new('RGBA', (1280, 720), (0, 0, 0, 110))
        bg = Image.alpha_composite(bg, dark_overlay)

        # ---------------------------------------------------------
        # --- 2. الحلقة الزجاجية والدائرة (يسار الشاشة) ---
        # ---------------------------------------------------------
        # تم تحريكها لليسار (90) وتصغير الحجم (360)
        art_size = 360
        ring_x, ring_y = 90, 180 
        ring_gap = 30 
        
        # رسم الحلقة الزجاجية الخارجية
        glass_ring_size = art_size + (ring_gap * 2)
        glass_ring = Image.new('RGBA', (glass_ring_size, glass_ring_size), (0,0,0,0))
        d_ring = ImageDraw.Draw(glass_ring)
        
        d_ring.ellipse(
            (0, 0, glass_ring_size, glass_ring_size),
            fill=(255, 255, 255, 10),    
            outline=(255, 255, 255, 60), 
            width=2
        )
        bg.paste(glass_ring, (ring_x - ring_gap, ring_y - ring_gap), glass_ring)

        # رسم صورة الألبوم
        art = ImageOps.fit(source, (art_size, art_size), centering=(0.5, 0.5)).convert("RGBA")
        mask = Image.new('L', (art_size, art_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, art_size, art_size), fill=255)
        
        art_circle = Image.new('RGBA', (art_size, art_size), (0,0,0,0))
        art_circle.paste(art, (0, 0), mask)
        
        # حدود للصورة نفسها
        ImageDraw.Draw(art_circle).ellipse((0,0,art_size,art_size), outline=(255,255,255,80), width=4)
        
        bg.paste(art_circle, (ring_x, ring_y), art_circle)

        # ---------------------------------------------------------
        # --- 3. المستطيل الزجاجي العريض (يمين الشاشة) ---
        # ---------------------------------------------------------
        # تم توسيع اللوحة (740) وسحبها لليسار (520)
        panel_x = 520
        panel_y = 150
        panel_w = 700
        panel_h = 420
        
        glass_panel = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
        d_panel = ImageDraw.Draw(glass_panel)
        
        d_panel.rounded_rectangle(
            (panel_x, panel_y, panel_x + panel_w, panel_y + panel_h),
            radius=35,
            fill=(0, 0, 0, 130),        
            outline=(255, 255, 255, 30),
            width=2
        )
        bg = Image.alpha_composite(bg, glass_panel)

        # --- 4. المحتوى داخل المستطيل ---
        draw = ImageDraw.Draw(bg)
        
        # هامش داخلي للنصوص
        padding = 50
        content_x = panel_x + padding
        content_y = panel_y + 40
        content_w = panel_w - (padding * 2)
        
        f_title = get_font(50)
        f_sub = get_font(30)
        f_time = get_font(26)

        if len(title) > 35: title = title[:35] + "..."

        # النصوص
        draw.text((content_x, content_y), title, font=f_title, fill="white")
        draw.text((content_x, content_y + 65), f"{userid}", font=f_sub, fill="#cccccc")
        draw.text((content_x, content_y + 105), f"Views: {views}", font=f_sub, fill="#aaaaaa")

        # شريط التقدم
        bar_y = content_y + 190
        # الخط الخلفي
        draw.line((content_x, bar_y, content_x + content_w, bar_y), fill=(255,255,255,50), width=8)
        # الخط الأمامي (الأحمر)
        progress_px = int(content_w * 0.45) # 45% كنسبة تقريبية
        draw.line((content_x, bar_y, content_x + progress_px, bar_y), fill=theme, width=8)
        # النقطة
        draw.ellipse(
            (content_x + progress_px - 9, bar_y - 9, content_x + progress_px + 9, bar_y + 9),
            fill="white"
        )
        
        # التوقيت
        draw.text((content_x, bar_y + 25), "00:00", font=f_time, fill="white")
        draw.text((content_x + content_w - 80, bar_y + 25), duration, font=f_time, fill="white")

        # الأزرار (Play/Pause) - توسيطها بدقة
        icons_center_x = content_x + (content_w // 2) - 32 # -32 نصف عرض زر التشغيل لضمان التوسط
        draw_player_icons(draw, icons_center_x, bar_y + 90)

        # الحفظ
        output = f"cache/{videoid}.png"
        bg.convert("RGB").save(output)
        return output
        
    except Exception as e:
        print(f"Error in draw_thumb: {e}")
        return thumbnail

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. الدالة الرئيسية (get_thumb)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def get_thumb(videoid):
    if not os.path.exists("cache"):
        os.makedirs("cache")

    if os.path.isfile(f"cache/{videoid}.png"):
        return f"cache/{videoid}.png"

    url = f"https://www.youtube.com/watch?v={videoid}"
    try:
        results = VideosSearch(url, limit=1)
        for result in (await results.next())["result"]:
            try:
                title = result["title"]
                title = re.sub("\W+", " ", title)
                title = title.title()
            except:
                title = "Unsupported Title"
            try:
                duration = result["duration"]
            except:
                duration = "Unknown"
            
            thumbnail = result["thumbnails"][0]["url"]

            try:
                views = result["viewCount"]["short"]
            except:
                views = "Unknown Views"
            try:
                channel = result["channel"]["name"]
            except:
                channel = "Unknown Channel"

        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(f"cache/temp{videoid}.png", mode="wb")
                    await f.write(await resp.read())
                    await f.close()

        final_image = await draw_thumb(
            f"cache/temp{videoid}.png", 
            title, 
            channel, 
            "#ff0000", 
            duration, 
            views,
            videoid
        )

        try:
            os.remove(f"cache/temp{videoid}.png")
        except:
            pass
            
        return final_image

    except Exception as e:
        print(e)
        return YOUTUBE_IMG_URL
