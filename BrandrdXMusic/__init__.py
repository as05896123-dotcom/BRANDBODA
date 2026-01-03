# ======================================
# BrandrdXMusic - Package Init (SAFE)
# ======================================

# ❌ ممنوع import logging هنا
# ❌ ممنوع logging.basicConfig

from BrandrdXMusic.logging import LOGGER

# ===============================
# Core
# ===============================

from BrandrdXMusic.core.bot import Hotty as _BotClient
from BrandrdXMusic.core.userbot import Userbot as _UserbotClient
from BrandrdXMusic.core.dir import dirr
from BrandrdXMusic.misc import dbb, heroku

# ===============================
# Environment setup
# ===============================

dirr()
dbb()
heroku()

# ===============================
# Clients
# ===============================

app = _BotClient()
userbot = _UserbotClient()

# ===============================
# External API
# ===============================

try:
    from SafoneAPI import SafoneAPI
    api = SafoneAPI()
except Exception:
    api = None
    LOGGER(__name__).warning("⚠️ SafoneAPI غير متوفر")

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
