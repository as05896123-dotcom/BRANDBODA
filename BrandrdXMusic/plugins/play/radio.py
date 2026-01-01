import logging
import asyncio 

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import (
    ChatAdminRequired,
    InviteRequestSent,
    UserAlreadyParticipant,
    UserNotParticipant,
)
from pyrogram.types import Message

from config import BANNED_USERS, adminlist
from strings import get_string
from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS
from BrandrdXMusic.utils.database import (
    get_assistant,
    get_cmode,
    get_lang,
    get_playmode,
    get_playtype,
)
from BrandrdXMusic.utils.logger import play_logs
from BrandrdXMusic.utils.stream.stream import stream

# تم تحديث الأسماء (القرآن الكريم) والروابط
RADIO_STATION = {
    "القرآن الكريم": "https://stream.radiojar.com/8s5u5tpdtwzuv",
    "نجوم اف ام": "https://ssl.mz-audiostreaming.com/nogoumfm",
    "نايل اف ام": "https://ssl.mz-audiostreaming.com/nilefm",
    "نغم اف ام": "https://ssl.mz-audiostreaming.com/naghamfm",
    "ميجا اف ام": "https://ssl.mz-audiostreaming.com/megafm",
    "الراديو 9090": "https://9090streaming.mobtada.com/9090FMEGYPT",
    "راديو مصر": "https://live.radiomasr.net/RADIOMASR",
    "محطة مصر": "https://s3.radio.co/s95f66299d/listen",
    "شعبى اف ام": "https://radio.masr.me/sha3byfm",
    "اون سبورت اف ام": "https://stream.radiojar.com/4884313205tv",
}

valid_stations = "\n".join([f"`{name}`" for name in sorted(RADIO_STATION.keys())])


