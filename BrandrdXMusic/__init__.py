from BrandrdXMusic.logging import LOGGER

from BrandrdXMusic.core.bot import Hotty
from BrandrdXMusic.core.dir import dirr
from BrandrdXMusic.core.git import git
from BrandrdXMusic.core.userbot import Userbot
from BrandrdXMusic.misc import dbb, heroku

from SafoneAPI import SafoneAPI

# ===============================
# تهيئة المجلدات والبيئة
# ===============================

# إنشاء المجلدات المطلوبة
dirr()

# ❌ تعطيل التحديث التلقائي من Git
# السبب: Fly / Docker لا يدعم git fetch بدون credentials
# git()

# تهيئة قواعد البيانات
dbb()

# تهيئة Heroku (لو موجود)
heroku()

# ===============================
# تشغيل البوتات
# ===============================

# البوت الأساسي
app = Hotty()

# الحساب المساعد
userbot = Userbot()

# API خارجي
api = SafoneAPI()

# ===============================
# منصات التشغيل
# ===============================

from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()

# ===============================
# اسم التطبيق
# ===============================

APP = "Systumm_music_bot"
