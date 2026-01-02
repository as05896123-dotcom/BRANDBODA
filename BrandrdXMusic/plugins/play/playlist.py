import asyncio
import os
import time
import traceback
from random import randint, choice
from time import time
from typing import Dict, List, Union

import requests
from pykeyboard import InlineKeyboard
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from youtube_search import YoutubeSearch

from config import BANNED_USERS, SERVER_PLAYLIST_LIMIT
from BrandrdXMusic import Carbon, app
from BrandrdXMusic.utils.decorators.language import language, languageCB
from BrandrdXMusic.utils.inline.playlist import (
    botplaylist_markup,
    get_playlist_markup,
    warning_markup,
)
from BrandrdXMusic.utils.pastebin import HottyBin
from BrandrdXMusic.utils.stream.stream import stream
from BrandrdXMusic.core.mongo import mongodb

# تعريف متغيرات الحماية من السبام
user_last_message_time = {}
user_command_count = {}
SPAM_THRESHOLD = 2
SPAM_WINDOW_SECONDS = 5

playlistdb = mongodb.playlist
playlist = []

# قائمة القلوب المطلوبة
HEART_EMOJIS = ["💖", "🤍", "💕", "🤎"]

# --- دوال قاعدة البيانات ---

async def _get_playlists(chat_id: int) -> Dict[str, int]:
    _notes = await playlistdb.find_one({"chat_id": chat_id})
    if not _notes:
        return {}
    return _notes["notes"]


async def get_playlist_names(chat_id: int) -> List[str]:
    _notes = []
    for note in await _get_playlists(chat_id):
        _notes.append(note)
    return _notes


async def get_playlist(chat_id: int, name: str) -> Union[bool, dict]:
    name = name
    _notes = await _get_playlists(chat_id)
    if name in _notes:
        return _notes[name]
    else:
        return False


async def save_playlist(chat_id: int, name: str, note: dict):
    name = name
    _notes = await _get_playlists(chat_id)
    _notes[name] = note
    await playlistdb.update_one(
        {"chat_id": chat_id}, {"$set": {"notes": _notes}}, upsert=True
    )


async def delete_playlist(chat_id: int, name: str) -> bool:
    notesd = await _get_playlists(chat_id)
    name = name
    if name in notesd:
        del notesd[name]
        await playlistdb.update_one(
            {"chat_id": chat_id},
            {"$set": {"notes": notesd}},
            upsert=True,
        )
        return True
    return False


# --- الأوامر ---

@app.on_message(filters.command(["playlist", "قائمتي", "قائمة التشغيل", "القائمة", "قائمه", "عرض القائمة", "ماي ليست"], prefixes=["/", "!", ".", ""]) & ~BANNED_USERS)
@language
async def check_playlist(client, message: Message, _):
    emo = choice(HEART_EMOJIS)
    user_id = message.from_user.id
    current_time = time()
    last_message_time = user_last_message_time.get(user_id, 0)

    if current_time - last_message_time < SPAM_WINDOW_SECONDS:
        user_last_message_time[user_id] = current_time
        user_command_count[user_id] = user_command_count.get(user_id, 0) + 1
        if user_command_count[user_id] > SPAM_THRESHOLD:
            hu = await message.reply_text(
                f"**{message.from_user.mention} ➜ رجـاءً لا تـكـرر الأمـر بـسـرعـة {emo}**"
            )
            await asyncio.sleep(3)
            await hu.delete()
            return
    else:
        user_command_count[user_id] = 1
        user_last_message_time[user_id] = current_time

    _playlist = await get_playlist_names(message.from_user.id)
    if _playlist:
        get = await message.reply_text(f"**جـاري جـلـب قـائـمـتـك الـتـشـغـيـلـيـة... {emo}**")
    else:
        return await message.reply_text(f"**قـائـمـة الـتـشـغـيـل الـخـاصـة بـك فـارغـة {emo}**")
    
    msg = "**هـذه هـي قـائـمـة الـتـشـغـيـل الـخـاصـة بـك:**\n"
    count = 0
    for shikhar in _playlist:
        _note = await get_playlist(message.from_user.id, shikhar)
        title = _note["title"]
        title = title.title()
        duration = _note["duration"]
        count += 1
        msg += f"\n\n{count}- {title[:70]}\n"
        msg += f"الـمـدة: {duration}"
    
    link = await HottyBin(msg)
    lines = msg.count("\n")
    if lines >= 17:
        car = os.linesep.join(msg.split(os.linesep)[:17])
    else:
        car = msg
    
    try:
        carbon = await Carbon.generate(car, randint(100, 10000000000))
        await get.delete()
        await message.reply_photo(carbon, caption=f"**[اضـغـط هـنـا لـعـرض الـقـائـمـة كـامـلـة]({link}) {emo}**")
    except:
        await get.edit_text(msg)


