import asyncio
import os
import time
import json
import traceback
from random import randint, choice
from typing import Dict, List, Union

# Network & File I/O (Async)
import aiohttp
import aiofiles

# Pyrogram & Types
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery

# Search & Extraction (Async)
from youtubesearchpython.__future__ import VideosSearch

# Local Modules
from config import BANNED_USERS, SERVER_PLAYLIST_LIMIT
from BrandrdXMusic import Carbon, app, YouTube
from BrandrdXMusic.utils.decorators.language import language, languageCB
from BrandrdXMusic.utils.inline.playlist import (
    botplaylist_markup,
    get_playlist_markup,
    warning_markup,
)
from BrandrdXMusic.utils.pastebin import HottyBin
from BrandrdXMusic.utils.stream.stream import stream
from BrandrdXMusic.core.mongo import mongodb

# --- Anti-Spam & Memory Management ---
user_last_message_time = {}
user_command_count = {}
SPAM_THRESHOLD = 2
SPAM_WINDOW_SECONDS = 5
CACHE_TTL = 60  # ثانية لتنظيف الكاش

def cleanup_spam_cache():
    """
    Smart GC: Removes only expired keys instead of clearing everything.
    Prevents memory leaks without punishing active users.
    """
    current_time = time.time()
    # Create a list of keys to remove to avoid RuntimeError during iteration
    expired_users = [
        user_id for user_id, timestamp in user_last_message_time.items() 
        if current_time - timestamp > CACHE_TTL
    ]
    
    for user_id in expired_users:
        user_last_message_time.pop(user_id, None)
        user_command_count.pop(user_id, None)

# --- Database Variables ---
playlistdb = mongodb.playlist
HEART_EMOJIS = ["💖", "🤍", "💕", "🤎"]

# --- Database Functions (Optimized) ---

async def _get_playlists(chat_id: int) -> Dict[str, dict]:
    try:
        _notes = await playlistdb.find_one({"chat_id": chat_id})
        if not _notes:
            return {}
        return _notes.get("notes", {})
    except Exception:
        return {}


async def get_playlist_names(chat_id: int) -> List[str]:
    _notes = await _get_playlists(chat_id)
    return list(_notes.keys())


async def get_playlist(chat_id: int, name: str) -> Union[bool, dict]:
    _notes = await _get_playlists(chat_id)
    return _notes.get(name, False)


async def save_playlist(chat_id: int, name: str, note: dict):
    """
    Atomic Update: Uses $set to update specific key directly.
    Safe for concurrency and lighter on DB.
    """
    try:
        await playlistdb.update_one(
            {"chat_id": chat_id},
            {"$set": {f"notes.{name}": note}},
            upsert=True
        )
    except Exception as e:
        traceback.print_exc()


async def save_playlist_bulk(chat_id: int, new_notes: dict):
    """
    Batch Update: Merges new dictionary with existing notes in ONE operation.
    Critical for importing large playlists.
    """
    if not new_notes:
        return
        
    try:
        # We need to fetch current to merge, or use a complex pipeline.
        # Simplest atomic approach for bulk: Fetch -> Merge -> Set
        # Note: $set with dot notation for bulk is messy if keys are dynamic.
        # Safer for bulk:
        current_notes = await _get_playlists(chat_id)
        current_notes.update(new_notes)
        
        await playlistdb.update_one(
            {"chat_id": chat_id},
            {"$set": {"notes": current_notes}},
            upsert=True
        )
    except Exception as e:
        traceback.print_exc()


async def delete_playlist(chat_id: int, name: str) -> bool:
    """
    Atomic Delete: Uses $unset to remove specific key directly.
    """
    try:
        # First check if exists locally to return bool correctly
        # (Optional: can be skipped for pure speed, but needed for logic)
        exists = await get_playlist(chat_id, name)
        if not exists:
            return False

        await playlistdb.update_one(
            {"chat_id": chat_id},
            {"$unset": {f"notes.{name}": ""}}
        )
        
        # Cleanup: If notes is empty, maybe remove doc? (Optional, kept simple)
        return True
    except Exception:
        return False


