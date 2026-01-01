import os 
import random
from datetime import datetime 
from telegraph import upload_file
from PIL import Image , ImageDraw
from pyrogram import filters, Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.enums import ChatType

# تأكد من مسار البوت الخاص بك
from BrandrdXMusic import app
# استيراد دوال قاعدة البيانات
from BrandrdXMusic.mongo.couples_db import _get_image, get_couple, save_couple

def dt():
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M")
    dt_list = dt_string.split(" ")
    return dt_list

def dt_tom():
    a = (
        str(int(dt()[0].split("/")[0]) + 1)
        + "/"
        + dt()[0].split("/")[1]
        + "/"
        + dt()[0].split("/")[2]
    )
    return a

tomorrow = str(dt_tom())
today = str(dt()[0])

@app.on_message(filters.command(["couples", "زوجين", "تطقيم", "كوبل"]))
async def couples(client, message: Message):
    cid = message.chat.id
    if message.chat.type == ChatType.PRIVATE:
        return await message.reply_text("🤎 **هـذا الأمـر يـعـمـل فـقـط فـي الـمـجـمـوعـات.**")
    
    try:
        msg = await message.reply_text("💞 **جـاري اخـتـيـار ثـنـائـي الـيـوم...**")
        
        # التحقق من قاعدة البيانات
        is_selected = await get_couple(cid, today)
        
        if not is_selected:
            # --- اختيار جديد ---
            list_of_users = []
            async for i in app.get_chat_members(message.chat.id, limit=100):
                if not i.user.is_bot:
                    list_of_users.append(i.user.id)

            if len(list_of_users) < 2:
                return await msg.edit("⚠️ **عـدد الأعـضـاء قـلـيـل جـداً لاخـتـيـار ثـنـائـي.**")

            c1_id = random.choice(list_of_users)
            c2_id = random.choice(list_of_users)
            while c1_id == c2_id:
                c1_id = random.choice(list_of_users)

            photo1 = (await app.get_chat(c1_id)).photo
            photo2 = (await app.get_chat(c2_id)).photo
 
            N1 = (await app.get_users(c1_id)).mention 
            N2 = (await app.get_users(c2_id)).mention
            
            try:
                p1 = await app.download_media(photo1.big_file_id, file_name="pfp.png")
            except Exception:
                p1 = "BrandrdXMusic/assets/upic.png"
            try:
                p2 = await app.download_media(photo2.big_file_id, file_name="pfp1.png")
            except Exception:
                p2 = "BrandrdXMusic/assets/upic.png"
            
            # --- معالجة الصور ---
            img1 = Image.open(f"{p1}")
            img2 = Image.open(f"{p2}")

            # يجب عليك حفظ الصورة التي أرسلتها باسم cppicbranded.jpg في هذا المسار
            img = Image.open("BrandrdXMusic/assets/cppicbranded.jpg")

            # تغيير الحجم ليناسب الدوائر في القالب الجديد
            img1 = img1.resize((437,437))
            img2 = img2.resize((437,437))

            mask = Image.new('L', img1.size, 0)
            draw = ImageDraw.Draw(mask) 
            draw.ellipse((0, 0) + img1.size, fill=255)

            mask1 = Image.new('L', img2.size, 0)
            draw = ImageDraw.Draw(mask1) 
            draw.ellipse((0, 0) + img2.size, fill=255)

            img1.putalpha(mask)
            img2.putalpha(mask1)

            draw = ImageDraw.Draw(img)

            # --- إحداثيات القالب الجديد (BODA Style) ---
            img.paste(img1, (116, 160), img1) # الدائرة الخضراء (يسار)
            img.paste(img2, (789, 160), img2) # الدائرة الوردية (يمين)

            img_path = f'test_{cid}.png'
            img.save(img_path)
            
            TXT = f"""
**💞 ثـنـائـي الـيـوم لـهـذه الـمـجـمـوعـة :**

{N1} + {N2} = 🤍

**سـيـتـم اخـتـيـار ثـنـائـي جـديـد غـداً فـي : {tomorrow}** 💕
"""
            await message.reply_photo(
                img_path, 
                caption=TXT,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("• الـمـطـور •", url="https://t.me/S_G0C7")]
                ])
            )
            await msg.delete()
            
            try:
                a = upload_file(img_path)
                for x in a:
                    img_url = "https://graph.org/" + x
                    couple = {"c1_id": c1_id, "c2_id": c2_id}
                    await save_couple(cid, today, couple, img_url)
            except Exception as e:
                print(f"Database Error: {e}")
        
        else:
            # --- إذا كان مختاراً مسبقاً ---
            await msg.delete()
            c1_id = int(is_selected["c1_id"])
            c2_id = int(is_selected["c2_id"])
            try:
                c1_name = (await app.get_users(c1_id)).mention
                c2_name = (await app.get_users(c2_id)).mention
            except:
                c1_name = "شـخـص"
                c2_name = "شـخـص"
            
            b = await _get_image(cid)
            
            TXT = f"""
**🤎 ثـنـائـي الـيـوم الـمـخـتـار سـابـقـاً :**

{c1_name} + {c2_name} = 🤍

**سـيـتـم تـحـديـث الـكـوبـل غـداً فـي : {tomorrow}** 🤎
"""
            await message.reply_photo(
                b, 
                caption=TXT,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("• الـمـطـور •", url="https://t.me/S_G0C7")]
                ])
            )

    except Exception as e:
        print(str(e))
        await msg.edit("🥀 **حـدث خـطـأ.**")
    
    try:
        if os.path.exists(f"test_{cid}.png"):
            os.remove(f"test_{cid}.png")
        if os.path.exists("pfp.png"):
            os.remove("pfp.png")
        if os.path.exists("pfp1.png"):
            os.remove("pfp1.png")
    except Exception:
        pass