async def get_keyboard(_, user_id):
    keyboard = InlineKeyboard(row_width=5)
    _playlist = await get_playlist_names(user_id)
    count = len(_playlist)
    for x in _playlist:
        _note = await get_playlist(user_id, x)
        title = _note["title"]
        title = title.title()
        keyboard.row(
            InlineKeyboardButton(
                text=title,
                callback_data=f"del_playlist {x}",
            )
        )
    keyboard.row(
        InlineKeyboardButton(
            text="حـذف الـقـائـمـة بـالـكـامـل",
            callback_data=f"delete_warning",
        ),
        InlineKeyboardButton(text="إغـلاق", callback_data=f"close"),
    )
    return keyboard, count


@app.on_message(filters.command(["delplaylist", "حذف القائمة", "حذف من القائمة", "حذف اغنية", "مسح القائمة"], prefixes=["/", "!", ".", ""]) & ~BANNED_USERS)
@language
async def del_plist_msg(client, message: Message, _):
    emo = choice(HEART_EMOJIS)
    user_id = message.from_user.id
    current_time = time()
    last_message_time = user_last_message_time.get(user_id, 0)

    if current_time - last_message_time < SPAM_WINDOW_SECONDS:
        user_last_message_time[user_id] = current_time
        user_command_count[user_id] = user_command_count.get(user_id, 0) + 1
        if user_command_count[user_id] > SPAM_THRESHOLD:
            hu = await message.reply_text(
                f"**{message.from_user.mention} ➜ رجـاءً لا تـكـرر الأمـر بـسـرعـة {emo}**"
            )
            await asyncio.sleep(3)
            await hu.delete()
            return
    else:
        user_command_count[user_id] = 1
        user_last_message_time[user_id] = current_time

    _playlist = await get_playlist_names(message.from_user.id)
    if _playlist:
        get = await message.reply_text(f"**جـاري جـلـب قـائـمـة الـحـذف... {emo}**")
    else:
        return await message.reply_text(f"**قـائـمـة الـتـشـغـيـل فـارغـة بـالـفـعـل {emo}**")
    
    keyboard, count = await get_keyboard(_, message.from_user.id)
    await get.edit_text(f"**لـديـك {count} أغـنـيـة فـي الـقـائـمـة، اضـغـط لـحـذفـهـا:**", reply_markup=keyboard)


