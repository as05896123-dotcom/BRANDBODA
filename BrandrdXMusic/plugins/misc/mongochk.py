from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import MongoClient
import re
from BrandrdXMusic import app as Hotty

# نمط التحقق من صحة الرابط
mongo_url_pattern = re.compile(r'mongodb(?:\+srv)?:\/\/[^\s]+')

@Hotty.on_message(filters.command(["مونجو", "فحص_مونجو", "mongochk"], prefixes=["/", "!", ".", ""]))
async def mongo_command(client, message: Message):
    if len(message.command) < 2:
        await message.reply("🥀 **الرجاء إدخال رابط المونجو بجانب الأمر.**\n\nمثال:\n`/مونجو الرابط_هنا`")
        return

    mongo_url = message.command[1]
    
    # التحقق من صيغة الرابط
    if re.match(mongo_url_pattern, mongo_url):
        try:
            # رسالة انتظار
            status_msg = await message.reply("🧚 **جـارِ فـحـص الـرابـط...**")
            
            # محاولة الاتصال بقاعدة البيانات (مهلة 5 ثواني)
            client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
            client.server_info()  # سيحدث خطأ هنا إذا لم يتم الاتصال
            
            await status_msg.edit("🧚 **رابط المونجو شغال والاتصال نجح !**")
        except Exception as e:
            await status_msg.edit(f"🥀 **فشل الاتصال بقاعدة البيانات:**\n\n`{e}`")
    else:
        await message.reply("🥀 **صيغة رابط المونجو غير صحيحة !**")
