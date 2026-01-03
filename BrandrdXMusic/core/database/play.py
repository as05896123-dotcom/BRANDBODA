# BrandrdXMusic/core/database/play.py

from BrandrdXMusic.core.mongo import mongodb

# =======================
# Mongo Collections
# =======================

playmodedb = mongodb.playmode
playtypedb = mongodb.playtypedb
skipdb = mongodb.skipmode
loopdb = mongodb.loopmode
channeldb = mongodb.cplaymode

# =======================
# In-Memory Cache
# =======================

playmode = {}
playtype = {}
skipmode = {}
loop = {}
channelconnect = {}

# =======================
# Play Mode
# =======================

async def set_playmode(chat_id: int, mode: str):
    playmode[chat_id] = mode
    await playmodedb.update_one(
        {"chat_id": chat_id},
        {"$set": {"mode": mode}},
        upsert=True,
    )


async def get_playmode(chat_id: int):
    if chat_id in playmode:
        return playmode[chat_id]

    data = await playmodedb.find_one({"chat_id": chat_id})
    if not data:
        return "Direct"

    playmode[chat_id] = data["mode"]
    return data["mode"]

# =======================
# Play Type (Audio / Video)
# =======================

async def set_playtype(chat_id: int, ptype: str):
    playtype[chat_id] = ptype
    await playtypedb.update_one(
        {"chat_id": chat_id},
        {"$set": {"type": ptype}},
        upsert=True,
    )


async def get_playtype(chat_id: int):
    if chat_id in playtype:
        return playtype[chat_id]

    data = await playtypedb.find_one({"chat_id": chat_id})
    if not data:
        return "Audio"

    playtype[chat_id] = data["type"]
    return data["type"]

# =======================
# Skip Mode
# =======================

async def set_skipmode(chat_id: int, mode: str):
    skipmode[chat_id] = mode
    await skipdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"mode": mode}},
        upsert=True,
    )


async def get_skipmode(chat_id: int):
    if chat_id in skipmode:
        return skipmode[chat_id]

    data = await skipdb.find_one({"chat_id": chat_id})
    if not data:
        return "Everyone"

    skipmode[chat_id] = data["mode"]
    return data["mode"]

# =======================
# Loop Mode
# =======================

async def set_loop(chat_id: int, value: int):
    loop[chat_id] = value
    await loopdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"value": value}},
        upsert=True,
    )


async def get_loop(chat_id: int):
    if chat_id in loop:
        return loop[chat_id]

    data = await loopdb.find_one({"chat_id": chat_id})
    if not data:
        return 0

    loop[chat_id] = data["value"]
    return data["value"]

# =======================
# Channel Play Mode
# =======================

async def set_cmode(chat_id: int, channel_id: int):
    channelconnect[chat_id] = channel_id
    await channeldb.update_one(
        {"chat_id": chat_id},
        {"$set": {"channel_id": channel_id}},
        upsert=True,
    )


async def get_cmode(chat_id: int):
    if chat_id in channelconnect:
        return channelconnect[chat_id]

    data = await channeldb.find_one({"chat_id": chat_id})
    if not data:
        return None

    channelconnect[chat_id] = data["channel_id"]
    return data["channel_id"]
