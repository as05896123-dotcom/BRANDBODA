import asyncio
import os

# ---------------------------------------------------
# 🔥 1. هنا السر: تفعيل التيربو قبل ما البوت يصحى
# ---------------------------------------------------
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    print("✅ UVLOOP Started Successfully!")
except ImportError:
    print("⚠️ UVLOOP not found, using default asyncio.")
# ---------------------------------------------------

# بعد ما جهزنا التيربو، دلوقتي نستدعي البوت بأمان
from BrandrdXMusic.__main__ import init

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init())
