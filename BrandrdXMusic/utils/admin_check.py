from pyrogram.types import Message
from pyrogram.enums import ChatType, ChatMemberStatus

async def admin_check(message: Message) -> bool:
    # 1. التعامل مع المشرف المتخفي (Anonymous Admin)
    # لو الرسالة جاية من غير مستخدم، بس جاية من "نفس الشات"، يبقى ده مشرف متخفي
    if not message.from_user:
        if message.sender_chat and message.sender_chat.id == message.chat.id:
            return True
        return False

    # 2. إضافة دعم الجروبات العادية (GROUP) بجانب السوبر جروب
    if message.chat.type not in [ChatType.SUPERGROUP, ChatType.CHANNEL, ChatType.GROUP]:
        return False

    # 3. التحقق من المستخدمين العاديين
    client = message._client
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        check_status = await client.get_chat_member(chat_id=chat_id, user_id=user_id)
        if check_status.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
            return True
        else:
            return False
    except:
        # لو حصل أي خطأ في جلب العضو (مثلاً غادر)، نعتبره مش أدمن
        return False