# --- Helper Functions ---

async def check_spam(user_id: int, message: Message) -> bool:
    """Returns True if user is spamming"""
    cleanup_spam_cache()
    current_time = time.time()
    last_message_time = user_last_message_time.get(user_id, 0)

    if current_time - last_message_time < SPAM_WINDOW_SECONDS:
        user_last_message_time[user_id] = current_time
        user_command_count[user_id] = user_command_count.get(user_id, 0) + 1
        if user_command_count[user_id] > SPAM_THRESHOLD:
            emo = choice(HEART_EMOJIS)
            hu = await message.reply_text(
                f"**{message.from_user.mention} ➜ رجـاءً لا تـكـرر الأمـر بـسـرعـة {emo}**"
            )
            await asyncio.sleep(3)
            await hu.delete()
            return True
    else:
        user_command_count[user_id] = 1
        user_last_message_time[user_id] = current_time
    return False

async def get_keyboard(_, user_id):
    """Generates InlineKeyboardMarkup safely"""
    _playlist = await get_playlist_names(user_id)
    count = len(_playlist)
    
    keyboard = []
    row = []
    for x in _playlist:
        _note = await get_playlist(user_id, x)
        if not _note:
            continue
        title = _note.get("title", "Unknown").title()
        row.append(InlineKeyboardButton(text=title[:20], callback_data=f"del_playlist {x}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton(text="حـذف الـقـائـمـة بـالـكـامـل", callback_data="delete_warning"),
        InlineKeyboardButton(text="إغـلاق", callback_data="close")
    ])
    
    return InlineKeyboardMarkup(keyboard), count

# --- Handlers ---

@app.on_message(filters.command(["playlist", "قائمتي", "قائمة التشغيل", "القائمة", "قائمه", "عرض القائمة", "ماي ليست"], prefixes=["/", "!", ".", ""]) & ~BANNED_USERS)
@language
async def check_playlist(client, message: Message, _):
    if await check_spam(message.from_user.id, message):
        return

    emo = choice(HEART_EMOJIS)
    _playlist = await get_playlist_names(message.from_user.id)
    
    if _playlist:
        get = await message.reply_text(f"**جـاري جـلـب قـائـمـتـك الـتـشـغـيـلـيـة... {emo}**")
    else:
        return await message.reply_text(f"**قـائـمـة الـتـشـغـيـل الـخـاصـة بـك فـارغـة {emo}**")
    
    msg = "**هـذه هـي قـائـمـة الـتـشـغـيـل الـخـاصـة بـك:**\n"
    count = 0
    for shikhar in _playlist:
        _note = await get_playlist(message.from_user.id, shikhar)
        if not _note:
            continue
        title = _note.get("title", "").title()
        duration = _note.get("duration", "")
        count += 1
        msg += f"\n\n{count}- {title[:70]}\n"
        msg += f"الـمـدة: {duration}"
    
    link = await HottyBin(msg)
    
    lines = msg.split("\n")
    if len(lines) >= 17:
        car = "\n".join(lines[:17])
    else:
        car = msg
    
    try:
        # Assuming Carbon.generate is an awaitable coroutine.
        # If it blocks, it should be wrapped, but respecting the "don't rewrite logic unless critical"
        # and assuming library compliance.
        carbon = await Carbon.generate(car, randint(100, 10000000000))
        await get.delete()
        await message.reply_photo(carbon, caption=f"**[اضـغـط هـنـا لـعـرض الـقـائـمـة كـامـلـة]({link}) {emo}**")
    except Exception:
        # Fallback if image generation fails
        await get.edit_text(msg)


