from .collections import gbansdb, sudoersdb

# ===================== GBANS =====================

async def get_gbanned() -> list:
    results = []
    async for user in gbansdb.find({"user_id": {"$gt": 0}}):
        user_id = user.get("user_id")
        if user_id:
            results.append(user_id)
    return results


async def is_gbanned_user(user_id: int) -> bool:
    user = await gbansdb.find_one({"user_id": user_id})
    return bool(user)


async def add_gban_user(user_id: int):
    if await is_gbanned_user(user_id):
        return
    await gbansdb.insert_one({"user_id": user_id})


async def remove_gban_user(user_id: int):
    if not await is_gbanned_user(user_id):
        return
    await gbansdb.delete_one({"user_id": user_id})


# ===================== SUDO =====================

async def get_sudoers() -> list:
    data = await sudoersdb.find_one({"sudo": "sudo"})
    if not data:
        return []
    return data.get("sudoers", [])


async def add_sudo(user_id: int) -> bool:
    sudoers = await get_sudoers()
    if user_id in sudoers:
        return True
    sudoers.append(user_id)
    await sudoersdb.update_one(
        {"sudo": "sudo"},
        {"$set": {"sudoers": sudoers}},
        upsert=True,
    )
    return True


async def remove_sudo(user_id: int) -> bool:
    sudoers = await get_sudoers()
    if user_id not in sudoers:
        return True
    sudoers.remove(user_id)
    await sudoersdb.update_one(
        {"sudo": "sudo"},
        {"$set": {"sudoers": sudoers}},
        upsert=True,
    )
    return True
