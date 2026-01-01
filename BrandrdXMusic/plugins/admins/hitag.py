from BrandrdXMusic import app 
import asyncio
import random
from pyrogram import Client, filters
from pyrogram.enums import ChatType, ChatMemberStatus
from pyrogram.errors import UserNotParticipant
from pyrogram.types import ChatPermissions

spam_chats = []

# تم تبسيط الإيموجي ليكون رمزاً واحداً أو اثنين
EMOJI = [ "🦋", "🌸", "🌹", "🍬", "⚡️", "✨", "🎈", "🧸", "🤍", "🌿", "🍉", "🍓", "☕️", "☁️", "💜", "🪴", "🐬", "🦄", "🌙", "💤" ]

# قائمة الدردشة العامة (منشن للحديث) - بدون خط عريض
TAGMES = [ 
    "وينك يا حلو مختفي؟",
    "تغديت ولا لسه؟",
    "هلا والله، نورت القروب",
    "كيف الحال يا غالي؟",
    "ممكن نتعرف؟",
    "شو رأيك نلعب لعبة؟",
    "منورين الشباب والبنات",
    "يا جماعة الجو يحتاج قهوة",
    "وين رحتوا؟ تعالوا نسولف",
    "صليت على النبي اليوم؟",
    "شكلكم نايمين، اصحوا",
    "هلا بالزين كله",
    "أحلى تحية لك",
    "عرفنا عليك أكثر",
    "شو قاعد تسوي الحين؟",
    "مزاجك كيف اليوم؟",
    "جوعان ولا شبعان؟",
    "أحبك في الله يا أخي",
    "خلينا نفتح موضوع للنقاش",
    "القروب نايم، ليش؟",
    "يا هلا باللي حضر",
    "سمعنا نكتة أو شي يضحك",
    "كيف كان يومك؟",
    "وحشتونا والله",
    "مسا الخير والسرور",
    "صباح الورد والياسمين",
    "دير بالك على نفسك",
    "ابتسم، الدنيا ما تسوى",
    "منور الشات بوجودك",
    "كل عام وانت بخير"
]

# قائمة حكم وأقوال (Life Tag) - بدون خط عريض
VC_TAG = [
    "الحياة مدرسة، والناس أسئلة، والأيام إجابات",
    "لا تتوقف عندما تتعب، توقف عندما تنتهي",
    "الصمت هو أفضل جواب لمن لا يقدر كلماتك",
    "كن قوياً لأجلك",
    "عامل الناس بأخلاقك لا بأخلاقهم",
    "كل مر سيمر",
    "لا تيأس، فالله معك",
    "الحياة قصيرة، لا تضيعها في الحزن",
    "كن أنت التغيير الذي تريد أن تراه في العالم",
    "الأمل هو حلم اليقظة",
    "الصبر مفتاح الفرج",
    "القناعة كنز لا يفنى",
    "لا تحزن على ما فات، واستبشر بما هو آت",
    "الكلمة الطيبة صدقة",
    "من جد وجد ومن زرع حصد",
    "الوقت كالسيف إن لم تقطعه قطعك",
    "رضا الناس غاية لا تدرك",
    "كن جميلاً تر الوجود جميلاً",
    "العلم نور والجهل ظلام",
    "احفظ الله يحفظك",
    "لا تؤجل عمل اليوم إلى الغد",
    "الصديق وقت الضيق",
    "عامل الناس كما تحب أن يعاملوك",
    "السعادة في العطاء لا في الأخذ",
    "لا تندم على ماضٍ ولى",
    "كن متفائلاً دائماً",
    "الثقة بالنفس طريق النجاح",
    "لا يضيع حق وراءه مطالب",
    "التواضع يرفع من شأنك",
    "الابتسامة في وجه أخيك صدقة"
]