@app.on_message(filters.command(["delplaylist", "حذف القائمة", "حذف من القائمة", "حذف اغنية", "مسح القائمة"], prefixes=["/", "!", ".", ""]) & ~BANNED_USERS)
@language
async def del_plist_msg(client, message: Message, _):
    if await check_spam(message.from_user.id, message):
        return

    emo = choice(HEART_EMOJIS)
    _playlist = await get_playlist_names(message.from_user.id)
    
    if _playlist:
        get = await message.reply_text(f"**جـاري جـلـب قـائـمـة الـحـذف... {emo}**")
    else:
        return await message.reply_text(f"**قـائـمـة الـتـشـغـيـل فـارغـة بـالـفـعـل {emo}**")
    
    keyboard, count = await get_keyboard(_, message.from_user.id)
    await get.edit_text(f"**لـديـك {count} أغـنـيـة فـي الـقـائـمـة، اضـغـط لـحـذفـهـا:**", reply_markup=keyboard)


@app.on_callback_query(filters.regex("play_playlist") & ~BANNED_USERS)
@languageCB
async def play_playlist(client, CallbackQuery: CallbackQuery, _):
    emo = choice(HEART_EMOJIS)
    callback_data = CallbackQuery.data.strip()
    mode = callback_data.split(None, 1)[1]
    user_id = CallbackQuery.from_user.id
    
    _playlist = await get_playlist_names(user_id)
    if not _playlist:
        try:
            return await CallbackQuery.answer("قـائـمـة الـتـشـغـيـل فـارغـة", show_alert=True)
        except:
            return

    chat_id = CallbackQuery.message.chat.id
    user_name = CallbackQuery.from_user.first_name
    
    try:
        await CallbackQuery.message.delete()
        await CallbackQuery.answer()
    except:
        pass
        
    video = True if mode == "v" else None
    mystic = await CallbackQuery.message.reply_text(f"**جـاري بـدء تـشـغـيـل قـائـمـتـك {emo}...**")
    
    result = list(_playlist)
    
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
        traceback.print_exc()
        return await mystic.edit_text(f"حـدث خـطـأ اثناء التشغيل: {e}")
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
        return await message.reply(f"**قـائـمـة الـتـشـغـيـل الـخـاصـة بـك فـارغـة {emo}**", quote=True)

    chat_id = message.chat.id
    user_name = message.from_user.first_name

    try:
        await message.delete()
    except:
        pass

    cmd = message.command[0].lower()
    video = True if ("v" in cmd or "فيديو" in cmd) else None
    
    mystic = await message.reply_text(f"**جـاري بـدء تـشـغـيـل قـائـمـتـك {emo}...**")

    result = list(_playlist)

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
        traceback.print_exc()
        return await mystic.edit_text(f"حـدث خـطـأ: {e}")

    return await mystic.delete()


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

    # --- 1. Youtube Playlist Handling (Optimized Batch Update) ---
    if "youtube.com/playlist" in query:
        adding = await message.reply_text(f"**🎧 جـاري إضـافـة أغـانـي قـائـمـة الـيـوتـيـوب... {emo}**")
        try:
            # yt-dlp fast extraction
            proc = await asyncio.create_subprocess_exec(
                "yt-dlp", "--flat-playlist", "-J", "--skip-download", query,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                 return await message.reply_text(f"خـطـأ في جلب القائمة: {stderr.decode()}")

            data = json.loads(stdout)
            video_entries = data.get('entries', [])

            if not video_entries:
                return await message.reply_text("**➻ لـم يـتـم الـعـثـور عـلـى أغـانـي.**")

            user_id = message.from_user.id
            new_tracks = {}
            
            # Prepare data in memory first (Batch Preparation)
            for entry in video_entries:
                if not entry: continue
                video_id = entry.get('id')
                title = entry.get('title', 'Unknown Title')
                duration = entry.get('duration', 0)
                
                if not video_id: continue

                new_tracks[video_id] = {
                    "videoid": video_id,
                    "title": title,
                    "duration": duration,
                }
            
            # Save all at once (One DB Call)
            await save_playlist_bulk(user_id, new_tracks)
            
            keyboardes = InlineKeyboardMarkup([[InlineKeyboardButton("حـذف أغـانـي؟", callback_data=f"open_playlist {user_id}")]])
            await adding.delete()
            return await message.reply_text(
                text=f"**➻ تـم إضـافـة {len(new_tracks)} أغـنـيـة لـقـائـمـتـك بـنـجـاح {emo}**\n\n**▷ تـحـقـق عـبـر: قائمتي**\n**▷ شـغـل عـبـر: بلاي ماي ليست**",
                reply_markup=keyboardes,
            )

        except Exception as e:
            traceback.print_exc()
            return await message.reply_text(f"خـطـأ غير متوقع: {e}")

    # --- 2. Single Video Link (Atomic Update) ---
    if "https://youtu.be" in query or "youtube.com/watch" in query:
        try:
            add = await message.reply_text(f"**🎧 جـاري الإضـافـة... {emo}**")
            
            if "youtu.be" in query:
                videoid = query.split("/")[-1].split("?")[0]
            else:
                videoid = query.split("v=")[1].split("&")[0]

            user_id = message.from_user.id
            thumbnail = f"https://img.youtube.com/vi/{videoid}/maxresdefault.jpg"
            
            if await get_playlist(user_id, videoid):
                await add.delete()
                return await message.reply_photo(thumbnail, caption=f"**هـذه الأغـنـيـة مـوجـودة بـالـفـعـل! {emo}**")

            current_list = await get_playlist_names(user_id)
            if len(current_list) >= SERVER_PLAYLIST_LIMIT:
                 return await message.reply_text(f"**عـذراً، وصـلـت لـلـحـد الأقـصـى ({SERVER_PLAYLIST_LIMIT}) {emo}**")

            try:
                title, duration_min, duration_sec, thumb, vidid = await YouTube.details(videoid, True)
            except Exception:
                title = "Unknown Video"
                duration_min = "00:00"

            plist = {
                "videoid": videoid,
                "title": title,
                "duration": duration_min,
            }
            # Single atomic save
            await save_playlist(user_id, videoid, plist)

            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("حـذف مـن الـقـائـمـة", callback_data=f"remove_playlist {videoid}")]])
            await add.delete()
            await message.reply_photo(
                thumbnail,
                caption=f"**➻ تـمـت الإضـافـة لـقـائـمـتـك بـنـجـاح {emo}**\n\n**➥ تـحـقـق عـبـر: قائمتي**",
                reply_markup=keyboard,
            )
        except Exception as e:
            traceback.print_exc()
            return await message.reply_text(f"خـطـأ: {e}")

    # --- 3. Search Query (Atomic Update) ---
    else:
        query = " ".join(message.command[1:])
        m = await message.reply(f"**🔄 جـاري الإضـافـة... {emo}**")
        
        try:
            search = VideosSearch(query, limit=1)
            result = (await search.next())["result"]
            
            if not result:
                await m.delete()
                return await message.reply_text("**لـم يـتـم الـعـثـور عـلـى نـتـائـج.**")
            
            top_result = result[0]
            videoid = top_result["id"]
            title = top_result["title"][:50]
            duration = top_result["duration"]
            thumbnail = top_result["thumbnails"][0]["url"].split("?")[0]

            user_id = message.from_user.id
            if await get_playlist(user_id, videoid):
                await m.delete()
                return await message.reply_photo(thumbnail, caption=f"**هـذه الأغـنـيـة مـوجـودة بـالـفـعـل! {emo}**")

            current_list = await get_playlist_names(user_id)
            if len(current_list) >= SERVER_PLAYLIST_LIMIT:
                await m.delete()
                return await message.reply_text(f"**الـقـائـمـة مـمـتـلـئـة ({SERVER_PLAYLIST_LIMIT}) {emo}**")

            thumb_name = f"{videoid}.jpg"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(thumbnail) as resp:
                        if resp.status == 200:
                            f = await aiofiles.open(thumb_name, mode='wb')
                            await f.write(await resp.read())
                            await f.close()
            except:
                thumb_name = thumbnail

            plist = {
                "videoid": videoid,
                "title": title,
                "duration": duration,
            }

            # Single atomic save
            await save_playlist(user_id, videoid, plist)

            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("حـذف مـن الـقـائـمـة", callback_data=f"remove_playlist {videoid}")]])
            await m.delete()
            
            try:
                await message.reply_photo(
                    thumb_name,
                    caption=f"**➻ تـمـت الإضـافـة لـقـائـمـتـك بـنـجـاح {emo}**\n\n**➥ تـحـقـق عـبـر: قائمتي**",
                    reply_markup=keyboard,
                )
            except:
                 await message.reply_text(f"**➻ تـمـت الإضـافـة: {title}**", reply_markup=keyboard)

            if os.path.exists(thumb_name) and thumb_name != thumbnail:
                try:
                    os.remove(thumb_name)
                except:
                    pass

        except Exception as e:
            traceback.print_exc()
            await m.edit_text(f"حـدث خـطـأ أثـنـاء الـبـحـث: {e}")


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
        await CallbackQuery.answer(f"تـم الـحـذف بـنـجـاح {emo}", show_alert=True)
    else:
        await CallbackQuery.answer("الأغـنـيـة غـيـر مـوجـودة", show_alert=True)
        return

    keyboards = InlineKeyboardMarkup([[InlineKeyboardButton("اسـتـرجـاع الأغـنـيـة", callback_data=f"recover_playlist {videoid}")]])
    await CallbackQuery.edit_message_text(
        text=f"**➻ تـم حـذف الأغـنـيـة مـن قـائـمـتـك {emo}**\n\n**➥ لـلاسـتـرجـاع اضـغـط الـزر فـي الأسـفـل.**",
        reply_markup=keyboards,
    )


