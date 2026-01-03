# core/database/assistants.py

import random
from pyrogram import Client

from BrandrdXMusic import userbot
from BrandrdXMusic.core.userbot import assistants
from BrandrdXMusic.core.database.connections import (
    assdb,
    _assistant_cache,
    ASSISTANT_LOCK,
)

# ==========================
# Assistant Client Resolver
# ==========================

async def get_client(assistant_id: int) -> Client:
    aid = int(assistant_id)
    if aid == 1:
        return userbot.one
    elif aid == 2:
        return userbot.two
    elif aid == 3:
        return userbot.three
    elif aid == 4:
        return userbot.four
    elif aid == 5:
        return userbot.five
    return userbot.one


# ==========================
# Assistant Cache Logic
# ==========================

async def get_assistant_number(chat_id: int) -> int | None:
    async with ASSISTANT_LOCK:
        return _assistant_cache.get(chat_id)


async def set_assistant_new(chat_id: int, number: int):
    number = int(number)
    async with ASSISTANT_LOCK:
        _assistant_cache[chat_id] = number

    await assdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"assistant": number}},
        upsert=True,
    )


async def set_assistant(chat_id: int) -> Client:
    ran_assistant = random.choice(assistants)

    async with ASSISTANT_LOCK:
        _assistant_cache[chat_id] = ran_assistant

    await assdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"assistant": ran_assistant}},
        upsert=True,
    )

    return await get_client(ran_assistant)


async def get_assistant(chat_id: int) -> Client:
    async with ASSISTANT_LOCK:
        assistant_id = _assistant_cache.get(chat_id)

    if not assistant_id:
        dbassistant = await assdb.find_one({"chat_id": chat_id})
        if not dbassistant:
            return await set_assistant(chat_id)

        got = dbassistant.get("assistant")
        if got in assistants:
            async with ASSISTANT_LOCK:
                _assistant_cache[chat_id] = got
            return await get_client(got)

        return await set_assistant(chat_id)

    if assistant_id in assistants:
        return await get_client(assistant_id)

    return await set_assistant(chat_id)


# ==========================
# Calls Assistant (PyTgCalls)
# ==========================

async def set_calls_assistant(chat_id: int) -> int:
    ran_assistant = random.choice(assistants)

    async with ASSISTANT_LOCK:
        _assistant_cache[chat_id] = ran_assistant

    await assdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"assistant": ran_assistant}},
        upsert=True,
    )

    return ran_assistant


async def group_assistant(self, chat_id: int):
    async with ASSISTANT_LOCK:
        assistant_id = _assistant_cache.get(chat_id)

    if not assistant_id:
        dbassistant = await assdb.find_one({"chat_id": chat_id})
        if not dbassistant:
            assistant_id = await set_calls_assistant(chat_id)
        else:
            assis = dbassistant.get("assistant")
            if assis in assistants:
                async with ASSISTANT_LOCK:
                    _assistant_cache[chat_id] = assis
                assistant_id = assis
            else:
                assistant_id = await set_calls_assistant(chat_id)

    if assistant_id not in assistants:
        assistant_id = await set_calls_assistant(chat_id)

    aid = int(assistant_id)
    if aid == 1:
        return self.one
    elif aid == 2:
        return self.two
    elif aid == 3:
        return self.three
    elif aid == 4:
        return self.four
    elif aid == 5:
        return self.five

    return self.one
