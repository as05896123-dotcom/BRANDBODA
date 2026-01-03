import asyncio
import os
import re
import aiofiles

from pykeyboard import InlineKeyboard
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton

from BrandrdXMusic import app
from BrandrdXMusic.utils.errors import capture_err
from BrandrdXMusic.utils.pastebin import HottyBin


# تحديد صيغ الملفات المسموح بها
pattern = re.compile(r"^text/|json$|yaml$|xml$|toml$|x-sh$|x-shellscript$")


# الأمر: لصق / رابط / طباعة
@app.on_message(filters.command(["لصق", "رابط", "طباعة"], prefixes=["/", "!", "."]))
@capture_err
async def paste_func(_, message):
    
    # لازم يكون فيه رد
    if not message.reply_to_message:
        return await message.reply_text(
            "**قـم بـالـرد عـلـى نـص أو مـلـف لـرفـعـه..** 🤍"
        )

    # رسالة انتظار
    m = await message.reply_text("**جـاري الـمـعـالـجـة والـرفـع...**")

    # ───── معالجة النص ─────
    if message.reply_to_message.text:
        content = str(message.reply_to_message.text)

    # ───── معالجة الملفات ─────
    elif message.reply_to_message.document:
        document = message.reply_to_message.document

        # حجم الملف (1 ميجا)
        if document.file_size > 1048576:
            return await m.edit(
                "**عـذراً، يـجـب أن يـكـون حـجـم الـمـلـف أقـل مـن 1 مـيـجـا.** 🧚"
            )

        # نوع الملف
        if not pattern.search(document.mime_type):
            return await m.edit(
                "**عـذراً، يُـسـمـح فـقـط بـالـمـلـفـات الـنـصـيـة.** 🤍"
            )

        doc = await message.reply_to_message.download()

        async with aiofiles.open(doc, mode="r") as f:
            content = await f.read()

        os.remove(doc)

    else:
        return await m.edit("**نـوع الـرسـالـة غـيـر مـدعـوم.** 🥀")

    # ───── رفع النص ─────
    link = await HottyBin(content)

    # زر الرابط
    button = InlineKeyboard(row_width=1)
    button.add(
        InlineKeyboardButton(
            text="• رابـط الـنـص •",
            url=link
        )
    )

    # إرسال النتيجة
    await m.delete()
    try:
        await message.reply(
            "**تـم اسـتـخـراج الـرابـط بـنـجـاح** 🧚",
            quote=False,
            reply_markup=button
        )
    except Exception:
        pass
