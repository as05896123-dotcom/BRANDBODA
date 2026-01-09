"""
[ SYSTEM: VC TOOLS - RANDOM EMOJI ]
[ STYLE: RANDOM BETWEEN ☔ AND 💜 ]
"""

import random
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from BrandrdXMusic import app

# =======================================================================
# 🎲 دالة اختيار الإيموجي العشوائي
# =======================================================================
def get_emo():
    return random.choice(["☔", "💜"])

# =======================================================================
# 1. إشعارات المكالمة الصوتية
# =======================================================================

# عند بدء المكالمة
@app.on_message(filters.video_chat_started)
async def vc_start(_, msg):
    await msg.reply(f"**◂ تـم فـتـح الـمـحـادثـة الـصـوتـيـة {get_emo()}**")

# عند إنهاء المكالمة
@app.on_message(filters.video_chat_ended)
async def vc_end(_, msg):
    await msg.reply(f"**◂ تـم إغـلاق الـمـحـادثـة الـصـوتـيـة {get_emo()}**")

# عند دعوة أعضاء للمكالمة
@app.on_message(filters.video_chat_members_invited)
async def vc_invite(client, message: Message):
    emo = get_emo()
    # تنسيق نص الدعوة
    text = f"**◂ قـام : {message.from_user.mention}\n**"
    text += f"**◂ بـدعـوة الاعـضـاء الـتـالـيـة لـلـمـكـالـمـة {emo} :**\n\n"
    
    # تجميع أسماء المدعوين
    try:
        for user in message.video_chat_members_invited.users:
            text += f"**•** [{user.first_name}](tg://user?id={user.id})\n"
    except Exception:
        pass

    # إنشاء زر الانضمام والرابط
    try:
        add_link = f"https://t.me/{app.username}?startgroup=true"
        
        await message.reply(
            text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="• انـضـمـام لـلـمـكـالـمـة •", url=add_link)]]
            ),
        )
    except Exception as e:
        print(f"Error in VC Invite: {e}")

# =======================================================================
# 🧮 2. الآلة الحاسبة (Math)
# =======================================================================

@app.on_message(filters.command(["احسب", "حساب"], prefixes=""))
async def calculate_math(client, message):
    emo = get_emo()
    try:
        if len(message.command) < 2:
            return await message.reply(f"**◂ خـطـأ .. الـرجـاء إدراج الـمـسـألـة الـحـسـابـيـة {emo}**\n**مـثـال :** `احسب 1 + 1`")
        
        # استخراج المعادلة
        expression = message.text.split(None, 1)[1]
        
        # حماية أمنية
        allowed_chars = set("0123456789+-*/(). ")
        if not set(expression).issubset(allowed_chars):
            return await message.reply(f"**◂ عـذراً .. الـمـعـادلـة تـحـتـوي عـلـى رمـوز خـاطـئـة {emo}**")
            
        # حساب النتيجة
        result = eval(expression)
        
        # الرد بالنتيجة
        await message.reply(f"**◂ الـنـاتـج الـنـهـائـي هـو :** `{result}` {emo}")
        
    except ZeroDivisionError:
        await message.reply(f"**◂ عـذراً .. لا يـمـكـن الـقـسـمـة عـلـى الـصـفـر {emo}**")
    except Exception:
        await message.reply(f"**◂ حـدث خـطـأ .. تـأكـد مـن الـمـعـادلـة مـرة أخـرى {emo}**")
