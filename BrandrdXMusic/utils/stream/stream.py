import os
from random import randint
from typing import Union
import asyncio
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from BrandrdXMusic import app, YouTube
from BrandrdXMusic.core.call import Hotty
from BrandrdXMusic.misc import db
from BrandrdXMusic.utils import seconds_to_min, time_to_seconds

# [CORE MIGRATION] تعديل المسار
from BrandrdXMusic.core.database import (
    add_active_video_chat,
    is_active_chat,
)

from BrandrdXMusic.utils.exceptions import AssistantErr
from BrandrdXMusic.utils.inline import (
    aq_markup,
    close_markup,
    stream_markup,
)
from BrandrdXMusic.utils.pastebin import HottyBin as brandedBin
from BrandrdXMusic.utils.stream.queue import put_queue, put_queue_index
from BrandrdXMusic.utils.thumbnails import get_thumb
import config

# --- الكود الأساسي ---

async def stream(
    _,
    mystic,
    user_id,
    result,
    chat_id,
    user_name,
    original_chat_id,
    video: Union[bool, str] = None,
    streamtype: Union[bool, str] = None,
    spotify: Union[bool, str] = None,
    forceplay: Union[bool, str] = None,
):
    if not result:
        return

    if forceplay:
        # [FIX] استبدال force_stop_stream بـ stop_stream
        await Hotty.stop_stream(chat_id)

    # 1. PLAYLIST
    if streamtype == "playlist":
        msg = f"{_['play_19']}\n\n"
        count = 0
        for search in result:
            if int(count) == config.PLAYLIST_FETCH_LIMIT:
                continue
            try:
                (
                    title,
                    duration_min,
                    duration_sec,
                    thumbnail,
                    vidid,
                ) = await YouTube.details(search, False if spotify else True)
            except:
                continue

            if str(duration_min) == "None":
                continue
            if duration_sec > config.DURATION_LIMIT:
                continue

            if await is_active_chat(chat_id):
                await put_queue(
                    chat_id,
                    original_chat_id,
                    f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if video else "audio",
                )
                position = len(db.get(chat_id)) - 1
                count += 1
                msg += f"{count}. {title[:70]}\n"
                msg += f"{_['play_20']} {position}\n\n"
            else:
                if not forceplay:
                    db[chat_id] = []
                status = True if video else None
                try:
                    file_path, direct = await YouTube.download(
                        vidid, mystic, video=status, videoid=True
                    )
                except:
                    return await mystic.edit_text(_["play_3"])

                # [FIX] إزالة image
                await Hotty.join_call(
                    chat_id,
                    original_chat_id,
                    file_path,
                    video=status,
                )
                await put_queue(
                    chat_id,
                    original_chat_id,
                    file_path if direct else f"vid_{vidid}",
                    title,
                    duration_min,
                    user_name,
                    vidid,
                    user_id,
                    "video" if video else "audio",
                    forceplay=forceplay,
                )
                img = await get_thumb(vidid)
                button = stream_markup(_, vidid, chat_id)
                run = await app.send_photo(
                    original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{vidid}",
                        title[:18],
                        duration_min,
                        user_name,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"

        if count == 0:
            return
        else:
            link = await brandedBin(msg)
            lines = msg.count("\n")
            if lines >= 17:
                car = os.linesep.join(msg.split(os.linesep)[:17])
            else:
                car = msg
            try:
                from BrandrdXMusic import Carbon
                carbon = await Carbon.generate(car, randint(100, 10000000))
            except:
                carbon = config.STREAM_IMG_URL
            
            queue_buttons = [
                [
                    InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"),
                    InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}"),
                ],
                [InlineKeyboardButton(text="إغلاق", callback_data="close")]
            ]
            
            return await app.send_photo(
                original_chat_id,
                photo=carbon,
                caption=_["play_21"].format(position, link),
                reply_markup=InlineKeyboardMarkup(queue_buttons),
            )

    # 2. YOUTUBE
    elif streamtype == "youtube":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        duration_min = result["duration_min"]
        thumbnail = result["thumb"]
        status = True if video else None

        try:
            file_path, direct = await YouTube.download(
                vidid, mystic, videoid=True, video=status
            )
        except:
            return await mystic.edit_text(_["play_3"])

        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path if direct else f"vid_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )
            img = await get_thumb(vidid)
            position = len(db.get(chat_id)) - 1
            
            queue_buttons = [
                [
                    InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"),
                    InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}"),
                ],
                [InlineKeyboardButton(text="إغلاق", callback_data="close")]
            ]
            
            await app.send_photo(
                chat_id=original_chat_id,
                photo=img,
                caption=_["queue_4"].format(
                    position, title[:18], duration_min, user_name
                ),
                reply_markup=InlineKeyboardMarkup(queue_buttons),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            
            # [FIX] إزالة image
            await Hotty.join_call(
                chat_id,
                original_chat_id,
                file_path,
                video=status,
            )
            await put_queue(
                chat_id,
                original_chat_id,
                file_path if direct else f"vid_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            img = await get_thumb(vidid)
            button = stream_markup(_, vidid, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{vidid}",
                    title[:18],
                    duration_min,
                    user_name,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"

    # 3. SOUNDCLOUD
    elif streamtype == "soundcloud":
        file_path = result["filepath"]
        title = result["title"]
        duration_min = result["duration_min"]
        
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
            )
            position = len(db.get(chat_id)) - 1
            
            queue_buttons = [
                [
                    InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"),
                    InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}"),
                ],
                [InlineKeyboardButton(text="إغلاق", callback_data="close")]
            ]

            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:18], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(queue_buttons),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await Hotty.join_call(chat_id, original_chat_id, file_path, video=None)
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "audio",
                forceplay=forceplay,
            )
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.SOUNCLOUD_IMG_URL,
                caption=_["stream_1"].format(
                    config.SUPPORT_CHAT, title[:23], duration_min, user_name
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

    # 4. TELEGRAM
    elif streamtype == "telegram":
        file_path = result["path"]
        link = result["link"]
        title = (result["title"]).title()
        duration_min = result["dur"]
        status = True if video else None
        
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            
            queue_buttons = [
                [
                    InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"),
                    InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}"),
                ],
                [InlineKeyboardButton(text="إغلاق", callback_data="close")]
            ]

            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:18], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(queue_buttons),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            await Hotty.join_call(chat_id, original_chat_id, file_path, video=status)
            await put_queue(
                chat_id,
                original_chat_id,
                file_path,
                title,
                duration_min,
                user_name,
                streamtype,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            if video:
                await add_active_video_chat(chat_id)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.TELEGRAM_VIDEO_URL if video else config.TELEGRAM_AUDIO_URL,
                caption=_["stream_1"].format(link, title[:23], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

    # 5. LIVE
    elif streamtype == "live":
        link = result["link"]
        vidid = result["vidid"]
        title = (result["title"]).title()
        thumbnail = result["thumb"]
        duration_min = "Live Track"
        status = True if video else None
        
        if await is_active_chat(chat_id):
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            
            queue_buttons = [
                [
                    InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"),
                    InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}"),
                ],
                [InlineKeyboardButton(text="إغلاق", callback_data="close")]
            ]

            await app.send_message(
                chat_id=original_chat_id,
                text=_["queue_4"].format(position, title[:18], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(queue_buttons),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            n, file_path = await YouTube.video(link)
            if n == 0:
                raise AssistantErr(_["str_3"])
            
            # [FIX] إزالة image
            await Hotty.join_call(
                chat_id,
                original_chat_id,
                file_path,
                video=status,
            )
            await put_queue(
                chat_id,
                original_chat_id,
                f"live_{vidid}",
                title,
                duration_min,
                user_name,
                vidid,
                user_id,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            img = await get_thumb(vidid)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{vidid}",
                    title[:23],
                    duration_min,
                    user_name,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

    # 6. INDEX
    elif streamtype == "index":
        link = result
        title = "ɪɴᴅᴇx ᴏʀ ᴍ3ᴜ8 ʟɪɴᴋ"
        duration_min = "00:00"
        
        if await is_active_chat(chat_id):
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video" if video else "audio",
            )
            position = len(db.get(chat_id)) - 1
            
            queue_buttons = [
                [
                    InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"),
                    InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}"),
                ],
                [InlineKeyboardButton(text="إغلاق", callback_data="close")]
            ]

            await mystic.edit_text(
                text=_["queue_4"].format(position, title[:27], duration_min, user_name),
                reply_markup=InlineKeyboardMarkup(queue_buttons),
            )
        else:
            if not forceplay:
                db[chat_id] = []
            
            # [FIX] إزالة image (تأكدنا من عدم وجوده أصلاً هنا ولكن للفحص)
            await Hotty.join_call(
                chat_id,
                original_chat_id,
                link,
                video=True if video else None,
            )
            await put_queue_index(
                chat_id,
                original_chat_id,
                "index_url",
                title,
                duration_min,
                user_name,
                link,
                "video" if video else "audio",
                forceplay=forceplay,
            )
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                original_chat_id,
                photo=config.STREAM_IMG_URL,
                caption=_["stream_2"].format(user_name),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await mystic.delete()
