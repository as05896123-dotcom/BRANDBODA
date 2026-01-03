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

from config import BANNED_USERS
from strings import get_string
from BrandrdXMusic import app
from BrandrdXMusic.misc import SUDOERS
from BrandrdXMusic.core.database import (
    get_assistant,
    get_cmode,
    get_lang,
)
from BrandrdXMusic.utils.logger import play_logs
from BrandrdXMusic.utils.stream.stream import stream

# ==========================
# محطات الـراديـو
# ==========================

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
    filters.command(
        ["radioplayforce", "radio", "cradio", "راديو"],
        prefixes=["/", "!", ".", ""],
    )
    & filters.group
    & ~BANNED_USERS
)
async def radio(client, message: Message):

    # ==========================
    # التحقق من الصلاحيات
    # ==========================

    user_id = None
    user_name = None
    is_admin = False

    if message.sender_chat and message.sender_chat.id == message.chat.id:
        user_id = message.chat.id
        user_name = message.chat.title
        is_admin = True

    elif message.from_user:
        user_id = message.from_user.id
        user_name = message.from_user.first_name

        if user_id in SUDOERS:
            is_admin = True
        else:
            try:
                member = await app.get_chat_member(message.chat.id, user_id)
                if member.status in (
                    ChatMemberStatus.ADMINISTRATOR,
                    ChatMemberStatus.OWNER,
                ):
                    is_admin = True
            except Exception:
                pass
    else:
        return

    if not is_admin:
        return await message.reply_text(
            "هـذا الأمـر مـخـصـص لـلـمـشـرفـيـن والـمـالـك فـقـط."
        )

    # ==========================
    # التأكد من وجود الـمـسـاعـد
    # ==========================

    msg = await message.reply_text("جـارِ تـجـهـيـز الـبـث...")

    try:
        userbot = await get_assistant(message.chat.id)
        member = await app.get_chat_member(message.chat.id, userbot.id)

        if member.status == ChatMemberStatus.BANNED:
            return await msg.edit_text(
                f"الـمـسـاعـد {userbot.mention} مـحـظـور فـي هـذا الـجـروب.\n"
                "يـرجـى رفـع الـحـظـر ثـم إعـادة الـمـحـاولـة."
            )

    except UserNotParticipant:
        try:
            if message.chat.username:
                invitelink = message.chat.username
            else:
                invitelink = await client.export_chat_invite_link(message.chat.id)

            await userbot.join_chat(invitelink)
            await asyncio.sleep(2)

        except InviteRequestSent:
            try:
                await app.approve_chat_join_request(message.chat.id, userbot.id)
            except Exception as ex:
                return await msg.edit_text(f"فـشـل انـضـمـام الـمـسـاعـد.\nالـسـبـب: `{ex}`")

        except Exception as ex:
            return await msg.edit_text(f"فـشـل انـضـمـام الـمـسـاعـد.\nالـسـبـب: `{ex}`")

    await msg.delete()

    # ==========================
    # تشغيل الـراديـو
    # ==========================

    if len(message.command) < 2:
        return await message.reply_text(
            f"اخـتـر مـحـطـة لـتـشـغـيـلـهـا:\n\n{valid_stations}\n\n"
            "مـثـال:\n`راديو القرآن الكريم`"
        )

    station_name = " ".join(message.command[1:])
    target_station = None

    for station in RADIO_STATION:
        def clean(txt):
            return (
                txt.replace("أ", "ا")
                .replace("إ", "ا")
                .replace("آ", "ا")
                .replace("ة", "ه")
                .replace("ى", "ي")
            )

        if clean(station) == clean(station_name):
            target_station = station
            break

    if not target_station:
        return await message.reply_text(
            f"لـم يـتـم الـعـثـور عـلـى الـمـحـطـة.\n\n{valid_stations}"
        )

    RADIO_URL = RADIO_STATION[target_station]
    language = await get_lang(message.chat.id)
    _ = get_string(language)

    if message.command[0].startswith("c"):
        chat_id = await get_cmode(message.chat.id)
        if chat_id is None:
            return await message.reply_text(_["setting_12"])
        chat = await app.get_chat(chat_id)
        channel = chat.title
    else:
        chat_id = message.chat.id
        channel = None

    mystic = await message.reply_text(
        _["play_2"].format(channel) if channel else _["play_1"]
    )

    try:
        await stream(
            _,
            mystic,
            user_id,
            RADIO_URL,
            chat_id,
            user_name,
            message.chat.id,
            video=None,
            streamtype="index",
        )
    except Exception as e:
        ex_type = type(e).__name__
        err = e if ex_type == "AssistantErr" else _["general_3"].format(ex_type)
        return await mystic.edit_text(err)

    return await play_logs(message, streamtype=f"Radio: {target_station}")


__MODULE__ = "الـراديـو"
__HELP__ = (
    "راديـو [اسـم الـمـحـطـة]\n\n"
    "لـتـشـغـيـل مـحـطـات الـراديـو الـمـتـاحـة:\n\n"
    f"{valid_stations}"
)
