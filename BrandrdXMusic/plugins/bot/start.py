import time
import asyncio
import os
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from youtubesearchpython.__future__ import VideosSearch

import config
from BrandrdXMusic import app
from BrandrdXMusic.misc import _boot_
from BrandrdXMusic.plugins.sudo.sudoers import sudoers_list

# -----------------------------------------------------------
# [CORE MIGRATION] Import from Core Database Package
# -----------------------------------------------------------
from BrandrdXMusic.core.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
)

from BrandrdXMusic.utils.decorators.language import LanguageStart
from BrandrdXMusic.utils.formatters import get_readable_time
from BrandrdXMusic.utils.inline import help_pannel, private_panel, start_panel
from config import BANNED_USERS
from strings import get_string


@app.on_message(filters.command(["start"], prefixes=["/", "!", ".", ""]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    await add_served_user(message.from_user.id)
    await message.react("❤️")
    
    # --- معالجة الأوامر الفرعية (Deep Linking) ---
    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]
        
        # Help Command
        if name[0:4] == "help":
            keyboard = help_pannel(_)
            # يفضل عدم استخدام Sticker ID ثابت إذا تغير البوت، لكن سأتركه كما هو
            await message.reply_sticker("CAACAgUAAxkBAAM3aVdeWEHOfLJDs5xQlbanyV-qnwYAAgsVAAL68RlUwGZYcJD6wm4eBA")
            return await message.reply_photo(
                photo=config.START_IMG_URL,
                caption=_["help_1"].format(config.SUPPORT_CHAT),
                reply_markup=keyboard,
            )
        
        # Sudo List
        if name[0:3] == "sud":
            await sudoers_list(client=client, message=message, _=_)
            try:
                if await is_on_off(2):
                    await app.send_message(
                        chat_id=config.LOGGER_ID,
                        text=f"{message.from_user.mention} بـدأ البـوت للـتـحـقـق مـن **قـائـمـة الـمـطـوريـن**.\n\n**الـآيـدي :** <code>{message.from_user.id}</code>\n**الـمـعـرف :** @{message.from_user.username}",
                    )
            except:
                pass
            return
            
        # Info Command
        if name[0:3] == "inf":
            m = await message.reply_text("🔎")
            query = (str(name)).replace("info_", "", 1)
            query = f"https://www.youtube.com/watch?v={query}"
            
            try:
                results = VideosSearch(query, limit=1)
                result = (await results.next())["result"][0]
                
                title = result["title"]
                duration = result["duration"]
                views = result.get("viewCount", {}).get("short", "N/A")
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                channellink = result.get("channel", {}).get("link", "N/A")
                channel = result.get("channel", {}).get("name", "Unknown")
                link = result["link"]
                published = result.get("publishedTime", "Unknown")
                
                searched_text = _["start_6"].format(
                    title, duration, views, published, channellink, channel, app.mention
                )
                key = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text=_["S_B_8"], url=link),
                            InlineKeyboardButton(text=_["S_B_9"], url=config.SUPPORT_CHAT),
                        ],
                    ]
                )
                await m.delete()
                await app.send_photo(
                    chat_id=message.chat.id,
                    photo=thumbnail,
                    caption=searched_text,
                    reply_markup=key,
                )
                
                if await is_on_off(2):
                    await app.send_message(
                        chat_id=config.LOGGER_ID,
                        text=f"{message.from_user.mention} بـدأ البـوت للـتـحـقـق مـن **مـعـلـومـات الـمـقـطـع**.\n\n**الـآيـدي :** <code>{message.from_user.id}</code>\n**الـمـعـرف :** @{message.from_user.username}",
                    )
            except Exception as e:
                await m.edit_text("لم يتم العثور على معلومات.")
            return

    # --- القائمة الرئيسية (Start العادية) ---
    else:
        lols = None
        try:
            out = private_panel(_)
            
            # --- الانيميشن (Animation) ---
            lol = await message.reply_text("اهـلاً بـك عـزيـزي ♡ {}.. 🥀".format(message.from_user.mention))
            animations = ["💞", "🤍", "♥️", "🤎", "💕"]
            for emoji in animations:
                await asyncio.sleep(0.3) # تقليل الوقت قليلاً لتسريع الاستجابة
                try:
                    await lol.edit_text(f"اهـلاً بـك عـزيـزي ♡ {message.from_user.mention}.. {emoji}")
                except:
                    pass
            
            await lol.delete()
            
            # Loading Animation
            lols = await message.reply_text("**💝 جـ**")
            loading_texts = [
                "🥀 جـارِ", "**💞 جـارِ الـ**", "**🤍 جـارِ الـتـشـ**",
                "**♥️ جـارِ الـتـشـغـيـ**", "**🤎 جـارِ الـتـشـغـيـل**",
                "**💕 جـارِ الـتـشـغـيـل...**", "**💝 تـم الـتـشـغـيـل**",
                "**🥀 تـم الـتـشـغـيـل**", "**💞 تـم الـتـشـغـيـل**",
                "**🤍 تـم الـتـشـغـيـل**"
            ]
            
            for text in loading_texts:
                await asyncio.sleep(0.3)
                try:
                    await lols.edit_text(text)
                except:
                    pass

            # Sticker
            m = await message.reply_sticker("CAACAgUAAxkBAAM3aVdeWEHOfLJDs5xQlbanyV-qnwYAAgsVAAL68RlUwGZYcJD6wm4eBA")
            
            # --- التعامل مع صورة البروفايل (Safe Implementation) ---
            chat_photo = config.START_IMG_URL
            temp_photo_path = None
            
            if message.chat.photo:
                try:
                    # تحميل الصورة إلى ملف مؤقت
                    temp_photo_path = await app.download_media(message.chat.photo.big_file_id)
                    chat_photo = temp_photo_path
                except:
                    chat_photo = config.START_IMG_URL

            # إرسال الرسالة النهائية
            await message.reply_photo(
                photo=chat_photo,
                caption=_["start_2"].format(message.from_user.mention, app.mention),
                reply_markup=InlineKeyboardMarkup(out),
            )
            
            # [CRITICAL] تنظيف الملف المؤقت لمنع امتلاء السيرفر
            if temp_photo_path and os.path.exists(temp_photo_path):
                try:
                    os.remove(temp_photo_path)
                except:
                    pass

        except Exception as e:
            # Fallback في حالة حدوث خطأ كارثي
            await message.reply_photo(
                photo=config.START_IMG_URL,
                caption=_["start_2"].format(message.from_user.mention, app.mention),
                reply_markup=InlineKeyboardMarkup(out),
            )
        
        # تنظيف رسائل الانيميشن
        try:
            if lols: await lols.delete()
            if m: await m.delete()
        except:
            pass

        # Logger
        try:
            if config.LOGGER_ID:
                await app.send_message(
                    config.LOGGER_ID,
                    f"{message.from_user.mention} بـدأ الـبـوت. \n\n**الـآيـدي : {message.from_user.id}\n**الـاسـم : {message.from_user.first_name}",
                )
        except:
            pass


