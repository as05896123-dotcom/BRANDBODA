import random
import re
import string
import lyricsgenius as lg
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from BrandrdXMusic import app
from config import BANNED_USERS, lyrical

# -----------------------------------------------------------
# مفتاح Genius الخاص بك ✅
api_key = "Hqw2MvfHddbZcv_5q3PsFYt_q_tAnGirPUlzxfJKU04vy-URdIopznmh2Z-jLaueU1YkGLahD2rNCTZq4TVVEQ"
# -----------------------------------------------------------

y = lg.Genius(api_key, skip_non_songs=True, excluded_terms=["(Remix)", "(Live)"], remove_section_headers=True)
y.verbose = False

y._session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1"
})

# -----------------------------------------------------------
# 1. دالة البحث
# -----------------------------------------------------------
@app.on_message(filters.command("كلمات", prefixes="") & ~BANNED_USERS)
async def lrsearch(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("**• اكـتـب الامـر + اسـم الاغـنـيـة 🧚🤍**\n**• مـثـال »** `كلمات بحبك`")

    title = message.text.split(None, 1)[1]
    m = await message.reply_text("**• جـارِ الـبـحـث عـن الـكـلـمـات (Genius) 🧚🤍...**")
    
    try:
        S = y.search_song(title, get_full_info=False)
        if S is None:
            return await m.edit(f"**• لـم يـتـم الـعـثـور عـلـى كـلـمـات لـ »** `{title}` 🥀")

        ran_hash = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
        lyric = S.lyrics
        
        # ------------------- منطقة التنظيف -------------------
        
        # 1. حذف الديباجة المزعجة في الأول (Contributors ... Lyrics)
        # الكود ده بيمسح أي حاجة من أول النص لحد كلمة Lyrics
        lyric = re.sub(r"^.*?Lyrics", "", lyric, flags=re.DOTALL)
        
        # 2. حذف جملة You might also like
        lyric = lyric.replace("You might also like", "")
        
        # 3. حذف كلمة Embed والأرقام اللي في الآخر
        lyric = re.sub(r"\d*Embed", "", lyric)
        
        # 4. مسح المسافات الفاضية في الأول والآخر
        lyric = lyric.strip()
        
        # -----------------------------------------------------
        
        lyrical[ran_hash] = lyric

        upl = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="• عـرض الـكـلـمـات 🥀 •", url=f"https://t.me/{app.username}?start=lyrics_{ran_hash}")]]
        )
        
        await m.edit(f"**• تـم الـعـثـور عـلـى الـكـلـمـات بـنـجـاح 💞**\n\n**• الاغـنـيـة »** {title} 🤍\n**• الـمـصـدر »** Genius ✅", reply_markup=upl)
    
    except Exception as e:
        print(f"Lyrics Search Error: {e}")
        await m.edit(f"**• حـدث خـطـأ أثـنـاء الـبـحـث 🥀**\n`{e}`")


# -----------------------------------------------------------
# 2. دالة العرض (مع الحل النهائي لمشكلة Start)
# -----------------------------------------------------------
@app.on_message(filters.regex(r"^/start lyrics_") & ~BANNED_USERS, group=-1)
async def lyrics_display(client, message: Message):
    try:
        ran_hash = message.text.split("lyrics_")[1]
        lyric = lyrical.get(ran_hash)
        
        if not lyric:
            return await message.reply_text("**• عـذراً، الـكـلـمـات لـم تـعـد مـتـاحـة (ابـحـث مـرة اخـرى) 🥀**")
        
        if len(lyric) > 4000:
            lyric = lyric[:4000] + "..."
            
        await message.reply_text(
            f"**• كـلـمـات الاغـنـيـة:**\n\n{lyric}",
            disable_web_page_preview=True
        )
        
        message.stop_propagation()
        
    except Exception as e:
        print(f"Lyrics Display Error: {e}")
