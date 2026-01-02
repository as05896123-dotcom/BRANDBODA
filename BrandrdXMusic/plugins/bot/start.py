import time
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from youtubesearchpython.__future__ import VideosSearch

import config
from BrandrdXMusic import app
from BrandrdXMusic.misc import _boot_
from BrandrdXMusic.plugins.sudo.sudoers import sudoers_list
from BrandrdXMusic.utils.database import (
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
    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]
        if name[0:4] == "help":
            keyboard = help_pannel(_)
            await message.reply_sticker("CAACAgUAAxkBAAM3aVdeWEHOfLJDs5xQlbanyV-qnwYAAgsVAAL68RlUwGZYcJD6wm4eBA")
            return await message.reply_photo(
                photo=config.START_IMG_URL,
                caption=_["help_1"].format(config.SUPPORT_CHAT),
                reply_markup=keyboard,
            )
        if name[0:3] == "sud":
            await sudoers_list(client=client, message=message, _=_)
            try:
                if await is_on_off(2):
                    return await app.send_message(
                        chat_id=config.LOGGER_ID,
                        text=f"{message.from_user.mention} بـدأ البـوت للـتـحـقـق مـن **قـائـمـة الـمـطـوريـن**.\n\n**الـآيـدي :** <code>{message.from_user.id}</code>\n**الـمـعـرف :** @{message.from_user.username}",
                    )
            except:
                pass
            return
        if name[0:3] == "inf":
            m = await message.reply_text("🔎")
            query = (str(name)).replace("info_", "", 1)
            query = f"https://www.youtube.com/watch?v={query}"
            results = VideosSearch(query, limit=1)
            for result in (await results.next())["result"]:
                title = result["title"]
                duration = result["duration"]
                views = result["viewCount"]["short"]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                channellink = result["channel"]["link"]
                channel = result["channel"]["name"]
                link = result["link"]
                published = result["publishedTime"]
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
            try:
                if await is_on_off(2):
                    return await app.send_message(
                        chat_id=config.LOGGER_ID,
                        text=f"{message.from_user.mention} بـدأ البـوت للـتـحـقـق مـن **مـعـلـومـات الـمـقـطـع**.\n\n**الـآيـدي :** <code>{message.from_user.id}</code>\n**الـمـعـرف :** @{message.from_user.username}",
                    )
            except:
                pass
    else:

        try:
            out = private_panel(_)
            
            # --- بداية الانيميشن البطيء ---
            lol = await message.reply_text("اهـلاً بـك عـزيـزي ♡ {}.. 🥀".format(message.from_user.mention))
            await asyncio.sleep(0.4)
            await lol.edit_text("اهـلاً بـك عـزيـزي ♡ {}.. 💞".format(message.from_user.mention))
            await asyncio.sleep(0.4)
            await lol.edit_text("اهـلاً بـك عـزيـزي ♡ {}.. 🤍".format(message.from_user.mention))
            await asyncio.sleep(0.4)
            await lol.edit_text("اهـلاً بـك عـزيـزي ♡ {}.. ♥️".format(message.from_user.mention))
            await asyncio.sleep(0.4)
            await lol.edit_text("اهـلاً بـك عـزيـزي ♡ {}.. 🤎".format(message.from_user.mention))
            await asyncio.sleep(0.4)
            await lol.edit_text("اهـلاً بـك عـزيـزي ♡ {}.. 💕".format(message.from_user.mention))
            await asyncio.sleep(0.4)
               
            await lol.delete()
            
            lols = await message.reply_text("**💝 جـ**")
            await asyncio.sleep(0.5)
            await lols.edit_text("🥀 جـارِ")        
            await asyncio.sleep(0.5)
            await lols.edit_text("**💞 جـارِ الـ**")
            await asyncio.sleep(0.5)
            await lols.edit_text("**🤍 جـارِ الـتـشـ**")
            await asyncio.sleep(0.5)
            await lols.edit_text("**♥️ جـارِ الـتـشـغـيـ**")
            await asyncio.sleep(0.5)
            await lols.edit_text("**🤎 جـارِ الـتـشـغـيـل**")
            await asyncio.sleep(0.5)
            await lols.edit_text("**💕 جـارِ الـتـشـغـيـل...**")
            await asyncio.sleep(0.5)
            await lols.edit_text("**💝 تـم الـتـشـغـيـل**")
            await asyncio.sleep(0.5)

            await lols.edit_text("**🥀 تـم الـتـشـغـيـل**")
            await asyncio.sleep(0.5)
            await lols.edit_text("**💞 تـم الـتـشـغـيـل**")
            await asyncio.sleep(0.5)
            await lols.edit_text("**🤍 تـم الـتـشـغـيـل**")
            # --- نهاية الانيميشن ---

            m = await message.reply_sticker("CAACAgUAAxkBAAM3aVdeWEHOfLJDs5xQlbanyV-qnwYAAgsVAAL68RlUwGZYcJD6wm4eBA")
            
            # --- إصلاح مشكلة الصورة (الحل النهائي) ---
            # نجعل الافتراضي هو صورة البوت
            chat_photo = config.START_IMG_URL
            
            # نحاول تحميل صورة العضو، لو فشل يظل على صورة البوت
            if message.chat.photo:
                try:
                    userss_photo = await app.download_media(message.chat.photo.big_file_id)
                    if userss_photo:
                        chat_photo = userss_photo
                except:
                    # في حالة الفشل نستخدم صورة البوت
                    chat_photo = config.START_IMG_URL

        except Exception as e:
            # أي خطأ آخر، نستخدم صورة البوت
            chat_photo = config.START_IMG_URL
            print(f"Error in start animation: {e}")
        
        # تنظيف الرسائل القديمة
        try:
            await lols.delete()
            await m.delete()
        except:
            pass

        # إرسال رسالة الترحيب النهائية (مضمونة الآن)
        await message.reply_photo(
            photo=chat_photo,
            caption=_["start_2"].format(message.from_user.mention, app.mention),
            reply_markup=InlineKeyboardMarkup(out),
        )

        try:
            if config.LOGGER_ID:
                sender_id = message.from_user.id
                sender_name = message.from_user.first_name
                await app.send_message(
                    config.LOGGER_ID,
                    f"{message.from_user.mention} بـدأ الـبـوت. \n\n**الـآيـدي : {sender_id}\n**الـاسـم : {sender_name}",
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
            if await is_banned_user(member.id):
                try:
                    await message.chat.ban_member(member.id)
                except:
                    pass
            if member.id == app.id:
                if message.chat.type != ChatType.SUPERGROUP:
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
        except Exception as ex:
            print(ex)