@app.on_callback_query(filters.regex("recover_playlist") & ~BANNED_USERS)
@languageCB
async def recover_playlist(client, CallbackQuery, _):
    emo = choice(HEART_EMOJIS)
    
    callback_data = CallbackQuery.data.strip()
    videoid = callback_data.split(None, 1)[1]
    user_id = CallbackQuery.from_user.id
    
    if await get_playlist(user_id, videoid):
        return await CallbackQuery.answer("مـوجـودة بـالـفـعـل!", show_alert=True)
        
    current_list = await get_playlist_names(user_id)
    if len(current_list) >= SERVER_PLAYLIST_LIMIT:
        return await CallbackQuery.answer("الـذاكـرة مـمـتـلـئـة!", show_alert=True)
    
    try:
        title, duration_min, duration_sec, thumbnail, vidid = await YouTube.details(videoid, True)
    except:
        title = "Unknown Song"
        duration_min = "00:00"

    plist = {
        "videoid": videoid,
        "title": title[:50],
        "duration": duration_min,
    }
    await save_playlist(user_id, videoid, plist)
    
    keyboardss = InlineKeyboardMarkup([[InlineKeyboardButton("حـذف مـجـدداً", callback_data=f"remove_playlist {videoid}")]])
    await CallbackQuery.edit_message_text(
        text=f"**➻ تـم اسـتـرجـاع الأغـنـيـة لـلـقـائـمـة {emo}**",
        reply_markup=keyboardss,
    )


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

    if await get_playlist(user_id, videoid):
        return await CallbackQuery.answer("مـوجـودة بـالـفـعـل!", show_alert=True)
        
    current_list = await get_playlist_names(user_id)
    if len(current_list) >= SERVER_PLAYLIST_LIMIT:
        return await CallbackQuery.answer("الـقـائـمـة مـمـتـلـئـة!", show_alert=True)

    try:
        title, duration_min, _, _, _ = await YouTube.details(videoid, True)
    except:
        title = "Unknown"
        duration_min = "00:00"

    plist = {
        "videoid": videoid,
        "title": title[:50],
        "duration": duration_min,
    }
    await save_playlist(user_id, videoid, plist)
    await CallbackQuery.answer(f"تـمـت الإضـافـة: {title} {emo}", show_alert=True)