@app.on_callback_query(filters.regex("play_playlist") & ~BANNED_USERS)
@languageCB
async def play_playlist(client, CallbackQuery, _):
    emo = choice(HEART_EMOJIS)
    callback_data = CallbackQuery.data.strip()
    mode = callback_data.split(None, 1)[1]
    user_id = CallbackQuery.from_user.id
    _playlist = await get_playlist_names(user_id)
    if not _playlist:
        try:
            return await CallbackQuery.answer(
                "قـائـمـة الـتـشـغـيـل فـارغـة",
                show_alert=True,
            )
        except:
            return
    chat_id = CallbackQuery.message.chat.id
    user_name = CallbackQuery.from_user.first_name
    await CallbackQuery.message.delete()
    result = []
    try:
        await CallbackQuery.answer()
    except:
        pass
    video = True if mode == "v" else None
    mystic = await CallbackQuery.message.reply_text(f"**جـاري بـدء تـشـغـيـل قـائـمـتـك {emo}...**")
    for vidids in _playlist:
        result.append(vidids)
    try:
        await stream(
            _,
            mystic,
            user_id,
            result,
            chat_id,
            user_name,
            CallbackQuery.message.chat.id,
            video,
            streamtype="playlist",
            forceplay=None,
        )
    except Exception as e:
        # Debugging info
        traceback.print_exc()
        ex_type = type(e).__name__
        err = e if ex_type == "AssistantErr" else f"حـدث خـطـأ: {ex_type}"
        return await mystic.edit_text(err)
    return await mystic.delete()


@app.on_message(
    filters.command(["playplaylist", "vplayplaylist", "تشغيل القائمة", "تشغيل قائمتي", "بلاي ماي ليست", "شغل القائمة"], prefixes=["/", "!", ".", ""]) & ~BANNED_USERS & filters.group
)
@languageCB
async def play_playlist_command(client, message, _):
    emo = choice(HEART_EMOJIS)
    user_id = message.from_user.id
    _playlist = await get_playlist_names(user_id)
    if not _playlist:
        try:
            return await message.reply(
                f"**قـائـمـة الـتـشـغـيـل الـخـاصـة بـك فـارغـة {emo}**",
                quote=True,
            )
        except:
            return

    chat_id = message.chat.id
    user_name = message.from_user.first_name

    try:
        await message.delete()
    except:
        pass

    result = []
    # تحسين منطق الفيديو
    cmd = message.command[0].lower()
    video = True if ("v" in cmd or "فيديو" in cmd) else None
    
    mystic = await message.reply_text(f"**جـاري بـدء تـشـغـيـل قـائـمـتـك {emo}...**")

    for vidids in _playlist:
        result.append(vidids)

    try:
        await stream(
            _,
            mystic,
            user_id,
            result,
            chat_id,
            user_name,
            message.chat.id,
            video,
            streamtype="playlist",
            forceplay=None,
        )
    except Exception as e:
        # Debugging info
        traceback.print_exc()
        ex_type = type(e).__name__
        err = e if ex_type == "AssistantErr" else f"حـدث خـطـأ: {ex_type}"
        return await mystic.edit_text(err)

    return await mystic.delete()


