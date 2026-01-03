# BrandrdXMusic/core/database/connections.py

import asyncio
from BrandrdXMusic.core.mongo import mongodb

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
chatsdbc = mongodb.chatsc
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
usersdbc = mongodb.tgusersdbc

privatedb = mongodb.privatechats
suggdb = mongodb.suggestion
cleandb = mongodb.cleanmode
queriesdb = mongodb.queries
userdb = mongodb.userstats
videodb = mongodb.vipvideocalls
chattopdb = mongodb.chattop

# ==========================
# In-Memory Caches
# ==========================
_active_audio: list = []
_active_video: list = []

_assistant_cache: dict = {}
_count_cache: dict = {}
_channel_connect: dict = {}
_lang_cache: dict = {}
_loop_state: dict = {}
_nonadmin_cache: dict = {}
_pause_state: dict = {}
_playmode: dict = {}
_playtype: dict = {}
_skipmode: dict = {}
_suggestion: dict = {}
_mute_state: dict = {}

_cleanmode: list = []
_maintenance: list = []

# ==========================
# Async Locks
# ==========================
DB_LOCK = asyncio.Lock()
ACTIVE_LOCK = asyncio.Lock()
ASSISTANT_LOCK = asyncio.Lock()
