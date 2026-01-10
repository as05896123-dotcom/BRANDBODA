import logging
import sys

LOG_FORMAT = "[%(asctime)s - %(levelname)s] - %(name)s - %(message)s"
DATE_FORMAT = "%d-%b-%y %H:%M:%S"

root = logging.getLogger()
root.setLevel(logging.INFO)

# امسح أي handlers قديمة (مهم جدًا)
root.handlers.clear()

# console
console = logging.StreamHandler(sys.stdout)
console.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
root.addHandler(console)

# file
file_handler = logging.FileHandler("log.txt", encoding="utf-8")
file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
root.addHandler(file_handler)

# تقليل الضوضاء
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("pymongo").setLevel(logging.ERROR)

# خلي pytgcalls warnings بس (أفضل)
logging.getLogger("pytgcalls").setLevel(logging.WARNING)
logging.getLogger("ntgcalls").setLevel(logging.WARNING)


def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