# Combined add_playlist function
@app.on_message(filters.command(["addplaylist", "اضف للقائمة", "اضافة للقائمة", "حفظ في القائمة", "ادد ليست"], prefixes=["/", "!", ".", ""]) & ~BANNED_USERS)
@language
async def add_playlist(client, message: Message, _):
    emo = choice(HEART_EMOJIS)
    if len(message.command) < 2:
        return await message.reply_text(
            f"**طـريـقـة الإضـافـة إلـى قـائـمـتـك الـخـاصـة {emo}:**\n\n"
            f"**يـجـب كـتـابـة اسـم الأغـنـيـة أو الـرابـط بـعـد الأمـر مـبـاشـرة.**\n\n"
            f"**• أمـثـلـة لـلاسـتـخـدام:**\n"
            f"1️⃣ **بـالاسـم:** `ادد ليست سـورة الـبـقـرة`\n"
            f"2️⃣ **بـالـرابـط:** `ادد ليست [رابـط الـفـيـديـو]`"
        )

    query = message.command[1]

    # اضافة قائمة يوتيوب كاملة
    if "youtube.com/playlist" in query:
        adding = await message.reply_text(
            f"**🎧 جـاري إضـافـة أغـانـي قـائـمـة الـيـوتـيـوب لـلـقـائـمـة الـخـاصـة بـك... {emo}**"
        )
        try:
            from pytube import Playlist, YouTube

            playlist = Playlist(query)
            video_urls = playlist.video_urls

        except Exception as e:
            return await message.reply_text(f"خـطـأ: {e}")

        if not video_urls:
            return await message.reply_text(
                "**➻ لـم يـتـم الـعـثـور عـلـى أغـانـي فـي الـرابـط.**"
            )

        user_id = message.from_user.id
        for video_url in video_urls:
            video_id = video_url.split("v=")[-1]

            try:
                yt = YouTube(video_url)
                title = yt.title
                duration = yt.length
            except Exception as e:
                return await message.reply_text(f"خـطـأ فـي جـلـب الـمـعـلـومـات: {e}")

            plist = {
                "videoid": video_id,
                "title": title,
                "duration": duration,
            }

            await save_playlist(user_id, video_id, plist)
            keyboardes = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "حـذف أغـانـي؟",
                            callback_data=f"open_playlist {user_id}",
                        )
                    ]
                ]
            )
        await adding.delete()
        return await message.reply_text(
            text=f"**➻ تـم إضـافـة أغـانـي قـائـمـة الـيـوتـيـوب لـقـائـمـتـك بـنـجـاح {emo}**\n\n**▷ تـحـقـق عـبـر: قائمتي**\n\n▷ **شـغـل عـبـر: بلاي ماي ليست**",
            reply_markup=keyboardes,
        )

    # اضافة رابط فيديو يوتيوب
    if "https://youtu.be" in query or "youtube.com/watch" in query:
        try:
            add = await message.reply_text(
                f"**🎧 جـاري الإضـافـة... {emo}**"
            )
            from pytube import YouTube

            # استخراج الايدي بطريقة ابسط
            if "youtu.be" in query:
                videoid = query.split("/")[-1].split("?")[0]
            else:
                videoid = query.split("v=")[1].split("&")[0]

            user_id = message.from_user.id
            thumbnail = f"https://img.youtube.com/vi/{videoid}/maxresdefault.jpg"
            _check = await get_playlist(user_id, videoid)
            if _check:
                try:
                    await add.delete()
                    return await message.reply_photo(thumbnail, caption=f"**هـذه الأغـنـيـة مـوجـودة بـالـفـعـل فـي قـائـمـتـك! {emo}**")
                except KeyError:
                    pass

            _count = await get_playlist_names(user_id)
            count = len(_count)
            if count == SERVER_PLAYLIST_LIMIT:
                try:
                    return await message.reply_text(
                        f"**عـذراً، لـقـد وصـلـت لـلـحـد الأقـصـى لـلـقـائـمـة ({SERVER_PLAYLIST_LIMIT}) {emo}**"
                    )
                except KeyError:
                    pass

            try:
                yt = YouTube(f"https://youtu.be/{videoid}")
                title = yt.title
                duration = yt.length
                plist = {
                    "videoid": videoid,
                    "title": title,
                    "duration": duration,
                }
                await save_playlist(user_id, videoid, plist)

                keyboard = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "حـذف مـن الـقـائـمـة",
                                callback_data=f"remove_playlist {videoid}",
                            )
                        ]
                    ]
                )
                await add.delete()
                await message.reply_photo(
                    thumbnail,
                    caption=f"**➻ تـمـت الإضـافـة لـقـائـمـتـك بـنـجـاح {emo}**\n\n**➥ تـحـقـق عـبـر: قائمتي**\n**➥ لـلـحـذف: حذف القائمة**",
                    reply_markup=keyboard,
                )
            except Exception as e:
                print(f"Error: {e}")
                await message.reply_text(str(e))
        except Exception as e:
            return await message.reply_text(str(e))
    else:
        # البحث بالاسم
        from BrandrdXMusic import YouTube

        query = " ".join(message.command[1:])
        
        try:
            results = YoutubeSearch(query, max_results=1).to_dict()
            if not results:
                 return await message.reply_text("**لـم يـتـم الـعـثـور عـلـى نـتـائـج.**")
            
            link = f"https://youtube.com{results[0]['url_suffix']}"
            title = results[0]["title"][:40]
            thumbnail = results[0]["thumbnails"][0]
            thumb_name = f"{title}.jpg"
            thumb = requests.get(thumbnail, allow_redirects=True)
            open(thumb_name, "wb").write(thumb.content)
            videoid = results[0]["id"]
            
            user_id = message.from_user.id
            _check = await get_playlist(user_id, videoid)
            if _check:
                try:
                    return await message.reply_photo(thumbnail, caption=f"**هـذه الأغـنـيـة مـوجـودة بـالـفـعـل فـي قـائـمـتـك! {emo}**")
                except KeyError:
                    pass

            _count = await get_playlist_names(user_id)
            count = len(_count)
            if count == SERVER_PLAYLIST_LIMIT:
                try:
                    return await message.reply_text(
                       f"**عـذراً، لـقـد وصـلـت لـلـحـد الأقـصـى لـلـقـائـمـة ({SERVER_PLAYLIST_LIMIT}) {emo}**"
                    )
                except KeyError:
                    pass

            m = await message.reply(f"**🔄 جـاري الإضـافـة... {emo}**")
            title, duration_min, _, _, _ = await YouTube.details(videoid, True)
            title = (title[:50]).title()
            plist = {
                "videoid": videoid,
                "title": title,
                "duration": duration_min,
            }

            await save_playlist(user_id, videoid, plist)

            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "حـذف مـن الـقـائـمـة",
                            callback_data=f"remove_playlist {videoid}",
                        )
                    ]
                ]
            )
            await m.delete()
            await message.reply_photo(
                thumbnail,
                caption=f"**➻ تـمـت الإضـافـة لـقـائـمـتـك بـنـجـاح {emo}**\n\n**➥ تـحـقـق عـبـر: قائمتي**\n**➥ لـلـحـذف: حذف القائمة**",
                reply_markup=keyboard,
            )
            try:
                os.remove(thumb_name)
            except:
                pass

        except KeyError:
            return await message.reply_text("حـدث خـطـأ فـي الـبـيـانـات.")
        except Exception as e:
            pass


