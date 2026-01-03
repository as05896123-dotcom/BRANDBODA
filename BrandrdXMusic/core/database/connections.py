# core/database/connections.py

import asyncio
from BrandrdXMusic.core.mongo import mongodb, pymongodb

# ==========================
# MongoDB Collections
# ==========================
authdb = mongodb.adminauth
authuserdb = mongodb.authuser
autoenddb = mongodb.autoend
assdb = mongodb.assistants
blacklist_chatdb = mongodb.blacklistChat
blockeddb = mongodb.blockedusers
chatsdb = mongodb.chats
channeldb = mongodb.cplaymode
countdb = mongodb.upcount
gbansdb = mongodb.gban
langdb = mongodb.language
onoffdb = mongodb.onoffper
playmodedb = mongodb.playmode
playtypedb = mongodb.playtypedb
skipdb = mongodb.skipmode
sudoersdb = mongodb.sudoers
usersdb = mongodb.tgusersdb
privatedb = mongodb.privatechats
suggdb = mongodb.suggestion
cleandb = mongodb.cleanmode
queriesdb = mongodb.queries
userdb = mongodb.userstats
videodb = mongodb.vipvideocalls
chatsdbc = mongodb.chatsc
usersdbc = mongodb.tgusersdbc
chattopdb = mongodb.chattop

# ==========================
# In-Memory Caches
# ==========================
_active_audio = []
_active_video = []
_assistant_cache = {}
_count_cache = {}
_channel_connect = {}
_lang_cache = {}
_loop_state = {}
_maintenance = []
_nonadmin_cache = {}
_pause_state = {}
_playmode = {}
_playtype = {}
_skipmode = {}
_cleanmode = []
_suggestion = {}
_mute_state = {}

# ==========================
# Locks
# ==========================
DB_LOCK = asyncio.Lock()
ACTIVE_LOCK = asyncio.Lock()
ASSISTANT_LOCK = asyncio.Lock()
