import os
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from BrandrdXMusic import app
import requests


def upload_file(file_path):
    url = "https://catbox.moe/user/api.php"
    data = {"reqtype": "fileupload", "json": "true"}
    files = {"fileToUpload": open(file_path, "rb")}
    response = requests.post(url, data=data, files=files)

    if response.status_code == 200:
        return True, response.text.strip()
    else:
        return False, f"Error: {response.status_code} - {response.text}"


@app.on_message(
    filters.command(
        ["tgm", "tgt", "telegraph", "tl", "تلجراف", "تليجراف", "رابط"],
        prefixes=["/", "!", ".", ""]
    )
)
async def get_link_group(client, message):
    if not message.reply_to_message:
        return await message.reply_text(
            "**قم بالرد على صورة أو فيديو أو ملف لرفعه.**"
        )

    media = message.reply_to_message
    file_size = 0
    if media.photo:
        file_size = media.photo.file_size
    elif media.video:
        file_size = media.video.file_size
    elif media.document:
        file_size = media.document.file_size

    if file_size > 200 * 1024 * 1024:
        return await message.reply_text("يجب أن يكون حجم الملف أقل من 200 ميجابايت.")

    try:
        text = await message.reply("🥀 جارٍ المعالجة...")

        async def progress(current, total):
            try:
                await text.edit_text(f"🥀 جارٍ التنزيل... {current * 100 / total:.1f}%")
            except Exception:
                pass

        try:
            local_path = await media.download(progress=progress)
            await text.edit_text("🥀 جارٍ الرفع إلى السيرفر...")

            success, upload_path = upload_file(local_path)

            if success:
                await text.edit_text(
                    f"🥀 | [رابط الملف]({upload_path})",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "رابط الملف",
                                    url=upload_path,
                                )
                            ]
                        ]
                    ),
                )
            else:
                await text.edit_text(
                    f"حدث خطأ أثناء الرفع\n{upload_path}"
                )

            try:
                os.remove(local_path)
            except Exception:
                pass

        except Exception as e:
            await text.edit_text(f"🥀 فشل الرفع\n\n<i>السبب: {e}</i>")
            try:
                os.remove(local_path)
            except Exception:
                pass
            return
    except Exception:
        pass


__HELP__ = """
**اوامر الرفع والاستخراج**

استخدم هذه الأوامر لاستخراج رابط مباشر للوسائط:

- تلجراف أو رابط : قم بالرد على الصورة أو الملف لاستخراج الرابط.
"""

__MODULE__ = "الروابط"
