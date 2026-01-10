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
# ❌ شلت كود UVLOOP من هنا
# لأن ملف run.py هو اللي بيقوم بالمهمة دي خلاص
# ====================================================

# ====================================================
# 📂 INITIALIZATION: تهيئة النظام
# ====================================================
dirr()
git()
dbb()
heroku()

# ====================================================
# 🤖 CLIENTS:
# app و userbot بيتم إنشائهم هنا
# وهياخدوا الـ Loop تلقائياً من ملف run.py
# ====================================================
app = Hotty()
api = SafoneAPI()
userbot = Userbot()

# ====================================================
# 🎵 PLATFORMS
# ====================================================
from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()
