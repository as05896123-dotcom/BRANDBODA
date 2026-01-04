import logging
import sys
from pyrogram import Client, filters

# ==========================
# إعدادات أساسية للـ Logging
# ==========================
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        logging.FileHandler("log.txt"),
        logging.StreamHandler(),
    ],
)

# تجاهل الرسائل الكثيرة من المكتبات الثانوية
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("pytgcalls").setLevel(logging.ERROR)
logging.getLogger("pymongo").setLevel(logging.ERROR)
logging.getLogger("ntgcalls").setLevel(logging.ERROR)

# دالة سهلة لإنشاء Logger جديد
def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)

# ==========================
# التقاط أي أخطاء غير متوقعة (Unhandled Exceptions)
# ==========================
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    log = LOGGER("Global")
    log.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

# ==========================
# مراقبة كل رسائل البوت
# ==========================
def monitor_bot(client: Client):
    """
    هذه الدالة تضيف مراقبة شاملة لأي رسالة أو أمر لم يتم التعامل معه
    """
    log = LOGGER("BotMonitor")

    @client.on_message(filters.all)
    async def monitor_all(client, message):
        try:
            # إذا كانت الرسالة غير معالجة في أي مكان
            handled = getattr(message, "handled", False)
            if not handled:
                user = getattr(message.from_user, "id", "Unknown")
                text = getattr(message, "text", str(message))
                log.warning(f"Unhandled message from {user}: {text}")
        except Exception as e:
            log.error(f"Error in monitoring message: {e}")
