import random

from BrandrdXMusic import userbot
from .collections import assdb, assistantdict


# ======================
# Helpers
# ======================

async def get_client(assistant: int):
    assistant = int(assistant)
    if assistant == 1:
        return userbot.one
    elif assistant == 2:
        return userbot.two
    elif assistant == 3:
        return userbot.three
    elif assistant == 4:
        return userbot.four
    elif assistant == 5:
        return userbot.five
    return None


# ======================
# Assistant Selectors
# ======================

async def set_assistant_new(chat_id: int, number: int):
    number = int(number)
    assistantdict[chat_id] = number
    await assdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"assistant": number}},
        upsert=True,
    )


async def set_assistant(chat_id: int):
    from BrandrdXMusic.core.userbot import assistants

    if not assistants:
        raise RuntimeError("No assistants available")

    ran_assistant = random.choice(assistants)
    assistantdict[chat_id] = ran_assistant

    await assdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"assistant": ran_assistant}},
        upsert=True,
    )

    return await get_client(ran_assistant)


async def get_assistant(chat_id: int):
    from BrandrdXMusic.core.userbot import assistants

    if not assistants:
        raise RuntimeError("No assistants available")

    assistant = assistantdict.get(chat_id)

    if not assistant:
        dbassistant = await assdb.find_one({"chat_id": chat_id})
        if not dbassistant:
            return await set_assistant(chat_id)

        assistant = dbassistant.get("assistant")

    if assistant in assistants:
        assistantdict[chat_id] = assistant
        client = await get_client(assistant)
        if client:
            return client

    return await set_assistant(chat_id)


# ======================
# Calls (PyTgCalls)
# ======================

async def set_calls_assistant(chat_id: int):
    from BrandrdXMusic.core.userbot import assistants

    if not assistants:
        raise RuntimeError("No assistants available")

    ran_assistant = random.choice(assistants)
    assistantdict[chat_id] = ran_assistant

    await assdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"assistant": ran_assistant}},
        upsert=True,
    )

    return ran_assistant


async def group_assistant(self, chat_id: int):
    from BrandrdXMusic.core.userbot import assistants

    if not assistants:
        raise RuntimeError("No assistants available")

    assistant = assistantdict.get(chat_id)

    if not assistant:
        dbassistant = await assdb.find_one({"chat_id": chat_id})
        if not dbassistant:
            assistant = await set_calls_assistant(chat_id)
        else:
            assistant = dbassistant.get("assistant")

    if assistant not in assistants:
        assistant = await set_calls_assistant(chat_id)

    assistantdict[chat_id] = assistant

    if assistant == 1:
        return self.one
    elif assistant == 2:
        return self.two
    elif assistant == 3:
        return self.three
    elif assistant == 4:
        return self.four
    elif assistant == 5:
        return self.five

    raise RuntimeError("Invalid assistant selected")
