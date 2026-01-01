from BrandrdXMusic import app 
import asyncio
import random
from pyrogram import Client, filters
from pyrogram.enums import ChatType, ChatMemberStatus
from pyrogram.errors import UserNotParticipant

spam_chats = []

# إيموجي متنوع يناسب الحزن والفرح
EMOJI = [ "🦋", "🌸", "🎻", "🎼", "🌹", "✨", "🕯️", "💌", "🍂", "🤍", "🌙", "🦉", "📜", "💔", "🥀" ]

SHAYRI = [
    # --- غزل وحب ---
    "أغركِ مني أن حبكِ قاتلي... وأنكِ مهما تأمري القلب يفعلِ.",
    "وإني أحبكِ بقلب طاهر بكلمات تعلو لـ رب الأكوان أن تبقي لي وحدي.",
    "عيناكِ رواية.. وأنا أهوى القراءة.",
    "سبحان من زرعكِ في قلبي كأنكِ جزء مني.",
    "يا ليتنا جيران، والباب يطرق الباب، ولما أشوفك أقول يا محلا دقة الباب.",
    "أنتِ قهوتي، وقصيدتي، وأغنيتي، وأجمل تفاصيلي.",
    "لو كان لي ألف قلب.. لأحببتك بألف طريقة.",
    "كل ما أريده هو أن تبقى معي، ليس عاماً أو عامين، بل عمراً.",
    "ضحكتكِ.. تختصر كل معاني السعادة في قلبي.",
    "أحببتك لدرجة أنني حين أرى ملامحك أنسى آلامي.",
    "يا أجمل صدفة في عمري.. يا نعمة من سابع سماء.",
    
    # --- حزن وفراق ---
    "سيء جداً أن تحمل هموماً ليست مناسبة لسنك، في وقت المفروض أنك في أجمل أيام حياتك.",
    "أصعب شعور.. أن تمثل الراحة وقلبك يملؤه الضجيج.",
    "نحن ضحايا التفاصيل الصغيرة، تقتلنا ببطء.",
    "لا تلوم الريح إذا كان بابك مفتوحاً.. ولا تلوم القلب إذا وثق بمن لا يستحق.",
    "مؤلم أن تشتاق لشخص.. لا يمكنك محادثته.",
    "الهدوء الذي يظهره وجهي.. لا يعكس أبداً الضجيج الذي في داخلي.",
    "أحياناً نرحل ليس حباً في الرحيل.. بل لأنه لا فائدة من البقاء.",
    "أكثر الأشياء وجعاً.. هو أن تنام كل ليلة وفي صدرك كلام لم يقل.",
    "شكراً للأيام التي علمتنا أن لا نتوقع شيئاً من أحد.",
    "لست بخير.. ولكني أجيد التمثيل.",
    
    # --- عتاب وشوق ---
    "عاتبتهم حتى مللت عتابهم.. وتركتهم للزمن يخبرهم كم كنت أحبهم.",
    "الاهتمام لا يطلب.. فإن طلب قلّت قيمته.",
    "أشتاق إليك بطريقة هادئة جداً.. لا يشعر بها أحد غيري.",
    "ليت الذكريات ترحل.. كما يرحل أصحابها.",
    "غريبة هذه الحياة.. قد تمتلك كل شيء، إلا ما تريده.",
    
    # --- خواطر قصيرة ---
    "كن وحيداً، ولا تكن بديلاً.",
    "القلوب الحساسة لا تجد منافذ للبوح، فتكتفي بالصمت.",
    "ما زلنا نتعلم كل يوم أن ليس كل ما يلمع ذهباً.",
    "اللهم راحة لقلب لا يعلم بحاله إلا أنت."
]


@app.on_message(filters.command(["shayari", "شعر", "قصيد", "بوح"], prefixes=["/", "@", "#"]))
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
        return await message.reply("أنت لست مشرفاً يا عزيزي، هذا الأمر للمشرفين فقط.")

    # التحقق من المدخلات للبدء
    if message.reply_to_message and message.text:
        return await message.reply("اكتب (شعر) أو (قصيد) للبدء.")
    elif message.text:
        mode = "text_on_cmd"
        msg = message.text
    elif message.reply_to_message:
        mode = "text_on_reply"
        msg = message.reply_to_message
        if not msg:
            return await message.reply("اكتب (شعر) أو (قصيد) للبدء.")
    else:
        return await message.reply("اكتب (شعر) أو (قصيد) للبدء.")
    
    if chat_id in spam_chats:
        return await message.reply("توجد عملية شعر شغالة حالياً، انتظر أو أوقفها أولاً.")
    
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
                # يرسل المنشن مع بيت شعر عشوائي
                txt = f"{usrtxt}\n\n**{random.choice(SHAYRI)}**"
                await client.send_message(chat_id, txt)
            elif mode == "text_on_reply":
                await msg.reply(f"[{random.choice(EMOJI)}](tg://user?id={usr.user.id})")
            
            await asyncio.sleep(4) # وقت الانتظار بين كل منشن
            usrnum = 0
            usrtxt = ""
            
    try:
        spam_chats.remove(chat_id)
    except:
        pass


@app.on_message(filters.command(["cancelshayari", "shayarioff", "بس شعر", "ايقاف شعر"]))
async def cancel_spam(client, message):
    if not message.chat.id in spam_chats:
        return await message.reply("لا يوجد شعر شغال حالياً لإيقافه.")
    
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
        return await message.reply("أنت لست مشرفاً لإيقاف الأمر.")
    else:
        try:
            spam_chats.remove(message.chat.id)
        except:
            pass
        return await message.reply("تم إيقاف الشعر والقصيد بنجاح 🎻")

