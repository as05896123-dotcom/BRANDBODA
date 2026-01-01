import asyncio

from BrandrdXMusic.misc import db
from BrandrdXMusic.utils.database import get_active_chats, is_music_playing


async def timer():
    while not await asyncio.sleep(1):
        try:
            active_chats = await get_active_chats()
            for chat_id in active_chats:
                try:
                    if not await is_music_playing(chat_id):
                        continue
                    playing = db.get(chat_id)
                    if not playing:
                        continue
                    file_path = playing[0]["file"]
                    if "index_" in file_path or "live_" in file_path:
                        continue
                    duration = int(playing[0]["seconds"])
                    if duration == 0:
                        continue
                    if db[chat_id][0]["played"] >= duration:
                        continue
                    db[chat_id][0]["played"] += 1
                except:
                    continue
        except:
            continue


asyncio.create_task(timer())