@app.on_message(
    filters.command(["radioplayforce", "radio", "cradio", "راديو"])
    & filters.group
    & ~BANNED_USERS
)
async def radio(client, message: Message):
    msg = await message.reply_text("جـارِ الاتـصـال بـالـبـث الـمـبـاشـر...")
    try:
        try:
            userbot = await get_assistant(message.chat.id)
            get = await app.get_chat_member(message.chat.id, userbot.id)
        except ChatAdminRequired:
            return await msg.edit_text(
                f"» لا أمـلـك صـلاحـيـة دعـوة الـمـسـتـخـدمـيـن لـإضـافـة {userbot.mention} الـمـسـاعـد إلـى {message.chat.title}."
            )
        if get.status == ChatMemberStatus.BANNED:
            return await msg.edit_text(
                text=f"» {userbot.mention} الـمـسـاعـد مـحـظـور فـي {message.chat.title}\n\n𖢵 الآيـدي : `{userbot.id}`\n𖢵 الاسـم : {userbot.mention}\n𖢵 الـيـوزر : @{userbot.username}\n\nيـرجـى رفـع الـحـظـر عـن الـمـسـاعـد والـمـحـاولـة مـرة أخـرى...",
            )
    except UserNotParticipant:
        if message.chat.username:
            invitelink = message.chat.username
            try:
                await userbot.resolve_peer(invitelink)
            except Exception as ex:
                logging.exception(ex)
        else:
            try:
                invitelink = await client.export_chat_invite_link(message.chat.id)
            except ChatAdminRequired:
                return await msg.edit_text(
                    f"» لا أمـلـك صـلاحـيـة دعـوة الـمـسـتـخـدمـيـن لـإضـافـة {userbot.mention} الـمـسـاعـد إلـى {message.chat.title}."
                )
            except InviteRequestSent:
                try:
                    await app.approve_chat_join_request(message.chat.id, userbot.id)
                except Exception as e:
                    return await msg.edit(
                        f"فـشـلـت فـي دعـوة {userbot.mention} الـمـسـاعـد إلـى {message.chat.title}.\n\n**الـسـبـب :** `{ex}`"
                    )
            except Exception as ex:
                if "channels.JoinChannel" in str(ex) or "Username not found" in str(ex):
                    return await msg.edit_text(
                        f"» لا أمـلـك صـلاحـيـة دعـوة الـمـسـتـخـدمـيـن لـإضـافـة {userbot.mention} الـمـسـاعـد إلـى {message.chat.title}."
                    )
                else:
                    return await msg.edit_text(
                        f"فـشـلـت فـي دعـوة {userbot.mention} الـمـسـاعـد إلـى {message.chat.title}.\n\n**الـسـبـب :** `{ex}`"
                    )
        if invitelink.startswith("https://t.me/+"):
            invitelink = invitelink.replace("https://t.me/+", "https://t.me/joinchat/")
        anon = await msg.edit_text(
            f"يـرجـى الانـتـظـار...\n\nجـارِ دعـوة {userbot.mention} إلـى {message.chat.title}."
        )
        try:
            await userbot.join_chat(invitelink)
            await asyncio.sleep(2)
            await msg.edit_text(
                f"تـم انـضـمـام {userbot.mention} بـنـجـاح،\n\nبـدء الـبـث..."
            )
        except UserAlreadyParticipant:
            pass
        except InviteRequestSent:
            try:
                await app.approve_chat_join_request(message.chat.id, userbot.id)
            except Exception as e:
                return await msg.edit(
                    f"فـشـلـت فـي دعـوة {userbot.mention} الـمـسـاعـد إلـى {message.chat.title}.\n\n**الـسـبـب :** `{ex}`"
                )
        except Exception as ex:
            if "channels.JoinChannel" in str(ex) or "Username not found" in str(ex):
                return await msg.edit_text(
                    f"» لا أمـلـك صـلاحـيـة دعـوة الـمـسـتـخـدمـيـن لـإضـافـة {userbot.mention} الـمـسـاعـد إلـى {message.chat.title}."
                )
            else:
                return await msg.edit_text(
                    f"فـشـلـت فـي دعـوة {userbot.mention} الـمـسـاعـد إلـى {message.chat.title}.\n\n**الـسـبـب :** `{ex}`"
                )

        try:
            await userbot.resolve_peer(invitelink)
        except:
            pass
    await msg.delete()
    
    if len(message.command) < 2:
        return await message.reply(
            f"**الـرجـاء اخـتـيـار إذاعـة لـتـشـغـيـلـهـا:**\n\n{valid_stations}\n\n**مـثـال:**\n`راديو القرآن الكريم`"
        )
        
    station_name = " ".join(message.command[1:])
    
    # البحث عن المحطة (تطبيع الحروف للبحث المرن)
    target_station = None
    for station in RADIO_STATION:
        # توحيد: أ، إ، آ -> ا | ة -> ه | ى -> ي
        clean_input = station_name.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه").replace("ى", "ي")
        clean_station = station.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه").replace("ى", "ي")
        
        if clean_station == clean_input:
            target_station = station
            break
            
    if target_station:
        RADIO_URL = RADIO_STATION[target_station]
        language = await get_lang(message.chat.id)
        _ = get_string(language)
        playmode = await get_playmode(message.chat.id)
        playty = await get_playtype(message.chat.id)
        if playty != "Everyone":
            if message.from_user.id not in SUDOERS:
                admins = adminlist.get(message.chat.id)
                if not admins:
                    return await message.reply_text(_["admin_18"])
                else:
                    if message.from_user.id not in admins:
                        return await message.reply_text(_["play_4"])
        if message.command[0][0] == "c":
            chat_id = await get_cmode(message.chat.id)
            if chat_id is None:
                return await message.reply_text(_["setting_12"])
            try:
                chat = await app.get_chat(chat_id)
            except:
                return await message.reply_text(_["cplay_4"])
            channel = chat.title
        else:
            chat_id = message.chat.id
            channel = None

        video = None
        mystic = await message.reply_text(
            _["play_2"].format(channel) if channel else _["play_1"]
        )
        try:
            await stream(
                _,
                mystic,
                message.from_user.id,
                RADIO_URL,
                chat_id,
                message.from_user.mention,
                message.chat.id,
                video=video,
                streamtype="index",
            )
        except Exception as e:
            ex_type = type(e).__name__
            err = e if ex_type == "AssistantErr" else _["general_3"].format(ex_type)
            return await mystic.edit_text(err)
        return await play_logs(message, streamtype=f"Radio: {target_station}")
    else:
        await message.reply(
            f"**لـم يـتـم الـعـثـور عـلـى الـمـحـطـة.**\nاخـتـر مـن الـقـائـمـة أدناه:\n\n{valid_stations}"
        )


__MODULE__ = "الراديو"
__HELP__ = f"\nراديو [المحطة] - لـتـشـغـيـل **الـراديـو الـمـصـري**\n\n**الـمـحـطـات الـمـتـاحـة:**\n{valid_stations}"
