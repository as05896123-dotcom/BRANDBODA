# core/database/queries.py

from BrandrdXMusic.core.database.connections import (
    queriesdb,
    DB_LOCK,
)

# ==========================
# Queries Counter (Global)
# ==========================

_QUERIES_CHAT_ID = 98324


async def get_queries() -> int:
    """
    Get total queries count.
    """
    try:
        data = await queriesdb.find_one({"chat_id": _QUERIES_CHAT_ID})
        return data.get("mode", 0) if data else 0
    except Exception:
        return 0


async def set_queries(value: int):
    """
    Increase queries count by value.
    """
    async with DB_LOCK:
        try:
            data = await queriesdb.find_one({"chat_id": _QUERIES_CHAT_ID})
            current = data.get("mode", 0) if data else 0
            await queriesdb.update_one(
                {"chat_id": _QUERIES_CHAT_ID},
                {"$set": {"mode": current + value}},
                upsert=True,
            )
        except Exception:
            pass