@app.on_message(filters.command(["تاك", "منشن", "tag"], prefixes=["/", "@", "#", ""]))
async def mentionall(client, message):
    chat_id = message.chat.id
    if message.chat.type == ChatType.PRIVATE:
        return await message.reply("هذا الأمر يعمل في المجموعات فقط.")

    is_admin = False
    try:
        participant = await client.get_chat_member(chat_id, message.from_user.id)
    except UserNotParticipant:
        is_admin = False
    else:
        if participant.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        ):
            is_admin = True
    if not is_admin:
        return await message.reply("أنت لست مشرفاً، هذا الأمر للمشرفين فقط.")

    if message.reply_to_message and message.text:
        return await message.reply("اكتب (تاك) أو (منشن) لبدء المنشن.")
    elif message.text:
        mode = "text_on_cmd"
        msg = message.text
    elif message.reply_to_message:
        mode = "text_on_reply"
        msg = message.reply_to_message
        if not msg:
            return await message.reply("اكتب (تاك) للبدء.")
    else:
        return await message.reply("اكتب (تاك) للبدء.")
    
    if chat_id in spam_chats:
        return await message.reply("توجد عملية منشن جارية بالفعل، أوقفها أولاً.")
    
    spam_chats.append(chat_id)
    usrnum = 0
    usrtxt = ""
    async for usr in client.get_chat_members(chat_id):
        if not chat_id in spam_chats:
            break
        if usr.user.is_bot:
            continue
        usrnum += 1
        usrtxt += "<a href='tg://user?id={}'>{}</a>".format(usr.user.id, usr.user.first_name)

        if usrnum == 1:
            if mode == "text_on_cmd":
                txt = f"{usrtxt} {random.choice(TAGMES)}"
                await client.send_message(chat_id, txt)
            elif mode == "text_on_reply":
                await msg.reply(f"[{random.choice(EMOJI)}](tg://user?id={usr.user.id})")
            await asyncio.sleep(4)
            usrnum = 0
            usrtxt = ""
    try:
        spam_chats.remove(chat_id)
    except:
        pass


@app.on_message(filters.command(["تاك حكم", "حكم", "أقوال", "lifetag"], prefixes=["/", "@", "#", ""]))
async def mention_allvc(client, message):
    chat_id = message.chat.id
    if message.chat.type == ChatType.PRIVATE:
        return await message.reply("هذا الأمر يعمل في المجموعات فقط.")

    is_admin = False
    try:
        participant = await client.get_chat_member(chat_id, message.from_user.id)
    except UserNotParticipant:
        is_admin = False
    else:
        if participant.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        ):
            is_admin = True
    if not is_admin:
        return await message.reply("أنت لست مشرفاً، هذا الأمر للمشرفين فقط.")
    
    if chat_id in spam_chats:
        return await message.reply("توجد عملية منشن جارية بالفعل، أوقفها أولاً.")
    
    spam_chats.append(chat_id)
    usrnum = 0
    usrtxt = ""
    async for usr in client.get_chat_members(chat_id):
        if not chat_id in spam_chats:
            break
        if usr.user.is_bot:
            continue
        usrnum += 1
        usrtxt += "<a href='tg://user?id={}'>{}</a>".format(usr.user.id, usr.user.first_name)

        if usrnum == 1:
            txt = f"{usrtxt} {random.choice(VC_TAG)}"
            await client.send_message(chat_id, txt)
            await asyncio.sleep(4)
            usrnum = 0
            usrtxt = ""
    try:
        spam_chats.remove(chat_id)
    except:
        pass


@app.on_message(filters.command(["ايقاف", "بس", "الغاء", "cancel"], prefixes=["/", "@", "#", ""]))
async def cancel_spam(client, message):
    if not message.chat.id in spam_chats:
        return await message.reply("لا يوجد منشن شغال حالياً لإيقافه.")
    
    is_admin = False
    try:
        participant = await client.get_chat_member(message.chat.id, message.from_user.id)
    except UserNotParticipant:
        is_admin = False
    else:
        if participant.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        ):
            is_admin = True
    if not is_admin:
        return await message.reply("أنت لست مشرفاً لإيقاف المنشن.")
    else:
        try:
            spam_chats.remove(message.chat.id)
        except:
            pass
        return await message.reply("تم إيقاف المنشن بنجاح.")
