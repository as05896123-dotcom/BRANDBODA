import os
from PIL import ImageDraw, Image, ImageFont, ImageChops
from pyrogram import filters, Client
from pyrogram.types import *
from logging import getLogger
from BrandrdXMusic import app
import config

LOGGER = getLogger(__name__)

class temp:
    ME = None
    CURRENT = 2
    CANCEL = False
    MELCOW = {}
    U_NAME = None
    B_NAME = None

def circle(pfp, size=(500, 500)):
    pfp = pfp.resize(size, Image.LANCZOS).convert("RGBA")
    bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
    mask = Image.new("L", bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(pfp.size, Image.LANCZOS)
    mask = ImageChops.darker(mask, pfp.split()[-1])
    pfp.putalpha(mask)
    return pfp

def welcomepic(pic, user, chatname, id, uname):
    background = Image.open("BrandrdXMusic/assets/Brandedwel2.png")
    pfp = Image.open(pic).convert("RGBA")
    pfp = circle(pfp)
    pfp = pfp.resize((825, 824))
    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype('BrandrdXMusic/assets/font.ttf', size=110)
    
    draw.text((2100, 1420), f'ID: {id}', fill=(255, 255, 255), font=font)
    
    pfp_position = (1990, 435)
    background.paste(pfp, pfp_position, pfp)
    background.save(f"downloads/welcome#{id}.png")
    return f"downloads/welcome#{id}.png"

# الأمر اليدوي لتجربة الترحيب
@app.on_message(filters.command(["ترحيب", "welcome"], prefixes=["/", "!", ".", ""]))
async def test_welcome(client, message):
    user = message.from_user
    chat = message.chat
    try:
        pic = await app.download_media(
            user.photo.big_file_id, file_name=f"pp{user.id}.png"
        )
    except AttributeError:
        pic = "BrandrdXMusic/assets/Brandedwel2.png"
    
    try:
        welcomeimg = welcomepic(
            pic, user.first_name, chat.title, user.id, user.username
        )
        await app.send_photo(
            chat.id,
            photo=welcomeimg,
            caption=f"""
• نــورت الـمـجـمـوعـة » {chat.title}
ـــــــــــــــــــــــــــــــــــــــــــــــــــــــ
• الاســـم » {user.mention}
• الايـدي » `{user.id}`
• الـيـوزر » @{user.username}
ـــــــــــــــــــــــــــــــــــــــــــــــــــــــ
""",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"• اضـف الـبـوت لـمـجـمـوعـتـك •", url=f"https://t.me/{app.username}?startgroup=true")]])
        )
    except Exception as e:
        LOGGER.error(e)
        await message.reply(f"حدث خطأ: {e}")
    
    try:
        os.remove(f"downloads/welcome#{user.id}.png")
        os.remove(f"downloads/pp{user.id}.png")
    except Exception:
        pass

# الترحيب التلقائي عند الانضمام
@app.on_chat_member_updated(filters.group, group=-3)
async def greet_group(_, member: ChatMemberUpdated):
    if (
        not member.new_chat_member
        or member.new_chat_member.status in {"banned", "left", "restricted"}
        or member.old_chat_member
    ):
        return
    user = member.new_chat_member.user if member.new_chat_member else member.from_user
    
    try:
        pic = await app.download_media(
            user.photo.big_file_id, file_name=f"pp{user.id}.png"
        )
    except AttributeError:
        pic = "BrandrdXMusic/assets/Brandedwel2.png"
        
    if (temp.MELCOW).get(f"welcome-{member.chat.id}") is not None:
        try:
            await temp.MELCOW[f"welcome-{member.chat.id}"].delete()
        except Exception as e:
            LOGGER.error(e)
            
    try:
        welcomeimg = welcomepic(
            pic, user.first_name, member.chat.title, user.id, user.username
        )
        temp.MELCOW[f"welcome-{member.chat.id}"] = await app.send_photo(
            member.chat.id,
            photo=welcomeimg,
            caption=f"""
• نــورت الـمـجـمـوعـة » {member.chat.title}
ـــــــــــــــــــــــــــــــــــــــــــــــــــــــ
• الاســـم » {user.mention}
• الايـدي » `{user.id}`
• الـيـوزر » @{user.username}
ـــــــــــــــــــــــــــــــــــــــــــــــــــــــ
""",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"• اضـف الـبـوت لـمـجـمـوعـتـك •", url=f"https://t.me/{app.username}?startgroup=true")]])
        )
    except Exception as e:
        LOGGER.error(e)
        
    try:
        os.remove(f"downloads/welcome#{user.id}.png")
        os.remove(f"downloads/pp{user.id}.png")
    except Exception as e:
        pass

# إشعار دخول البوت لمجموعة جديدة
@app.on_message(filters.new_chat_members & filters.group, group=-1)
async def bot_wel(_, message):
    for u in message.new_chat_members:
        if u.id == app.me.id:
            try:
                await app.send_message(config.LOG_GROUP_ID, f"""
• تـم تـفـعـيـل الـبـوت فـي مـجـمـوعـة جـديـدة
ـــــــــــــــــــــــــــــــــــــــــــــــــــــــ
• الاســـم » {message.chat.title}
• الايـدي » {message.chat.id}
• الـيـوزر » @{message.chat.username}
ـــــــــــــــــــــــــــــــــــــــــــــــــــــــ
""")
            except:
                pass

__HELP__ = """
**اوامر الترحيب**

يقوم البوت بالترحيب بالأعضاء الجدد تلقائياً بصورة.

- ترحيب : لعرض بطاقة الترحيب الخاصة بك (تجربة).
"""

__MODULE__ = "الترحيب"
