# ======================================
# BrandrdXMusic - Main Package Init
# ======================================

import asyncio
import logging
import sys

from BrandrdXMusic.logging import LOGGER

# ===============================
# Core imports
# ===============================

from BrandrdXMusic.core.bot import Hotty as _BotClient
from BrandrdXMusic.core.userbot import Userbot as _UserbotClient
from BrandrdXMusic.core.dir import dirr
from BrandrdXMusic.misc import dbb, heroku

# ===============================
# External APIs
# ===============================

try:
    from SafoneAPI import SafoneAPI
except Exception:
    SafoneAPI = None

# ===============================
# تهيئة المجلدات والبيئة
# ===============================

dirr()       # إنشاء الفولدرات
dbb()        # تهيئة قواعد البيانات
heroku()     # Heroku env (لو موجود)

# ===============================
# Logging
# ===============================

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# ===============================
# Clients
# ===============================

app = _BotClient()          # البوت الأساسي
userbot = _UserbotClient() # الحساب المساعد

# ===============================
# API Object
# ===============================

api = SafoneAPI() if SafoneAPI else None

# ===============================
# Platforms
# ===============================

try:
    from BrandrdXMusic.platforms.apple import AppleAPI
    from BrandrdXMusic.platforms.carbon import CarbonAPI
    from BrandrdXMusic.platforms.soundcloud import SoundAPI
    from BrandrdXMusic.platforms.spotify import SpotifyAPI
    from BrandrdXMusic.platforms.resso import RessoAPI
    from BrandrdXMusic.platforms.telegram import TeleAPI
    from BrandrdXMusic.platforms.youtube import YouTubeAPI

    Apple = AppleAPI()
    Carbon = CarbonAPI()
    SoundCloud = SoundAPI()
    Spotify = SpotifyAPI()
    Resso = RessoAPI()
    Telegram = TeleAPI()
    YouTube = YouTubeAPI()

except Exception as e:
    LOGGER(__name__).warning(f"⚠️ فشل تحميل بعض المنصات: {e}")
    Apple = Carbon = SoundCloud = Spotify = Resso = Telegram = YouTube = None

# ===============================
# Globals
# ===============================

APP = "Systumm_music_bot"

__all__ = [
    "app",
    "userbot",
    "api",
    "Apple",
    "Carbon",
    "SoundCloud",
    "Spotify",
    "Resso",
    "Telegram",
    "YouTube",
    "LOGGER",
    "APP",
]
