from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from BrandrdXMusic import LOGGER
import config
import sys


# التحقق من وجود رابط قاعدة البيانات
if not config.MONGO_DB_URI:
    LOGGER(__name__).error(
        "❌ لم يتم العثور على رابط قاعدة البيانات MONGO_DB_URI في المتغيرات!"
    )
    sys.exit(1)

try:
    # ==========================
    # قاعدة البيانات (Async - Motor)
    # ==========================
    _mongo_async_ = AsyncIOMotorClient(
        config.MONGO_DB_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
    )
    mongodb = _mongo_async_.BrandrdXMusic

    # اختبار الاتصال async (غير مباشر)
    LOGGER(__name__).info("🔄 جاري التحقق من اتصال قاعدة البيانات async...")

    # ==========================
    # قاعدة البيانات (Sync - PyMongo)
    # ==========================
    _mongo_sync_ = MongoClient(
        config.MONGO_DB_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
    )
    pymongodb = _mongo_sync_.BrandrdXMusic

    # اختبار الاتصال sync
    _mongo_sync_.admin.command("ping")

    LOGGER(__name__).info("✅ تم الاتصال بقاعدة البيانات MongoDB بنجاح (Async + Sync)")

except Exception as e:
    LOGGER(__name__).error(
        f"❌ فشل الاتصال بقاعدة البيانات MongoDB!\nالسبب: {e}"
    )
    sys.exit(1)
