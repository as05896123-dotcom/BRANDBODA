from BrandrdXMusic.misc import db

async def set_queries(count: int):
    db["queries"] = count
