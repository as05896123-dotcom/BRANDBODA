import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from youtubesearchpython.__future__ import VideosSearch
from config import YOUTUBE_IMG_URL

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. دالة الرسم والتصميم (Vinyl Style)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def draw_thumb(thumbnail, title, userid, theme, duration, views, videoid):
    try:
        # إعداد الخلفية
        if os.path.isfile(thumbnail):
            source = Image.open(thumbnail).convert("RGB")
        else:
            source = Image.new('RGB', (1280, 720), (30, 30, 30))

        bg = ImageOps.fit(source, (1280, 720), centering=(0.5, 0.5))
        bg = bg.filter(ImageFilter.GaussianBlur(60))
        
        overlay = Image.new('RGBA', (1280, 720), (0, 0, 0, 100))
        bg.paste(overlay, (0, 0), overlay)

        # تصميم الأسطوانة (Vinyl)
        sz = 440
        mask = Image.new('L', (sz, sz), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, sz, sz), fill=255)
        
        vinyl = ImageOps.fit(source, (sz, sz), centering=(0.5, 0.5)).convert("RGBA")
        vinyl.putalpha(mask)
        
        d_v = ImageDraw.Draw(vinyl)
        for i in range(0, sz//2, 12):
            d_v.ellipse((i, i, sz-i, sz-i), outline=(0,0,0,35), width=2)
            
        lbl_sz = 150
        lbl_img = ImageOps.fit(source, (lbl_sz, lbl_sz), centering=(0.5, 0.5))
        lbl_mask = Image.new('L', (lbl_sz, lbl_sz), 0)
        ImageDraw.Draw(lbl_mask).ellipse((0, 0, lbl_sz, lbl_sz), fill=255)
        lbl_img.putalpha(lbl_mask)
        
        lbl_border = Image.new('RGBA', (lbl_sz+10, lbl_sz+10), (20,20,20,255))
        bor_mask = Image.new('L', (lbl_sz+10, lbl_sz+10), 0)
        ImageDraw.Draw(bor_mask).ellipse((0,0,lbl_sz+10,lbl_sz+10), fill=255)
        lbl_border.putalpha(bor_mask)
        lbl_border.paste(lbl_img, (5,5), lbl_img)
        vinyl.paste(lbl_border, ((sz-lbl_sz-10)//2, (sz-lbl_sz-10)//2), lbl_border)
        
        h_sz = 25
        h_mask = Image.new('L', (h_sz, h_sz), 0)
        ImageDraw.Draw(h_mask).ellipse((0, 0, h_sz, h_sz), fill=255)
        hole = Image.new('RGBA', (h_sz, h_sz), (10,10,10,255))
        hole.putalpha(h_mask)
        vinyl.paste(hole, ((sz-h_sz)//2, (sz-h_sz)//2), hole)

        shadow = Image.new('RGBA', (sz+60, sz+60), (0,0,0,0))
        ImageDraw.Draw(shadow).ellipse((30, 30, sz+30, sz+30), fill=(0,0,0,160))
        shadow = shadow.filter(ImageFilter.GaussianBlur(40))
        
        bg.paste(shadow, (-60, (720-sz)//2 + 20), shadow)
        bg.paste(vinyl, (-80, (720-sz)//2), vinyl)

        # الفقاعة الزجاجية
        cx, cy, cw, ch = 440, 160, 780, 420
        glass = Image.new('RGBA', (cw, ch), (255, 255, 255, 0))
        d_glass = ImageDraw.Draw(glass)
        d_glass.rounded_rectangle((0,0,cw,ch), radius=60, fill=(255,255,255,15), outline=(255,255,255,50), width=2)
        bg.paste(glass, (cx, cy), glass)

        # النصوص
        d = ImageDraw.Draw(bg)
        try:
            # محاولة تحميل الخطوط، إذا فشل يستخدم الافتراضي
            f_title = ImageFont.truetype("assets/font.ttf", 55)
            f_sub = ImageFont.truetype("assets/font.ttf", 35)
            f_small = ImageFont.truetype("assets/font.ttf", 28)
        except:
            f_title = f_sub = f_small = ImageFont.load_default()

        if len(title) > 30: title = title[:30] + "..."
        
        tx, ty = cx + 60, cy + 50
        
        d.text((tx, ty), title, font=f_title, fill="white")
        d.text((tx, ty+75), f"Channel: {userid}", font=f_sub, fill="#dddddd")
        d.text((tx, ty+125), f"Views: {views}", font=f_small, fill="#aaaaaa")

        by = cy + 280
        d.line([(tx, by), (cx+cw-60, by)], fill=(255,255,255,50), width=8)
        d.line([(tx, by), (tx+250, by)], fill=theme, width=8)
        d.ellipse((tx+240, by-10, tx+260, by+10), fill='white')
        
        d.text((tx, by+25), "00:00", font=f_small, fill="white")
        d.text((cx+cw-150, by+25), duration, font=f_small, fill="white")

        output = f"cache/{videoid}.png"
        bg.save(output)
        return output
        
    except Exception as e:
        print(f"Error in draw_thumb: {e}")
        return thumbnail


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. الدالة الرئيسية (Main Entry Point)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def gen_thumb(videoid, user_id):
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
            
            # === ⚠️ هنا الإصلاح الحقيقي ⚠️ ===
            # أخذنا الرابط كاملاً وحذفنا .split("?")[0]
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

        # استدعاء دالة الرسم
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
