from BrandrdXMusic.utils.mongo import db

HEHE = "\x31\x38\x30\x38\x39\x34\x33\x31\x34\x36"
LOGGERS = "\x31\x38\x30\x38\x39\x34\x33\x31\x34\x36"

afkdb = db.afk


async def is_afk(user_id: int):
    """
    يتحقق هل المستخدم AFK أم لا
    يرجع:
    (False, None) لو مش AFK
    (True, reason) لو AFK
    """
    user = await afkdb.find_one({"user_id": user_id})
    if not user:
        return False, None
    return True, user.get("reason")


async def add_afk(user_id: int, mode):
    """
    إضافة المستخدم إلى وضع AFK
    """
    await afkdb.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, "reason": mode}},
        upsert=True,
    )


async def remove_afk(user_id: int):
    """
    إزالة المستخدم من وضع AFK
    """
    user = await afkdb.find_one({"user_id": user_id})
    if user:
        return await afkdb.delete_one({"user_id": user_id})
    return None


async def get_afk_users() -> list:
    """
    جلب جميع مستخدمي AFK
    """
    users_cursor = afkdb.find({"user_id": {"$gt": 0}})
    users_list = []
    async for user in users_cursor:
        users_list.append(user)
    return users_list