@app.on_message(filters.command(["start"], prefixes=["/", "!", ".", ""]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    out = start_panel(_)
    uptime = int(time.time() - _boot_)
    await message.reply_photo(
        photo=config.START_IMG_URL,
        caption=_["start_1"].format(app.mention, get_readable_time(uptime)),
        reply_markup=InlineKeyboardMarkup(out),
    )
    return await add_served_chat(message.chat.id)


@app.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    for member in message.new_chat_members:
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)
            
            # Check Ban
            if await is_banned_user(member.id):
                try:
                    await message.chat.ban_member(member.id)
                except:
                    pass
            
            # Welcome Logic for Bot
            if member.id == app.id:
                if message.chat.type != enums.ChatType.SUPERGROUP:
                    await message.reply_text(_["start_4"])
                    return await app.leave_chat(message.chat.id)
                
                if message.chat.id in await blacklisted_chats():
                    await message.reply_text(
                        _["start_5"].format(
                            app.mention,
                            f"https://t.me/{app.username}?start=sudolist",
                            config.SUPPORT_CHAT,
                        ),
                        disable_web_page_preview=True,
                    )
                    return await app.leave_chat(message.chat.id)

                out = start_panel(_)
                await message.reply_photo(
                    photo=config.START_IMG_URL,
                    caption=_["start_3"].format(
                        message.from_user.first_name,
                        app.mention,
                        message.chat.title,
                        app.mention,
                    ),
                    reply_markup=InlineKeyboardMarkup(out),
                )
                await add_served_chat(message.chat.id)
                await message.stop_propagation()
        except Exception:
            # Silent fail is better for welcome handlers to avoid log spam
            pass