@app.on_callback_query(filters.regex("open_playlist") & ~BANNED_USERS)
@languageCB
async def open_playlist(client, CallbackQuery, _):
    emo = choice(HEART_EMOJIS)
    _playlist = await get_playlist_names(CallbackQuery.from_user.id)
    if _playlist:
        get = await CallbackQuery.message.edit_text(f"**جـاري جـلـب الـقـائـمـة... {emo}**")
    else:
        return await CallbackQuery.message.edit_text(f"**الـقـائـمـة فـارغـة {emo}**")
    keyboard, count = await get_keyboard(_, CallbackQuery.from_user.id)
    await get.edit_text(f"**لـديـك {count} أغـنـيـة فـي الـقـائـمـة:**", reply_markup=keyboard)


@app.on_callback_query(filters.regex("remove_playlist") & ~BANNED_USERS)
@languageCB
async def del_plist(client, CallbackQuery, _):
    emo = choice(HEART_EMOJIS)
    callback_data = CallbackQuery.data.strip()
    videoid = callback_data.split(None, 1)[1]
    deleted = await delete_playlist(CallbackQuery.from_user.id, videoid)
    if deleted:
        try:
            await CallbackQuery.answer(f"تـم الـحـذف بـنـجـاح {emo}", show_alert=True)
        except:
            pass
    else:
        try:
            return await CallbackQuery.answer("حـدث خـطـأ او الأغـنـيـة غـيـر مـوجـودة", show_alert=True)
        except:
            return
    keyboards = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "اسـتـرجـاع الأغـنـيـة", callback_data=f"recover_playlist {videoid}"
                )
            ]
        ]
    )
    return await CallbackQuery.edit_message_text(
        text=f"**➻ تـم حـذف الأغـنـيـة مـن قـائـمـتـك {emo}**\n\n**➥ لـلاسـتـرجـاع اضـغـط الـزر فـي الأسـفـل.**",
        reply_markup=keyboards,
    )


