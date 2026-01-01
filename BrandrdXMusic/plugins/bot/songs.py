import os
import re
import asyncio
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaAudio,
    InputMediaVideo,
    Message,
)

from config import (
    BANNED_USERS,
    SONG_DOWNLOAD_DURATION,
    SONG_DOWNLOAD_DURATION_LIMIT,
)
from BrandrdXMusic import YouTube, app
from BrandrdXMusic.utils.decorators.language import language, languageCB
from BrandrdXMusic.utils.formatters import convert_bytes
from BrandrdXMusic.utils.inline.song import song_markup

# ------------------------------------------------------------------
# دالة تنزيل داخلية لضمان عمل التحميل (بديلة للدالة الخارجية المعطلة)
# ------------------------------------------------------------------
def download_internal(url, stype, format_id):
    opts = {
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "geo_bypass": True,
        "nocheckcertificate": True,
        "quiet": True,
        "no_warnings": True,
        "cookiefile": "cookies.txt" if os.path.exists("cookies.txt") else None
    }

    if stype == "video":
        opts["format"] = f"{format_id}+bestaudio/best"
        opts["merge_output_format"] = "mp4"
    else:
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]

    try:
        with yt_dlp.YoutubeDL(opts) as ytdl:
            info = ytdl.extract_info(url, download=True)
            filename = ytdl.prepare_filename(info)
            
            if stype == "audio":
                base, _ = os.path.splitext(filename)
                return f"{base}.mp3"
            elif stype == "video":
                base, _ = os.path.splitext(filename)
                return f"{base}.mp4"
            return filename
    except Exception as e:
        print(f"Download Error: {e}")
        raise e 

# ------------------------------------------------------------------
# Song Module
# ------------------------------------------------------------------

@app.on_message(filters.command(["song", "يوت"], prefixes=["", "/"]) & ~BANNED_USERS)
@language
async def song_commad_private(client, message: Message, _):
    # لا نقوم بحذف الرسالة إذا لم تكن تحتوي على "/" لتجنب المشاكل في المجموعات
    if message.text.startswith("/"):
        await message.delete()
        
    url = await YouTube.url(message)
    if url:
        if not await YouTube.exists(url):
            return await message.reply_text(_["song_5"])
        mystic = await message.reply_text(_["play_1"])
        (
            title,
            duration_min,
            duration_sec,
            thumbnail,
            vidid,
        ) = await YouTube.details(url)
        if str(duration_min) == "None":
            return await mystic.edit_text(_["song_3"])
        if int(duration_sec) > SONG_DOWNLOAD_DURATION_LIMIT:
            return await mystic.edit_text(
                _["play_4"].format(
                    SONG_DOWNLOAD_DURATION, duration_min
                )
            )
        buttons = song_markup(_, vidid)
        await mystic.delete()
        await message.reply_photo(
            thumbnail,
            caption=_["song_4"].format(title),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    else:
        if len(message.command) < 2:
            return await message.reply_text(_["song_2"])
    
    mystic = await message.reply_text(_["play_1"])
    query = message.text.split(None, 1)[1]
    try:
        (
            title,
            duration_min,
            duration_sec,
            thumbnail,
            vidid,
        ) = await YouTube.details(query)
    except:
        return await mystic.edit_text(_["play_3"])
    if str(duration_min) == "None":
        return await mystic.edit_text(_["song_3"])
    if int(duration_sec) > SONG_DOWNLOAD_DURATION_LIMIT:
        return await mystic.edit_text(
            _["play_6"].format(SONG_DOWNLOAD_DURATION, duration_min)
        )
    buttons = song_markup(_, vidid)
    await mystic.delete()
    await message.reply_photo(
        thumbnail,
        caption=_["song_4"].format(title),
        reply_markup=InlineKeyboardMarkup(buttons),
    )

@app.on_callback_query(filters.regex(pattern=r"song_back") & ~BANNED_USERS)
@languageCB
async def songs_back_helper(client, callback_query: CallbackQuery, _):
    callback_data = callback_query.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    stype, vidid = callback_request.split("|")
    buttons = song_markup(_, vidid)
    await callback_query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_callback_query(filters.regex(pattern=r"song_helper") & ~BANNED_USERS)
@languageCB
async def song_helper_cb(client, callback_query: CallbackQuery, _):
    callback_data = callback_query.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    stype, vidid = callback_request.split("|")
    try:
        await callback_query.answer(_["song_6"], show_alert=True)
    except:
        pass
    if stype == "audio":
        try:
            formats_available, link = await YouTube.formats(
                vidid, True
            )
        except:
            return await callback_query.edit_message_text(_["song_7"])
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        done = []
        for x in formats_available:
            check = x["format"]
            if "audio" in check:
                if x["filesize"] is None:
                    continue
                form = x["format_note"].title()
                if form not in done:
                    done.append(form)
                else:
                    continue
                sz = convert_bytes(x["filesize"])
                fom = x["format_id"]
                keyboard.inline_keyboard.append(
                    [
                        InlineKeyboardButton(
                            text=f"{form} Quality Audio = {sz}",
                            callback_data=f"song_download {stype}|{fom}|{vidid}",
                        ),
                    ]
                )
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data=f"song_back {stype}|{vidid}",
                ),
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"],
                    callback_data=f"close"
                ),
            ]
        )
        await callback_query.edit_message_reply_markup(
            reply_markup=keyboard
        )
    else:
        try:
            formats_available, link = await YouTube.formats(
                vidid, True
            )
        except Exception as e:
            print(e)
            return await callback_query.edit_message_text(_["song_7"])
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        done = [160, 133, 134, 135, 136, 137, 298, 299, 264, 304, 266]
        for x in formats_available:
            check = x["format"]
            if x["filesize"] is None:
                continue
            if int(x["format_id"]) not in done:
                continue
            sz = convert_bytes(x["filesize"])
            ap = check.split("-")[1]
            to = f"{ap} = {sz}"
            keyboard.inline_keyboard.append(
                [
                    InlineKeyboardButton(
                        text=to,
                        callback_data=f"song_download {stype}|{x['format_id']}|{vidid}",
                    ),
                ]
            )
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data=f"song_back {stype}|{vidid}",
                ),
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"],
                    callback_data=f"close"
                ),
            ]
        )
        await callback_query.edit_message_reply_markup(
            reply_markup=keyboard
        )

