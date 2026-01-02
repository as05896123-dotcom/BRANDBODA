import os
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageFont

async def gen_thumb(thumbnail, title, userid, theme, duration, views):
    try:
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1. إعداد الخلفية والصورة الأساسية
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if os.path.isfile(thumbnail):
            source = Image.open(thumbnail).convert("RGB")
        else:
            # لون احتياطي في حال عدم وجود صورة
            source = Image.new('RGB', (1280, 720), (30, 30, 30))

        # استخدام fit لضمان عدم مط الصورة (الحفاظ على الأبعاد)
        bg = ImageOps.fit(source, (1280, 720), centering=(0.5, 0.5))
        bg = bg.filter(ImageFilter.GaussianBlur(60)) # ضبابية قوية
        
        # طبقة تعتيم (Dark Overlay)
        overlay = Image.new('RGBA', (1280, 720), (0, 0, 0, 100))
        bg.paste(overlay, (0, 0), overlay)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. تصميم الأسطوانة (Vinyl) - حجم مصغر
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        sz = 440 # حجم صغير ومناسب
        
        # قص الصورة بشكل دائري
        mask = Image.new('L', (sz, sz), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, sz, sz), fill=255)
        
        vinyl = ImageOps.fit(source, (sz, sz), centering=(0.5, 0.5)).convert("RGBA")
        vinyl.putalpha(mask)
        
        # رسم خطوط الأسطوانة (Grooves)
        d_v = ImageDraw.Draw(vinyl)
        for i in range(0, sz//2, 12):
            d_v.ellipse((i, i, sz-i, sz-i), outline=(0,0,0,35), width=2)
            
        # الملصق الداخلي (Label)
        lbl_sz = 150
        lbl_img = ImageOps.fit(source, (lbl_sz, lbl_sz), centering=(0.5, 0.5))
        lbl_mask = Image.new('L', (lbl_sz, lbl_sz), 0)
        ImageDraw.Draw(lbl_mask).ellipse((0, 0, lbl_sz, lbl_sz), fill=255)
        lbl_img.putalpha(lbl_mask)
        
        # إطار حول الملصق
        lbl_border = Image.new('RGBA', (lbl_sz+10, lbl_sz+10), (20,20,20,255))
        bor_mask = Image.new('L', (lbl_sz+10, lbl_sz+10), 0)
        ImageDraw.Draw(bor_mask).ellipse((0,0,lbl_sz+10,lbl_sz+10), fill=255)
        lbl_border.putalpha(bor_mask)
        lbl_border.paste(lbl_img, (5,5), lbl_img)
        vinyl.paste(lbl_border, ((sz-lbl_sz-10)//2, (sz-lbl_sz-10)//2), lbl_border)
        
        # الثقب الأسود (Hole)
        h_sz = 25
        h_mask = Image.new('L', (h_sz, h_sz), 0)
        ImageDraw.Draw(h_mask).ellipse((0, 0, h_sz, h_sz), fill=255)
        hole = Image.new('RGBA', (h_sz, h_sz), (10,10,10,255))
        hole.putalpha(h_mask)
        vinyl.paste(hole, ((sz-h_sz)//2, (sz-h_sz)//2), hole)

        # الظل الخلفي للأسطوانة
        shadow = Image.new('RGBA', (sz+60, sz+60), (0,0,0,0))
        ImageDraw.Draw(shadow).ellipse((30, 30, sz+30, sz+30), fill=(0,0,0,160))
        shadow = shadow.filter(ImageFilter.GaussianBlur(40))
        
        # تركيب الأسطوانة على اليسار
        bg.paste(shadow, (-60, (720-sz)//2 + 20), shadow)
        bg.paste(vinyl, (-80, (720-sz)//2), vinyl)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3. الفقاعة الزجاجية (Glass Bubble)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        cx, cy, cw, ch = 440, 160, 780, 420
        glass = Image.new('RGBA', (cw, ch), (255, 255, 255, 0))
        d_glass = ImageDraw.Draw(glass)
        # حواف دائرية جداً (Radius = 60)
        d_glass.rounded_rectangle((0,0,cw,ch), radius=60, fill=(255,255,255,15), outline=(255,255,255,50), width=2)
        bg.paste(glass, (cx, cy), glass)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 4. النصوص والمحتوى
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        d = ImageDraw.Draw(bg)
        try:
            # حاول تحميل الخطوط، إذا لم توجد استخدم الافتراضي
            f_title = ImageFont.truetype("BrandrdXMusic/assets/font.ttf", 55)
            f_sub = ImageFont.truetype("BrandrdXMusic/assets/font.ttf", 35)
            f_small = ImageFont.truetype("BrandrdXMusic/assets/font2.ttf", 28)
        except:
            f_title = f_sub = f_small = ImageFont.load_default()

        # قص العنوان إذا كان طويلاً جداً
        if len(title) > 30: title = title[:30] + "..."
        
        tx, ty = cx + 60, cy + 50
        
        # العنوان
        d.text((tx, ty), title, font=f_title, fill="white")
        
        # اسم المستخدم
        d.text((tx, ty+75), f"By: {userid}", font=f_sub, fill="#dddddd")
        
        # عدد المشاهدات
        d.text((tx, ty+125), f"Views: {views}", font=f_small, fill="#aaaaaa")

        # شريط التقدم (Progress Bar)
        by = cy + 280
        # الخط الخلفي الشفاف
        d.line([(tx, by), (cx+cw-60, by)], fill=(255,255,255,50), width=8)
        # الخط الملون (يأخذ لون الثيم)
        d.line([(tx, by), (tx+250, by)], fill=theme, width=8)
        # النقطة البيضاء
        d.ellipse((tx+240, by-10, tx+260, by+10), fill='white')
        
        # توقيت البداية والنهاية
        d.text((tx, by+25), "00:00", font=f_small, fill="white")
        d.text((cx+cw-150, by+25), duration, font=f_small, fill="white")

        # الحفظ والإرجاع
        output = f"thumb_{userid}.png"
        bg.save(output)
        return output
        
    except Exception as e:
        print(f"Error in gen_thumb: {e}")
        return thumbnail
