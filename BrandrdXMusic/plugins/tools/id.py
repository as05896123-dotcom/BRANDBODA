from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.enums import ChatMemberStatus
from pymongo import MongoClient

from BrandrdXMusic import app
from config import MONGO_DB_URI  # استدعاء رابط قاعدة البيانات

# --- إعداد قاعدة البيانات (MongoDB) ---
try:
    _client = MongoClient(MONGO_DB_URI)
    db = _client["BrandrdX_ID_System"] # اسم قاعدة البيانات
    col = db["id_triggers"] # اسم المجموعة
except Exception as e:
    print(f"خطأ في الاتصال بقاعدة البيانات: {e}")
    col = None

# --- تحميل الكلمات من القاعدة عند التشغيل ---
def load_triggers():
    default_triggers = {"ايدي", "id", "ايدى", "معلوماتي"}
    if col is None:
        return default_triggers
    
    try:
        # جلب الكلمات المحفوظة من المونجو
        saved_triggers = [doc["word"] for doc in col.find()]
        # دمج الكلمات الافتراضية مع المحفوظة
        return default_triggers.union(set(saved_triggers))
    except:
        return default_triggers

# هذه القائمة في الذاكرة لسرعة الاستجابة
ID_TRIGGERS = load_triggers()

# --- فلتر التحقق من الكلمات ---
async def custom_id_filter(_, __, message: Message):
    if not message.text:
        return False
    return message.text.strip() in ID_TRIGGERS

id_filter = filters.create(custom_id_filter)


# --- 1. أمر إضافة كلمة جديدة للايدي (مع الحفظ في Mongo) ---
@app.on_message(filters.command(["اضافة نص ايدي", "إضافة نص ايدي"], prefixes="") & filters.group)
async def add_id_trigger(client, message):
    try:
        trigger = message.text.replace("إضافة نص ايدي", "").replace("اضافة نص ايدي", "").strip()
        
        if not trigger:
            await message.reply_text("**يـرجـى كـتـابـة الـنـص الـذي تـريـد إضـافـتـه.**")
            return

        if trigger in ID_TRIGGERS:
            await message.reply_text(f"**الـنـص :** ({trigger}) **مـوجـود بـالـفـعـل.**")
            return

        # 1. الحفظ في الذاكرة الحالية
        ID_TRIGGERS.add(trigger)
        
        # 2. الحفظ في قاعدة البيانات (للأبد)
        if col is not None:
            col.insert_one({"word": trigger})
            
        await message.reply_text(f"**تـم إضـافـة الـنـص :** ({trigger}) **وحـفـظـه فـي الـنـظـام.**")

    except Exception as e:
        await message.reply_text(f"**حـدث خـطـأ أثناء الحفظ:** {e}")


# --- 2. أمر حذف كلمة من الايدي (مع الحذف من Mongo) ---
@app.on_message(filters.command(["مسح نص ايدي", "حذف نص ايدي"], prefixes="") & filters.group)
async def del_id_trigger(client, message):
    trigger = message.text.replace("مسح نص ايدي", "").replace("حذف نص ايدي", "").strip()
    
    # لا يمكن حذف الأوامر الأساسية
    basic_cmds = {"ايدي", "id", "ايدى", "معلوماتي"}
    if trigger in basic_cmds:
        await message.reply_text("**لا يـمـكـن حـذف الأوامـر الأسـاسـيـة.**")
        return

    if trigger in ID_TRIGGERS:
        # 1. الحذف من الذاكرة
        ID_TRIGGERS.remove(trigger)
        
        # 2. الحذف من قاعدة البيانات
        if col is not None:
            col.delete_one({"word": trigger})
            
        await message.reply_text(f"**تـم حـذف الـنـص :** ({trigger}) **مـن الـنـظـام.**")
    else:
        await message.reply_text("**هـذا الـنـص غـيـر مـوجـود.**")


# --- 3. دالة جلب المعلومات ---
@app.on_message(id_filter & filters.group)
async def get_custom_id(client, message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    else:
        user = message.from_user

    wait_msg = await message.reply_text("جـاري الـجـلـب...")

    try:
        full_user = await client.get_chat(user.id)
        bio = full_user.bio if full_user.bio else "لا يوجد نبذة"
        
        # تحديد الرتبة
        try:
            member = await message.chat.get_member(user.id)
            if member.status == ChatMemberStatus.OWNER:
                status = "المالك"
            elif member.status == ChatMemberStatus.ADMINISTRATOR:
                status = "مشرف"
            elif member.status == ChatMemberStatus.MEMBER:
                status = "عضو"
            elif member.status == ChatMemberStatus.RESTRICTED:
                status = "مقيد"
            elif member.status == ChatMemberStatus.BANNED:
                status = "محظور"
            else:
                status = "غير معروف"
        except:
            status = "عضو"

        name = user.first_name
        username = f"@{user.username}" if user.username else "لا يوجد"
        user_id = user.id
        mention = user.mention("الرابط")
        chat_title = message.chat.title
        
        # التنسيق المطلوب: الرتبة داخل كديشة والإيموجي المحددة
        text = f"""
💕 ɴᴀᴍᴇ - {name}
🤍 ᴜѕᴇ - {username}
🧚 ѕᴛᴀ - `{status}`
♥️ ᴍѕɢ - {mention}
🤎 ɪᴅ - {user_id}
💞 ᴛɪᴛʟᴇ - {chat_title}
🤍 ʙɪᴏ - {bio}
"""
        
        close_btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
        ])

        if full_user.photo:
            await message.reply_photo(
                photo=full_user.photo.big_file_id,
                caption=text,
                reply_markup=close_btn
            )
        else:
            await message.reply_text(
                text=text,
                reply_markup=close_btn
            )

        await wait_msg.delete()

    except Exception as e:
        await wait_msg.edit(f"**حـدث خـطـأ :** {e}")
