import os
import sys
import subprocess
import shutil
import compileall

def setup_library():
    LIB_NAME = "pytgcalls"
    cwd = os.getcwd()
    lib_path = os.path.join(cwd, LIB_NAME)

    # 1. تنظيف الذاكرة القديمة وحذف المكتبة المعلقة (مهم جداً للتعليق) 🧹
    print("🧹 Cleaning old cache & Removing corrupted library...")
    # بنحذف المكتبة عشان تنزل نظيفة
    if os.path.exists(lib_path):
        try:
            shutil.rmtree(lib_path)
            print("✅ Old corrupted library removed.")
        except:
            pass

    for root, dirs, files in os.walk(cwd):
        for file in files:
            if file.endswith(".pyc"):
                os.remove(os.path.join(root, file))
        for dir in dirs:
            if dir == "__pycache__":
                shutil.rmtree(os.path.join(root, dir), ignore_errors=True)

    # 2. تنزيل المكتبة من جديد (Fresh Install)
    if not os.path.exists(lib_path):
        print("⏳ Installing Fresh PyTgCalls v2.2.8...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "py-tgcalls==2.2.8", 
                "--target", cwd,
                "--no-deps",
                "--upgrade",
                "--force-reinstall"  # إجبار التنزيل النظيف
            ])
            print("✅ Install successful.")
        except Exception as e:
            print(f"❌ Install failed: {e}")
            return

    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    # 3. الإصلاح الشامل (Syntax + Anti-Crash Protection) 🛡️
    print("🔧 Applying Anti-Crash Patch...")
    file_path = os.path.join(lib_path, "mtproto", "pyrogram_client.py")
    
    if os.path.exists(file_path):
        # هنكتب الملف كله من جديد عشان نضمن إن الحماية موجودة 100%
        # الكود ده بيستبدل محتوى الملف بكود آمن تماماً
        safe_code = r'''
from pyrogram import Client
from .mtproto_client import MTProtoClient
from ...types import Update
from ...types import GroupCall
import logging

class PyrogramClient(MTProtoClient):
    def __init__(self, client: Client):
        super().__init__()
        self._client = client

        @self._client.on_message()
        async def on_message(client, message):
            if message.chat:
                await self.on_update(
                    Update(
                        chat_id=message.chat.id,
                        chat=message.chat,
                        message_id=message.id,
                        message=message,
                    )
                )

        @self._client.on_deleted_messages()
        async def on_deleted_messages(client, messages):
            for message in messages:
                if message.chat:
                    await self.on_update(
                        Update(
                            chat_id=message.chat.id,
                            chat=message.chat,
                            message_id=message.id,
                        )
                    )

    async def start(self):
        await self._client.start()

    async def stop(self):
        await self._client.stop()

    async def call(self, method, data):
        try:
            return await self._client.invoke(method, data)
        except Exception as e:
            # حماية ضد سقوط السيرفر لما الكول يفصل
            logging.error(f"[Anti-Crash] Call Error ignored: {e}")
            return None

    async def resolve_peer(self, id):
        return await self._client.resolve_peer(id)

    async def get_input_entity(self, peer):
        return await self._client.resolve_peer(peer)

    def chat_id(self, chat: GroupCall):
        return int(f"-100{chat.id}")

    async def set_params(self, chats: dict):
        self._my_id = (await self._client.get_me()).id
        self._chats = chats

    async def on_update(self, update: Update):
        chats = self._chats
        try:
            c_id = getattr(update, 'chat_id', None)
            if c_id is None and hasattr(update, 'chat'):
                 c_id = update.chat.id
            
            if c_id is None: return

            if c_id in chats:
                chat_id = self.chat_id(chats[c_id])
                await self._on_update(update, chat_id)
        except Exception:
            return
'''
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(safe_code)
            
        print("✅ Core file replaced with Protected Version.")
        print("🔄 Recompiling library...")
        compileall.compile_dir(lib_path, force=True)
        print("🚀 Ready! Please Restart.")
            
    else:
        print(f"❌ Critical: Could not find {file_path}")

if __name__ == "__main__":
    setup_library()