# Downloading Songs Here

@app.on_callback_query(
    filters.regex(pattern=r"song_download") & ~BANNED_USERS
)
@languageCB
async def song_download_cb(client, callback_query: CallbackQuery, _) :
    try:
        await callback_query.answer("ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ...")
    except:
        pass
    callback_data = callback_query.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    stype, format_id, vidid = callback_request.split("|")
    mystic = await callback_query.edit_message_text(_["song_8"])
    yturl = f"https://www.youtube.com/watch?v={vidid}"
    
    # جلب المعلومات فقط للاسم والمدة
    with yt_dlp.YoutubeDL({"quiet": True}) as ytdl:
        x = ytdl.extract_info(yturl, download=False)
    
    title = (x["title"]).title()
    title = re.sub("\W+", " ", title)
    
    try:
        thumb_image_path = await callback_query.message.download()
    except:
        thumb_image_path = None
        
    duration = x["duration"]
    
    if stype == "video":
        if thumb_image_path:
            width = callback_query.message.photo.width
            height = callback_query.message.photo.height
        else:
            width = 1280
            height = 720
            
        try:
            # هنا التغيير: استخدام الدالة الداخلية بدلاً من الخارجية
            loop = asyncio.get_event_loop()
            file_path = await loop.run_in_executor(None, download_internal, yturl, "video", format_id)
        except Exception as e:
            return await mystic.edit_text(_["song_9"].format(e))
            
        med = InputMediaVideo(
            media=file_path,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb_image_path,
            caption=title,
            supports_streaming=True,
        )
        await mystic.edit_text(_["song_11"])
        await app.send_chat_action(
            chat_id=callback_query.message.chat.id,
            action="upload_video",
        )
        try:
            await callback_query.edit_message_media(media=med)
        except Exception as e:
            print(e)
            return await mystic.edit_text(_["song_10"])
        os.remove(file_path)
        if thumb_image_path: os.remove(thumb_image_path)
            
    elif stype == "audio":
        try:
            # هنا التغيير: استخدام الدالة الداخلية بدلاً من الخارجية
            loop = asyncio.get_event_loop()
            filename = await loop.run_in_executor(None, download_internal, yturl, "audio", format_id)
        except Exception as e:
            return await mystic.edit_text(_["song_9"].format(e))
            
        med = InputMediaAudio(
            media=filename,
            caption=title,
            thumb=thumb_image_path,
            title=title,
            performer=x["uploader"],
        )
        await mystic.edit_text(_["song_11"])
        await app.send_chat_action(
            chat_id=callback_query.message.chat.id,
            action="upload_audio",
        )
        try:
            await callback_query.edit_message_media(media=med)
        except Exception as e:
            print(e)
            return await mystic.edit_text(_["song_10"])
        os.remove(filename)
        if thumb_image_path: os.remove(thumb_image_path)
