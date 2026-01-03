# BrandrdXMusic/core/database/queries.py

from BrandrdXMusic.misc import db

async def set_queries(count: int):
    """
    حفظ عدد الاستعلامات (Placeholder للتوافق مع السورس القديم)
    """
    try:
        db["queries"] = count
    except Exception:
        pass
