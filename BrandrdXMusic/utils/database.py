import random
from typing import Dict, List, Union
from functools import wraps
from BrandrdXMusic.core.mongo import mongodb

# ====================================================================
# 🛡️ إعدادات الأمان وقواعد البيانات
# ====================================================================

# المعرفات الثابتة (Magic IDs)
GLOBAL_QUERY_ID = 98324
GLOBAL_AUTOEND_ID = 1234

# تعريف المجموعات (Collections)
authdb = mongodb.adminauth
authuserdb = mongodb.authuser
autoenddb = mongodb.autoend
assdb = mongodb.assistants
blacklist_chatdb = mongodb.blacklistChat
blockeddb = mongodb.blockedusers
chatsdb = mongodb.chats
chattopdb = mongodb.chattop_db
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

# الذاكرة المؤقتة (Caching)
active = []
activevideo = []
assistantdict = {}
autoend = {}
count = {}
channelconnect = {}
langm = {}
loop = {}
maintenance = []
nonadmin = {}
pause = {}
playmode = {}
playtype = {}
skipmode = {}
privatechats = {}
cleanmode = []
suggestion = {}
mute = {}
audio = {}
video = {}

# ====================================================================
# 🛡️ نظام الحماية (Safety Wrapper)
# ====================================================================

def safe_db(default_return=None):
    """
    ديكوريتور لتغليف دوال قاعدة البيانات وحمايتها من الانهيار.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # يمكن تفعيل طباعة الخطأ للتصحيح إذا أردت
                # print(f"⚠️ Database Error in {func.__name__}: {e}")
                return default_return
        return wrapper
    return decorator

# ====================================================================
# ⚡ قسم المساعدين (Assistants Logic) - متطور ومربوط
# ====================================================================

@safe_db(None)
async def get_assistant_number(chat_id: int) -> str:
    return assistantdict.get(chat_id)

async def get_client(assistant: int):
    """يجلب عميل المساعد بأمان بناءً على الرقم"""
    # استيراد داخلي لمنع Loop Import
    from BrandrdXMusic import userbot
    
    clients = {
        1: userbot.one,
        2: userbot.two,
        3: userbot.three,
        4: userbot.four,
        5: userbot.five
    }
    return clients.get(int(assistant), userbot.one)

@safe_db(None)
async def set_assistant_new(chat_id, number):
    number = int(number)
    await assdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"assistant": number}},
        upsert=True,
    )
    assistantdict[chat_id] = number

async def set_assistant(chat_id):
    from BrandrdXMusic.core.userbot import assistants
    if not assistants: return None

    ran_assistant = random.choice(assistants)
    assistantdict[chat_id] = ran_assistant
    
    try:
        await assdb.update_one(
            {"chat_id": chat_id},
            {"$set": {"assistant": ran_assistant}},
            upsert=True,
        )
    except: pass
    
    return await get_client(ran_assistant)

async def get_assistant(chat_id: int) -> str:
    from BrandrdXMusic.core.userbot import assistants

    assistant = assistantdict.get(chat_id)
    if not assistant:
        try:
            dbassistant = await assdb.find_one({"chat_id": chat_id})
            if not dbassistant:
                return await set_assistant(chat_id)
            
            got_assis = dbassistant["assistant"]
            if got_assis in assistants:
                assistantdict[chat_id] = got_assis
                return await get_client(got_assis)
            else:
                return await set_assistant(chat_id)
        except:
            return await set_assistant(chat_id)
    else:
        if assistant in assistants:
            return await get_client(assistant)
        else:
            return await set_assistant(chat_id)

async def set_calls_assistant(chat_id):
    from BrandrdXMusic.core.userbot import assistants
    if not assistants: return 1

    ran_assistant = random.choice(assistants)
    assistantdict[chat_id] = ran_assistant
    try:
        await assdb.update_one(
            {"chat_id": chat_id},
            {"$set": {"assistant": ran_assistant}},
            upsert=True,
        )
    except: pass
    return ran_assistant

async def group_assistant(self, chat_id: int) -> int:
    from BrandrdXMusic.core.userbot import assistants
    
    if not assistants: return self.one

    assistant = assistantdict.get(chat_id)
    if not assistant:
        try:
            dbassistant = await assdb.find_one({"chat_id": chat_id})
            if not dbassistant:
                assis = await set_calls_assistant(chat_id)
            else:
                assis = dbassistant["assistant"]
                if assis in assistants:
                    assistantdict[chat_id] = assis
                else:
                    assis = await set_calls_assistant(chat_id)
        except:
            assis = await set_calls_assistant(chat_id)
    else:
        if assistant in assistants:
            assis = assistant
        else:
            assis = await set_calls_assistant(chat_id)
            
    return await get_client(assis)

# ====================================================================
# 📊 الإحصائيات (Stats)
# ====================================================================

@safe_db(0)
async def get_queries() -> int:
    mode = await queriesdb.find_one({"chat_id": GLOBAL_QUERY_ID})
    return mode["mode"] if mode else 0

@safe_db(None)
async def set_queries(mode: int):
    queries = await queriesdb.find_one({"chat_id": GLOBAL_QUERY_ID})
    if queries:
        mode = queries["mode"] + mode
    await queriesdb.update_one(
        {"chat_id": GLOBAL_QUERY_ID}, {"$set": {"mode": mode}}, upsert=True
    )

# ====================================================================
# 🔝 التوب (Top Chats & Users)
# ====================================================================

@safe_db({})
async def get_top_chats() -> dict:
    results = {}
    async for chat in chattopdb.find({"chat_id": {"$lt": 0}}):
        chat_id = chat["chat_id"]
        total = sum(item["spot"] for item in chat["vidid"].values() if item["spot"] > 0)
        results[chat_id] = total
    return results

@safe_db({})
async def get_global_tops() -> dict:
    results = {}
    async for chat in chattopdb.find({"chat_id": {"$lt": 0}}):
        for i, data in chat["vidid"].items():
            if data["spot"] > 0:
                if i not in results:
                    results[i] = {"spot": data["spot"], "title": data["title"]}
                else:
                    results[i]["spot"] += data["spot"]
    return results

@safe_db({})
async def get_particulars(chat_id: int) -> Dict[str, int]:
    ids = await chattopdb.find_one({"chat_id": chat_id})
    return ids["vidid"] if ids else {}

@safe_db(False)
async def get_particular_top(chat_id: int, name: str) -> Union[bool, dict]:
    ids = await get_particulars(chat_id)
    return ids.get(name, False)

@safe_db(None)
async def update_particular_top(chat_id: int, name: str, vidid: dict):
    ids = await get_particulars(chat_id)
    ids[name] = vidid
    await chattopdb.update_one(
        {"chat_id": chat_id}, {"$set": {"vidid": ids}}, upsert=True
    )

@safe_db({})
async def get_userss(chat_id: int) -> Dict[str, int]:
    ids = await userdb.find_one({"chat_id": chat_id})
    return ids["vidid"] if ids else {}

@safe_db(False)
async def get_user_top(chat_id: int, name: str) -> Union[bool, dict]:
    ids = await get_userss(chat_id)
    return ids.get(name, False)

@safe_db(None)
async def update_user_top(chat_id: int, name: str, vidid: dict):
    ids = await get_userss(chat_id)
    ids[name] = vidid
    await userdb.update_one({"chat_id": chat_id}, {"$set": {"vidid": ids}}, upsert=True)

@safe_db({})
async def get_topp_users() -> dict:
    results = {}
    async for chat in userdb.find({"chat_id": {"$gt": 0}}):
        total = sum(item["spot"] for item in chat["vidid"].values() if item["spot"] > 0)
        results[chat["chat_id"]] = total
    return results

# ====================================================================
# ⚙️ الإعدادات (Config & Play Modes)
# ====================================================================

@safe_db(False)
async def is_skipmode(chat_id: int) -> bool:
    mode = skipmode.get(chat_id)
    if mode is None:
        user = await skipdb.find_one({"chat_id": chat_id})
        skipmode[chat_id] = not bool(user)
        return skipmode[chat_id]
    return mode

@safe_db(None)
async def skip_on(chat_id: int):
    skipmode[chat_id] = True
    await skipdb.delete_one({"chat_id": chat_id})

@safe_db(None)
async def skip_off(chat_id: int):
    skipmode[chat_id] = False
    await skipdb.insert_one({"chat_id": chat_id})

@safe_db(5)
async def get_upvote_count(chat_id: int) -> int:
    mode = count.get(chat_id)
    if not mode:
        mode = await countdb.find_one({"chat_id": chat_id})
        if not mode: return 5
        count[chat_id] = mode["mode"]
        return mode["mode"]
    return mode

@safe_db(None)
async def set_upvotes(chat_id: int, mode: int):
    count[chat_id] = mode
    await countdb.update_one(
        {"chat_id": chat_id}, {"$set": {"mode": mode}}, upsert=True
    )

@safe_db(False)
async def is_autoend() -> bool:
    user = await autoenddb.find_one({"chat_id": GLOBAL_AUTOEND_ID})
    return bool(user)

@safe_db(None)
async def autoend_on():
    await autoenddb.insert_one({"chat_id": GLOBAL_AUTOEND_ID})

@safe_db(None)
async def autoend_off():
    await autoenddb.delete_one({"chat_id": GLOBAL_AUTOEND_ID})

@safe_db(0)
async def get_loop(chat_id: int) -> int:
    return loop.get(chat_id, 0)

@safe_db(None)
async def set_loop(chat_id: int, mode: int):
    loop[chat_id] = mode

@safe_db(None)
async def get_cmode(chat_id: int) -> int:
    mode = channelconnect.get(chat_id)
    if not mode:
        mode = await channeldb.find_one({"chat_id": chat_id})
        if not mode: return None
        channelconnect[chat_id] = mode["mode"]
        return mode["mode"]
    return mode

@safe_db(None)
async def set_cmode(chat_id: int, mode: int):
    channelconnect[chat_id] = mode
    await channeldb.update_one(
        {"chat_id": chat_id}, {"$set": {"mode": mode}}, upsert=True
    )

@safe_db("Everyone")
async def get_playtype(chat_id: int) -> str:
    mode = playtype.get(chat_id)
    if not mode:
        mode = await playtypedb.find_one({"chat_id": chat_id})
        if not mode:
            playtype[chat_id] = "Everyone"
            return "Everyone"
        playtype[chat_id] = mode["mode"]
        return mode["mode"]
    return mode

@safe_db(None)
async def set_playtype(chat_id: int, mode: str):
    playtype[chat_id] = mode
    await playtypedb.update_one(
        {"chat_id": chat_id}, {"$set": {"mode": mode}}, upsert=True
    )

@safe_db("Direct")
async def get_playmode(chat_id: int) -> str:
    mode = playmode.get(chat_id)
    if not mode:
        mode = await playmodedb.find_one({"chat_id": chat_id})
        if not mode:
            playmode[chat_id] = "Direct"
            return "Direct"
        playmode[chat_id] = mode["mode"]
        return mode["mode"]
    return mode

@safe_db(None)
async def set_playmode(chat_id: int, mode: str):
    playmode[chat_id] = mode
    await playmodedb.update_one(
        {"chat_id": chat_id}, {"$set": {"mode": mode}}, upsert=True
    )

@safe_db("en")
async def get_lang(chat_id: int) -> str:
    mode = langm.get(chat_id)
    if not mode:
        lang = await langdb.find_one({"chat_id": chat_id})
        if not lang:
            langm[chat_id] = "en"
            return "en"
        langm[chat_id] = lang["lang"]
        return lang["lang"]
    return mode

@safe_db(None)
async def set_lang(chat_id: int, lang: str):
    langm[chat_id] = lang
    await langdb.update_one({"chat_id": chat_id}, {"$set": {"lang": lang}}, upsert=True)

# ====================================================================
# ⏸️ الموسيقى (Music State)
# ====================================================================

async def is_music_playing(chat_id: int) -> bool:
    return pause.get(chat_id, False)

async def music_on(chat_id: int):
    pause[chat_id] = True

async def music_off(chat_id: int):
    pause[chat_id] = False

async def is_muted(chat_id: int) -> bool:
    return mute.get(chat_id, False)

async def mute_on(chat_id: int):
    mute[chat_id] = True

async def mute_off(chat_id: int):
    mute[chat_id] = False

# ====================================================================
# 🔴 القوائم النشطة والمحظورة (Active & Blacklist)
# ====================================================================

async def get_active_chats() -> list:
    return active

async def is_active_chat(chat_id: int) -> bool:
    return chat_id in active

async def add_active_chat(chat_id: int):
    if chat_id not in active: active.append(chat_id)

async def remove_active_chat(chat_id: int):
    if chat_id in active: active.remove(chat_id)

async def get_active_video_chats() -> list:
    return activevideo

async def is_active_video_chat(chat_id: int) -> bool:
    return chat_id in activevideo

async def add_active_video_chat(chat_id: int):
    if chat_id not in activevideo: activevideo.append(chat_id)

async def remove_active_video_chat(chat_id: int):
    if chat_id in activevideo: activevideo.remove(chat_id)

@safe_db(False)
async def check_nonadmin_chat(chat_id: int) -> bool:
    user = await authdb.find_one({"chat_id": chat_id})
    return bool(user)

@safe_db(False)
async def is_nonadmin_chat(chat_id: int) -> bool:
    mode = nonadmin.get(chat_id)
    if mode is None:
        user = await authdb.find_one({"chat_id": chat_id})
        nonadmin[chat_id] = bool(user)
        return nonadmin[chat_id]
    return mode

@safe_db(None)
async def add_nonadmin_chat(chat_id: int):
    nonadmin[chat_id] = True
    if not await check_nonadmin_chat(chat_id):
        await authdb.insert_one({"chat_id": chat_id})

@safe_db(None)
async def remove_nonadmin_chat(chat_id: int):
    nonadmin[chat_id] = False
    if await check_nonadmin_chat(chat_id):
        await authdb.delete_one({"chat_id": chat_id})

@safe_db(False)
async def is_on_off(on_off: int) -> bool:
    onoff = await onoffdb.find_one({"on_off": on_off})
    return bool(onoff)

@safe_db(None)
async def add_on(on_off: int):
    if not await is_on_off(on_off):
        await onoffdb.insert_one({"on_off": on_off})

@safe_db(None)
async def add_off(on_off: int):
    if await is_on_off(on_off):
        await onoffdb.delete_one({"on_off": on_off})

@safe_db(True)
async def is_maintenance():
    if not maintenance:
        get = await onoffdb.find_one({"on_off": 1})
        if not get:
            maintenance.clear()
            maintenance.append(2)
            return True
        else:
            maintenance.clear()
            maintenance.append(1)
            return False
    return 1 not in maintenance

@safe_db(None)
async def maintenance_off():
    maintenance.clear()
    maintenance.append(2)
    if await is_on_off(1):
        await onoffdb.delete_one({"on_off": 1})

@safe_db(None)
async def maintenance_on():
    maintenance.clear()
    maintenance.append(1)
    if not await is_on_off(1):
        await onoffdb.insert_one({"on_off": 1})

@safe_db(False)
async def is_served_user(user_id: int) -> bool:
    user = await usersdb.find_one({"user_id": user_id})
    return bool(user)

@safe_db([])
async def get_served_users() -> list:
    return [user async for user in usersdb.find({"user_id": {"$gt": 0}})]

@safe_db(None)
async def add_served_user(user_id: int):
    if not await is_served_user(user_id):
        await usersdb.insert_one({"user_id": user_id})

@safe_db([])
async def get_served_chats() -> list:
    return [chat async for chat in chatsdb.find({"chat_id": {"$lt": 0}})]

@safe_db(False)
async def is_served_chat(chat_id: int) -> bool:
    chat = await chatsdb.find_one({"chat_id": chat_id})
    return bool(chat)

@safe_db(None)
async def add_served_chat(chat_id: int):
    if not await is_served_chat(chat_id):
        await chatsdb.insert_one({"chat_id": chat_id})

@safe_db(None)
async def delete_served_chat(chat_id: int):
    await chatsdb.delete_one({"chat_id": chat_id})

@safe_db([])
async def blacklisted_chats() -> list:
    return [chat["chat_id"] async for chat in blacklist_chatdb.find({"chat_id": {"$lt": 0}})]

@safe_db(False)
async def blacklist_chat(chat_id: int) -> bool:
    if not await blacklist_chatdb.find_one({"chat_id": chat_id}):
        await blacklist_chatdb.insert_one({"chat_id": chat_id})
        return True
    return False

@safe_db(False)
async def whitelist_chat(chat_id: int) -> bool:
    if await blacklist_chatdb.find_one({"chat_id": chat_id}):
        await blacklist_chatdb.delete_one({"chat_id": chat_id})
        return True
    return False

# ====================================================================
# 🔐 إدارة المستخدمين الموثوقين (Auth Users)
# ====================================================================

@safe_db({})
async def _get_authusers(chat_id: int) -> Dict[str, int]:
    _notes = await authuserdb.find_one({"chat_id": chat_id})
    return _notes["notes"] if _notes else {}

@safe_db([])
async def get_authuser_names(chat_id: int) -> List[str]:
    _notes = await _get_authusers(chat_id)
    return list(_notes.keys())

@safe_db(False)
async def get_authuser(chat_id: int, name: str) -> Union[bool, dict]:
    _notes = await _get_authusers(chat_id)
    return _notes.get(name, False)

@safe_db(None)
async def save_authuser(chat_id: int, name: str, note: dict):
    _notes = await _get_authusers(chat_id)
    _notes[name] = note
    await authuserdb.update_one(
        {"chat_id": chat_id}, {"$set": {"notes": _notes}}, upsert=True
    )

@safe_db(False)
async def delete_authuser(chat_id: int, name: str) -> bool:
    notesd = await _get_authusers(chat_id)
    if name in notesd:
        del notesd[name]
        await authuserdb.update_one(
            {"chat_id": chat_id},
            {"$set": {"notes": notesd}},
            upsert=True,
        )
        return True
    return False

# ====================================================================
# 🚫 الحظر العام (GBan)
# ====================================================================

@safe_db([])
async def get_gbanned() -> list:
    return [user["user_id"] async for user in gbansdb.find({"user_id": {"$gt": 0}})]

@safe_db(False)
async def is_gbanned_user(user_id: int) -> bool:
    user = await gbansdb.find_one({"user_id": user_id})
    return bool(user)

@safe_db(None)
async def add_gban_user(user_id: int):
    if not await is_gbanned_user(user_id):
        await gbansdb.insert_one({"user_id": user_id})

@safe_db(None)
async def remove_gban_user(user_id: int):
    if await is_gbanned_user(user_id):
        await gbansdb.delete_one({"user_id": user_id})

# ====================================================================
# 👑 المطورين (Sudoers)
# ====================================================================

@safe_db([])
async def get_sudoers() -> list:
    sudoers = await sudoersdb.find_one({"sudo": "sudo"})
    return sudoers["sudoers"] if sudoers else []

@safe_db(True)
async def add_sudo(user_id: int) -> bool:
    sudoers = await get_sudoers()
    if user_id not in sudoers:
        sudoers.append(user_id)
        await sudoersdb.update_one(
            {"sudo": "sudo"}, {"$set": {"sudoers": sudoers}}, upsert=True
        )
        return True
    return False

@safe_db(True)
async def remove_sudo(user_id: int) -> bool:
    sudoers = await get_sudoers()
    if user_id in sudoers:
        sudoers.remove(user_id)
        await sudoersdb.update_one(
            {"sudo": "sudo"}, {"$set": {"sudoers": sudoers}}, upsert=True
        )
        return True
    return False

# ====================================================================
# 🚫 المستخدمين المحظורים (Banned Users)
# ====================================================================

@safe_db([])
async def get_banned_users() -> list:
    return [user["user_id"] async for user in blockeddb.find({"user_id": {"$gt": 0}})]

@safe_db(0)
async def get_banned_count() -> int:
    return await blockeddb.count_documents({"user_id": {"$gt": 0}})

@safe_db(False)
async def is_banned_user(user_id: int) -> bool:
    user = await blockeddb.find_one({"user_id": user_id})
    return bool(user)

@safe_db(None)
async def add_banned_user(user_id: int):
    if not await is_banned_user(user_id):
        await blockeddb.insert_one({"user_id": user_id})

@safe_db(None)
async def remove_banned_user(user_id: int):
    if await is_banned_user(user_id):
        await blockeddb.delete_one({"user_id": user_id})

# ====================================================================
# 🔒 الخاص والاقتراحات (Private & Suggestion)
# ====================================================================

@safe_db([])
async def get_private_served_chats() -> list:
    return [chat async for chat in privatedb.find({"chat_id": {"$lt": 0}})]

@safe_db(False)
async def is_served_private_chat(chat_id: int) -> bool:
    chat = await privatedb.find_one({"chat_id": chat_id})
    return bool(chat)

@safe_db(None)
async def add_private_chat(chat_id: int):
    if not await is_served_private_chat(chat_id):
        await privatedb.insert_one({"chat_id": chat_id})

@safe_db(None)
async def remove_private_chat(chat_id: int):
    if await is_served_private_chat(chat_id):
        await privatedb.delete_one({"chat_id": chat_id})

@safe_db(False)
async def is_suggestion(chat_id: int) -> bool:
    mode = suggestion.get(chat_id)
    if mode is None:
        user = await suggdb.find_one({"chat_id": chat_id})
        suggestion[chat_id] = not bool(user)
        return suggestion[chat_id]
    return mode

@safe_db(None)
async def suggestion_on(chat_id: int):
    suggestion[chat_id] = True
    await suggdb.delete_one({"chat_id": chat_id})

@safe_db(None)
async def suggestion_off(chat_id: int):
    suggestion[chat_id] = False
    await suggdb.insert_one({"chat_id": chat_id})

@safe_db(True)
async def is_cleanmode_on(chat_id: int) -> bool:
    return chat_id not in cleanmode

async def cleanmode_off(chat_id: int):
    if chat_id not in cleanmode: cleanmode.append(chat_id)

async def cleanmode_on(chat_id: int):
    if chat_id in cleanmode: cleanmode.remove(chat_id)

# ====================================================================
# 🤖 البوتات المستنسخة (Clone Bots)
# ====================================================================

@safe_db(False)
async def is_served_user_clone(user_id: int) -> bool:
    user = await usersdbc.find_one({"user_id": user_id})
    return bool(user)

@safe_db([])
async def get_served_users_clone() -> list:
    return [user async for user in usersdbc.find({"user_id": {"$gt": 0}})]

@safe_db(None)
async def add_served_user_clone(user_id: int):
    if not await is_served_user_clone(user_id):
        await usersdbc.insert_one({"user_id": user_id})

@safe_db([])
async def get_served_chats_clone() -> list:
    return [chat async for chat in chatsdbc.find({"chat_id": {"$lt": 0}})]

@safe_db(False)
async def is_served_chat_clone(chat_id: int) -> bool:
    chat = await chatsdbc.find_one({"chat_id": chat_id})
    return bool(chat)

@safe_db(None)
async def add_served_chat_clone(chat_id: int):
    if not await is_served_chat_clone(chat_id):
        await chatsdbc.insert_one({"chat_id": chat_id})

@safe_db(None)
async def delete_served_chat_clone(chat_id: int):
    await chatsdbc.delete_one({"chat_id": chat_id})