@app.on_callback_query(filters.regex("recover_playlist") & ~BANNED_USERS)
@languageCB
async def recover_playlist(client, CallbackQuery, _):
    emo = choice(HEART_EMOJIS)
    from BrandrdXMusic import YouTube

    callback_data = CallbackQuery.data.strip()
    videoid = callback_data.split(None, 1)[1]
    user_id = CallbackQuery.from_user.id
    _check = await get_playlist(user_id, videoid)
    if _check:
        try:
            return await CallbackQuery.answer("مـوجـودة بـالـفـعـل!", show_alert=True)
        except:
            return
    _count = await get_playlist_names(user_id)
    count = len(_count)
    if count == SERVER_PLAYLIST_LIMIT:
        try:
            return await CallbackQuery.answer(
                "الـذاكـرة مـمـتـلـئـة!",
                show_alert=True,
            )
        except:
            return
    (
        title,
        duration_min,
        duration_sec,
        thumbnail,
        vidid,
    ) = await YouTube.details(videoid, True)
    title = (title[:50]).title()
    plist = {
        "videoid": vidid,
        "title": title,
        "duration": duration_min,
    }
    await save_playlist(user_id, videoid, plist)
    try:
        title = (title[:30]).title()
        keyboardss = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "حـذف مـجـدداً", callback_data=f"remove_playlist {videoid}"
                    )
                ]
            ]
        )
        return await CallbackQuery.edit_message_text(
            text=f"**➻ تـم اسـتـرجـاع الأغـنـيـة لـلـقـائـمـة {emo}**",
            reply_markup=keyboardss,
        )
    except:
        return


@app.on_callback_query(filters.regex("add_playlist") & ~BANNED_USERS)
@languageCB
async def add_playlist_cb(client, CallbackQuery, _):
    await CallbackQuery.answer(
        "طـريـقـة الإضـافـة:\nاكـتـب الأمـر وبـجـانـبـه اسـم الأغـنـيـة\nمـثـال: ادد ليست سـورة الـبـقـرة",
        show_alert=True,
    )


@app.on_callback_query(filters.regex("branded_playlist") & ~BANNED_USERS)
@languageCB
async def add_playlists_branded(client, CallbackQuery, _):
    emo = choice(HEART_EMOJIS)
    callback_data = CallbackQuery.data.strip()
    videoid = callback_data.split(None, 1)[1]
    user_id = CallbackQuery.from_user.id
    from BrandrdXMusic import YouTube

    _check = await get_playlist(user_id, videoid)
    if _check:
        try:
            return await CallbackQuery.answer("مـوجـودة بـالـفـعـل فـي قـائـمـتـك!", show_alert=True)
        except:
            return
    _count = await get_playlist_names(user_id)
    count = len(_count)
    if count == SERVER_PLAYLIST_LIMIT:
        try:
            return await CallbackQuery.answer(
                "قـائـمـتـك مـمـتـلـئـة بـالـكـامـل!",
                show_alert=True,
            )
        except:
            return
    (
        title,
        duration_min,
        duration_sec,
        thumbnail,
        vidid,
    ) = await YouTube.details(videoid, True)
    title = (title[:50]).title()
    plist = {
        "videoid": vidid,
        "title": title,
        "duration": duration_min,
    }
    await save_playlist(user_id, videoid, plist)
    try:
        title = (title[:30]).title()
        return await CallbackQuery.answer(
            f"تـمـت الإضـافـة: {title} {emo}", show_alert=True
        )
    except:
        return