@app.on_message(filters.command(["delallplaylist", "حذف القائمة كلها", "حذف الكل", "فرمتة القائمة"], prefixes=["/", "!", ".", ""]) & ~BANNED_USERS)
@language
async def delete_all_playlists(client, message, _):
    emo = choice(HEART_EMOJIS)
    user_id = message.from_user.id
    _playlist = await get_playlist_names(user_id)
    if _playlist:
        upl = warning_markup(_)
        await message.reply_text(f"**هـل أنـت مـتـأكـد أنـك تـريـد حـذف الـقـائـمـة بـالـكـامـل؟ {emo}**", reply_markup=upl)
    else:
        await message.reply_text("**الـقـائـمـة فـارغـة بـالـفـعـل.**")


@app.on_callback_query(filters.regex("del_playlist") & ~BANNED_USERS)
@languageCB
async def del_plist_cb(client, CallbackQuery, _):
    emo = choice(HEART_EMOJIS)
    callback_data = CallbackQuery.data.strip()
    videoid = callback_data.split(None, 1)[1]
    user_id = CallbackQuery.from_user.id
    
    deleted = await delete_playlist(user_id, videoid)
    if deleted:
        await CallbackQuery.answer(f"تـم الـحـذف {emo}", show_alert=True)
    else:
        await CallbackQuery.answer("حـدث خـطـأ.", show_alert=True)
        
    keyboard, count = await get_keyboard(_, user_id)
    await CallbackQuery.edit_message_reply_markup(reply_markup=keyboard)


