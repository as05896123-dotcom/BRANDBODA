# BrandrdXMusic/__init__.py
import asyncio
import sys
from SafoneAPI import SafoneAPI

from BrandrdXMusic.core.bot import Hotty
from BrandrdXMusic.core.dir import dirr
from BrandrdXMusic.core.git import git
from BrandrdXMusic.core.userbot import Userbot
from BrandrdXMusic.misc import dbb, heroku
from .logging import LOGGER

# ====================================================
# 🚀 PERFORMANCE BOOST: تفعيل UVLOOP (مثل Alexa)
# بيخلي استجابة البوت أسرع بكتير
# ====================================================
if sys.platform != "win32":
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        LOGGER(__name__).info("✅ UVLOOP Enabled: Performance Optimized.")
    except ImportError:
        LOGGER(__name__).warning("⚠️ Uvloop not found, using default asyncio.")

# ====================================================
# 📂 INITIALIZATION: تهيئة النظام
# ====================================================
dirr()   # تنظيف المجلدات
git()    # فحص التحديثات
dbb()    # تحميل قاعدة البيانات
heroku() # إعدادات هيروكو

# ====================================================
# 🤖 CLIENTS: التعريف المباشر (زي Annie و Alexa)
# لازم يتعرفوا هنا فوراً عشان باقي الملفات تشوفهم
# ====================================================
app = Hotty()
api = SafoneAPI()
userbot = Userbot()

# ====================================================
# 🎵 PLATFORMS: منصات التشغيل
# ====================================================
from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()