@app.on_message(filters.command(["delallplaylist", "حذف القائمة كلها", "حذف الكل", "فرمتة القائمة"], prefixes=["/", "!", ".", ""]) & ~BANNED_USERS)
@language
async def delete_all_playlists(client, message, _):
    emo = choice(HEART_EMOJIS)
    user_id = message.from_user.id
    _playlist = await get_playlist_names(user_id)
    if _playlist:
        try:
            upl = warning_markup(_)
            await message.reply_text(f"**هـل أنـت مـتـأكـد أنـك تـريـد حـذف الـقـائـمـة بـالـكـامـل؟ {emo}**", reply_markup=upl)
        except:
            pass
    else:
        await message.reply_text("**الـقـائـمـة فـارغـة بـالـفـعـل.**")


@app.on_callback_query(filters.regex("del_playlist") & ~BANNED_USERS)
@languageCB
async def del_plist_cb(client, CallbackQuery, _):
    emo = choice(HEART_EMOJIS)
    callback_data = CallbackQuery.data.strip()
    videoid = callback_data.split(None, 1)[1]
    user_id = CallbackQuery.from_user.id
    deleted = await delete_playlist(CallbackQuery.from_user.id, videoid)
    if deleted:
        try:
            await CallbackQuery.answer(f"تـم الـحـذف {emo}", show_alert=True)
        except:
            pass
    else:
        try:
            return await CallbackQuery.answer("حـدث خـطـأ.", show_alert=True)
        except:
            return
    keyboard, count = await get_keyboard(_, user_id)
    return await CallbackQuery.edit_message_reply_markup(reply_markup=keyboard)


@app.on_callback_query(filters.regex("delete_whole_playlist") & ~BANNED_USERS)
@languageCB
async def del_whole_playlist(client, CallbackQuery, _):
    emo = choice(HEART_EMOJIS)
    _playlist = await get_playlist_names(CallbackQuery.from_user.id)
    for x in _playlist:
        await delete_playlist(CallbackQuery.from_user.id, x)
    return await CallbackQuery.edit_message_text(f"**تـم حـذف الـقـائـمـة بـالـكـامـل بـنـجـاح {emo}**")


@app.on_callback_query(filters.regex("get_playlist_playmode") & ~BANNED_USERS)
@languageCB
async def get_playlist_playmode_(client, CallbackQuery, _):
    try:
        await CallbackQuery.answer()
    except:
        pass
    buttons = get_playlist_markup(_)
    return await CallbackQuery.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@app.on_callback_query(filters.regex("delete_warning") & ~BANNED_USERS)
@languageCB
async def delete_warning_message(client, CallbackQuery, _):
    emo = choice(HEART_EMOJIS)
    try:
        await CallbackQuery.answer()
    except:
        pass
    upl = warning_markup(_)
    return await CallbackQuery.edit_message_text(f"**هـل أنـت مـتـأكـد مـن الـحـذف؟ لا يـمـكـن الـتـراجـع! {emo}**", reply_markup=upl)


@app.on_callback_query(filters.regex("home_play") & ~BANNED_USERS)
@languageCB
async def home_play_(client, CallbackQuery, _):
    try:
        await CallbackQuery.answer()
    except:
        pass
    buttons = botplaylist_markup(_)
    return await CallbackQuery.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@app.on_callback_query(filters.regex("del_back_playlist") & ~BANNED_USERS)
@languageCB
async def del_back_playlist(client, CallbackQuery, _):
    user_id = CallbackQuery.from_user.id
    _playlist = await get_playlist_names(user_id)
    if _playlist:
        try:
            await CallbackQuery.answer("الـرجـوع...", show_alert=True)
        except:
            pass
    else:
        try:
            return await CallbackQuery.answer("الـقـائـمـة فـارغـة", show_alert=True)
        except:
            return
    keyboard, count = await get_keyboard(_, user_id)
    return await CallbackQuery.edit_message_text(
        f"**لـديـك {count} أغـنـيـة فـي الـقـائـمـة:**", reply_markup=keyboard
    )