@app.on_callback_query(filters.regex("delete_whole_playlist") & ~BANNED_USERS)
@languageCB
async def del_whole_playlist(client, CallbackQuery, _):
    emo = choice(HEART_EMOJIS)
    user_id = CallbackQuery.from_user.id
    # Optimizing mass delete using $unset on "notes" key, or set empty
    await playlistdb.update_one(
        {"chat_id": user_id},
        {"$set": {"notes": {}}},
        upsert=True
    )
    await CallbackQuery.edit_message_text(f"**تـم حـذف الـقـائـمـة بـالـكـامـل بـنـجـاح {emo}**")


@app.on_callback_query(filters.regex("get_playlist_playmode") & ~BANNED_USERS)
@languageCB
async def get_playlist_playmode_(client, CallbackQuery, _):
    try:
        await CallbackQuery.answer()
    except:
        pass
    buttons = get_playlist_markup(_)
    await CallbackQuery.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))


@app.on_callback_query(filters.regex("delete_warning") & ~BANNED_USERS)
@languageCB
async def delete_warning_message(client, CallbackQuery, _):
    emo = choice(HEART_EMOJIS)
    try:
        await CallbackQuery.answer()
    except:
        pass
    upl = warning_markup(_)
    await CallbackQuery.edit_message_text(f"**هـل أنـت مـتـأكـد مـن الـحـذف؟ لا يـمـكـن الـتـراجـع! {emo}**", reply_markup=upl)


@app.on_callback_query(filters.regex("home_play") & ~BANNED_USERS)
@languageCB
async def home_play_(client, CallbackQuery, _):
    try:
        await CallbackQuery.answer()
    except:
        pass
    buttons = botplaylist_markup(_)
    await CallbackQuery.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))


@app.on_callback_query(filters.regex("del_back_playlist") & ~BANNED_USERS)
@languageCB
async def del_back_playlist(client, CallbackQuery, _):
    user_id = CallbackQuery.from_user.id
    _playlist = await get_playlist_names(user_id)
    if not _playlist:
        return await CallbackQuery.answer("الـقـائـمـة فـارغـة", show_alert=True)
    
    await CallbackQuery.answer("الـرجـوع...", show_alert=True)
    keyboard, count = await get_keyboard(_, user_id)
    await CallbackQuery.edit_message_text(f"**لـديـك {count} أغـنـيـة فـي الـقـائـمـة:**", reply_markup=keyboard)
