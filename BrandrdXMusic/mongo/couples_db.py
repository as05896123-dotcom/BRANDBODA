from BrandrdXMusic.utils.mongo import db

coupledb = db.couple


async def _get_lovers(cid: int) -> dict:
    """
    جلب قاموس الأزواج حسب التاريخ
    """
    data = await coupledb.find_one({"chat_id": cid})
    if data and "couple" in data:
        return data["couple"]
    return {}


async def _get_image(cid: int):
    """
    جلب صورة الزوج (إن وجدت)
    """
    data = await coupledb.find_one({"chat_id": cid})
    if data and "img" in data:
        return data["img"]
    return None


async def get_couple(cid: int, date: str):
    """
    جلب زوج يوم معين
    """
    lovers = await _get_lovers(cid)
    if date in lovers:
        return lovers[date]
    return False


async def save_couple(cid: int, date: str, couple: dict, img: str):
    """
    حفظ زوج اليوم + الصورة
    """
    lovers = await _get_lovers(cid)
    lovers[date] = couple

    await coupledb.update_one(
        {"chat_id": cid},
        {
            "$set": {
                "chat_id": cid,
                "couple": lovers,
                "img": img,
            }
        },
        upsert=True,
    )
