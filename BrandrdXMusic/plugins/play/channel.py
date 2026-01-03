from pyrogram import filters
from pyrogram.enums import ChatMembersFilter, ChatMemberStatus, ChatType
from pyrogram.types import Message

from BrandrdXMusic import app
from BrandrdXMusic.core.database import set_cmode
from BrandrdXMusic.utils.decorators.admins import AdminActual
from config import BANNED_USERS


@app.on_message(
    filters.command(
        ["channelplay", "ربط القناة", "تشغيل القناة", "ربط قناة"],
        prefixes=["/", "!", ".", ""]
    )
    & filters.group
    & ~BANNED_USERS
)
@AdminActual
async def playmode_(client, message: Message, _):
    # التحقق مما إذا كان المستخدم مشرف مخفي
    if message.sender_chat and message.sender_chat.id == message.chat.id:
        return await message.reply_text(
            "**عــذراً، لا يــمــكــنــك ربــط الــقــنــاة وأنــت بــوضــع الــتــخــفــي ( مــشــرف مــخــفــي ).**\n"
            "يــرجــى الــدخــول بــحــســابــك الــشــخــصــي لــإثــبــات مــلــكــيــة الــقــنــاة."
        )

    if len(message.command) < 2:
        return await message.reply_text(
            "<b>طــريــقــة الاســتــخــدام :</b>\n"
            "ربــط قــنــاة [ مــعــرف الــقــنــاة / مــرتــبــطــة / تــعــطــيــل ]\n\n"
            "<b>مــثــال :</b>\nربــط قــنــاة @ChannelName"
        )
    
    query = message.text.split(None, 2)[1].lower().strip()
    
    # خيار التعطيل
    if query in ["disable", "تعطيل"]:
        await set_cmode(message.chat.id, None)
        return await message.reply_text(
            "تــم تــعــطــيــل وضــع تــشــغــيــل الــقــنــاة، ســيــتــم الــتــشــغــيــل فــي الــمــجــمــوعــة الآن."
        )
    
    # خيار القناة المرتبطة تلقائياً
    elif query in ["linked", "مرتبطة"]:
        chat = await app.get_chat(message.chat.id)
        if chat.linked_chat:
            chat_id = chat.linked_chat.id
            await set_cmode(message.chat.id, chat_id)
            return await message.reply_text(
                f"تــم ربــط الــتــشــغــيــل بــالــقــنــاة الــمــرتــبــطــة : {chat.linked_chat.title}\n"
                f"الــمــعــرف : {chat.linked_chat.id}"
            )
        else:
            return await message.reply_text(
                "هــذه الــمــجــمــوعــة لا تــمــتــلــك قــنــاة مــرتــبــطــة بــهــا فــي إعــدادات تــيــلــيــجــرام."
            )
    
    # خيار ربط قناة محددة
    else:
        try:
            chat = await app.get_chat(query)
        except Exception:
            return await message.reply_text(
                "لــم أســتــطــع الــعــثــور عــلــى الــقــنــاة، تــأكــد مــن الــمــعــرف أو أن الــبــوت مــشــرف فــيــهــا."
            )
        
        if chat.type != ChatType.CHANNEL:
            return await message.reply_text("هــذا الــمــعــرف لا يــنــتــمــي لــقــنــاة.")
        
        crid = None
        cusn = None
        
        try:
            async for user in app.get_chat_members(
                chat.id, filter=ChatMembersFilter.ADMINISTRATORS
            ):
                if user.status == ChatMemberStatus.OWNER and user.user:
                    cusn = user.user.username
                    crid = user.user.id
                    break
        except Exception as e:
            return await message.reply_text(
                "حــدث خــطــأ، تــأكــد أنــنــي مــشــرف فــي الــقــنــاة ولــدي صــلاحــيــة رؤيــة الــمــشــرفــيــن.\n"
                f"الــخــطــأ : {e}"
            )
        
        if crid is None:
            return await message.reply_text("لــم أتــمــكــن مــن تــحــديــد مــالــك الــقــنــاة.")

        if crid != message.from_user.id:
            return await message.reply_text(
                f"عــذراً، يــجــب أن تــكــون مــالــك الــقــنــاة لــربــطــهــا.\n"
                f"الــمــالــك هــو : @{cusn}"
            )
        
        await set_cmode(message.chat.id, chat.id)
        return await message.reply_text(
            f"تــم ربــط الــتــشــغــيــل بــالــقــنــاة : {chat.title}\n"
            f"الــمــعــرف : {chat.id}"
        )
