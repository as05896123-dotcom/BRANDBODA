# BrandrdXMusic/core/database/__init__.py

from typing import Dict, List, Union
import random

from BrandrdXMusic import userbot
from BrandrdXMusic.core.mongo import mongodb, pymongodb

# =======================
# Mongo Collections
# =======================

authdb = mongodb.adminauth
authuserdb = mongodb.authuser
autoenddb = mongodb.autoend
assdb = mongodb.assistants
blacklist_chatdb = mongodb.blacklistChat
blockeddb = mongodb.blockedusers
chatsdb = mongodb.chats
channeldb = mongodb.cplaymode
countdb = mongodb.upcount
gbansdb = mongodb.gban
langdb = mongodb.language
onoffdb = mongodb.onoffper
playmodedb = mongodb.playmode
playtypedb = mongodb.playtypedb
skipdb = mongodb.skipmode
sudoersdb = mongodb.sudoers
usersdb = mongodb.tgusersdb
privatedb = mongodb.privatechats
suggdb = mongodb.suggestion
cleandb = mongodb.cleanmode
queriesdb = mongodb.queries
userdb = mongodb.userstats
videodb = mongodb.vipvideocalls
chatsdbc = mongodb.chatsc
usersdbc = mongodb.tgusersdbc

# =======================
# In-Memory Cache
# =======================

active = []
activevideo = []
assistantdict = {}
autoend = {}
count = {}
channelconnect = {}
langm = {}
loop = {}
maintenance = []
nonadmin = {}
pause = {}
playmode = {}
playtype = {}
skipmode = {}
privatechats = {}
cleanmode = []
suggestion = {}
mute = {}

# =======================
# Assistant Handling
# =======================

async def get_client(assistant: int):
    if assistant == 1:
        return userbot.one
    if assistant == 2:
        return userbot.two
    if assistant == 3:
        return userbot.three
    if assistant == 4:
        return userbot.four
    if assistant == 5:
        return userbot.five


async def set_assistant(chat_id: int):
    from BrandrdXMusic.core.userbot import assistants

    ran = random.choice(assistants)
    assistantdict[chat_id] = ran
    await assdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"assistant": ran}},
        upsert=True,
    )
    return await get_client(ran)


async def get_assistant(chat_id: int):
    from BrandrdXMusic.core.userbot import assistants

    assistant = assistantdict.get(chat_id)
    if assistant and assistant in assistants:
        return await get_client(assistant)

    data = await assdb.find_one({"chat_id": chat_id})
    if data and data["assistant"] in assistants:
        assistantdict[chat_id] = data["assistant"]
        return await get_client(data["assistant"])

    return await set_assistant(chat_id)

# =======================
# Auth Users (مهم جدًا)
# =======================

async def _get_authusers(chat_id: int) -> Dict[str, dict]:
    data = await authuserdb.find_one({"chat_id": chat_id})
    if not data:
        return {}
    return data.get("notes", {})


async def get_authuser_names(chat_id: int) -> List[str]:
    notes = await _get_authusers(chat_id)
    return list(notes.keys())


async def get_authuser(chat_id: int, name: str) -> Union[bool, dict]:
    notes = await _get_authusers(chat_id)
    return notes.get(name, False)


async def save_authuser(chat_id: int, name: str, note: dict):
    notes = await _get_authusers(chat_id)
    notes[name] = note
    await authuserdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"notes": notes}},
        upsert=True,
    )


async def delete_authuser(chat_id: int, name: str) -> bool:
    notes = await _get_authusers(chat_id)
    if name not in notes:
        return False

    del notes[name]
    await authuserdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"notes": notes}},
        upsert=True,
    )
    return True
from .play import *
