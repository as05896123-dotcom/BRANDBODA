from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from BrandrdXMusic import LOGGER
import config

if config.MONGO_DB_URI is None:
    LOGGER(__name__).error("لم يتم العثور على رابط قاعدة البيانات MONGO_DB_URI في المتغيرات!")
    exit()

try:
    _mongo_async_ = AsyncIOMotorClient(config.MONGO_DB_URI)
    mongodb = _mongo_async_.BrandrdXMusic

    _mongo_sync_ = MongoClient(config.MONGO_DB_URI)
    pymongodb = _mongo_sync_.BrandrdXMusic

except Exception as e:
    LOGGER(__name__).error(f"فشل الاتصال بقاعدة البيانات: {e}")
    exit()
