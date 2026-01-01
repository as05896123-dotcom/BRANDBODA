import sys
import io
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from BrandrdXMusic import app

# السماح بتحويل الأرقام الضخمة جداً إلى نصوص (لإصدارات بايثون الحديثة)
try:
    sys.set_int_max_str_digits(0)
except AttributeError:
    pass

# إشعار بدء المكالمة
@app.on_message(filters.video_chat_started)
async def brah(_, msg):
    await msg.reply("🥀 **بدأت المحادثة المرئية**")


# إشعار انتهاء المكالمة
@app.on_message(filters.video_chat_ended)
async def brah2(_, msg):
    await msg.reply("🥀 **تم اغلاق المحادثة المرئية**")


# إشعار دعوة أعضاء للمكالمة
@app.on_message(filters.video_chat_members_invited)
async def brah3(client, message: Message):
    text = f"🥀 {message.from_user.mention}\n\n**قام بدعوة هؤلاء للمكالمة :**\n\n**➻ **"
    x = 0
    for user in message.video_chat_members_invited.users:
        try:
            text += f"[{user.first_name}](tg://user?id={user.id}) "
            x += 1
        except Exception:
            pass

    try:
        add_link = f"https://t.me/{app.username}?startgroup=true"
        await message.reply(
            text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(text="🥀 انضم للمكالمة", url=add_link)],
                ]
            ),
        )
    except Exception as e:
        print(f"Error: {e}")


# الآلة الحاسبة
@app.on_message(
    filters.command(
        ["math", "احسب", "حساب"],
        prefixes=["/", "!", ".", ""]
    )
)
async def calculate_math(client, message):
    if len(message.command) < 2:
        return await message.reply("🥀 **يرجى كتابة المسألة الحسابية بجوار الأمر.**")
    
    expression = message.text.split(None, 1)[1]
    try:
        # حساب النتيجة
        result = eval(expression)
        result_str = str(result)
        
        # إذا كان الرقم كبيراً جداً (أكثر من 4096 حرف)، يتم إرساله كملف
        if len(result_str) > 4090:
            with io.BytesIO(str.encode(result_str)) as out_file:
                out_file.name = "result.txt"
                await message.reply_document(
                    document=out_file,
                    caption="🥀 **الرقم كبير جداً، تم إرسال النتيجة في ملف.**"
                )
        else:
            await message.reply(f"🥀 النتيجة : {result_str}")
            
    except ZeroDivisionError:
        await message.reply("🥀 **لا يمكن القسمة على صفر.**")
    except Exception:
        await message.reply("🥀 **مسألة خاطئة، تأكد من كتابة الأرقام والرموز بشكل صحيح.**")


__HELP__ = """
**اوامر الالة الحاسبة**

- احسب [المسألة] : يقوم بحل المسائل الرياضية مهما كان حجم الرقم.

**مثال:**
- احسب 100 ** 100
"""

__MODULE__ = "الحساب"
