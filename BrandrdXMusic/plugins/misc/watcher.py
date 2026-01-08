from pyrogram import filters
from pyrogram.types import Message

from BrandrdXMusic import app
from BrandrdXMusic.core.call import Hotty

welcome = 20
close = 30

@app.on_message(filters.video_chat_started, group=welcome)
@app.on_message(filters.video_chat_ended, group=close)
async def welcome(_, message: Message):
    try:
        # بيحاول يوقف التشغيل القديم لو موجود
        await Hotty.stop_stream_force(message.chat.id)
    except AttributeError:
        # لو الدالة مش موجودة، كمل عادي ومتقفش
        pass
    except Exception:
        pass
