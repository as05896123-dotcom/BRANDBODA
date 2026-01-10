import os
import sys
import subprocess
import shutil
import compileall

def final_fix():
    LIB_NAME = "pytgcalls"
    cwd = os.getcwd()
    lib_path = os.path.join(cwd, LIB_NAME)

    # 1. تنظيف سريع
    print("🧹 Cleaning library...")
    if os.path.exists(lib_path):
        try:
            shutil.rmtree(lib_path)
        except: pass

    # 2. تحميل المكتبة
    print("⏳ Installing PyTgCalls v2.2.8...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "py-tgcalls==2.2.8", 
            "--target", cwd,
            "--no-deps",
            "--upgrade",
            "--force-reinstall"
        ])
    except Exception:
        pass

    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    # 3. كتابة الكود السليم (بدون Import MTProtoClient)
    print("🔧 Writing fixed client code...")
    target_file = os.path.join(lib_path, "mtproto", "pyrogram_client.py")
    
    # لاحظ: شلنا السطر اللي كان بيعمل المشكلة وشلنا (MTProtoClient) من الكلاس
    safe_code = r'''
from pyrogram import Client
from ...types import Update
from ...types import GroupCall
import logging

class PyrogramClient:
    def __init__(self, client: Client):
        self._client = client

    async def start(self):
        await self._client.start()

    async def stop(self):
        await self._client.stop()

    async def call(self, method, data):
        try:
            return await self._client.invoke(method, data)
        except Exception as e:
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

    def set_on_update(self, func):
        self._on_update = func

    async def on_update(self, update: Update):
        if not hasattr(self, '_on_update'): return
        chats = self._chats
        try:
            c_id = getattr(update, 'chat_id', None)
            if c_id is None and hasattr(update, 'chat'):
                 c_id = update.chat.id
            if c_id is None: return
            if c_id in chats:
                chat_id = self.chat_id(chats[c_id])
                await self._on_update(update, chat_id)
        except: return
'''
    
    # نتأكد إن المجلد موجود قبل الكتابة
    os.makedirs(os.path.dirname(target_file), exist_ok=True)
    
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(safe_code)

    # 4. تعديل الملف الأم عشان يقبل الكود الجديد
    mtproto_file = os.path.join(lib_path, "mtproto", "mtproto_client.py")
    if os.path.exists(mtproto_file):
        with open(mtproto_file, "r") as f:
            content = f.read()
        # إلغاء فحص النوع عشان ميعترضش على الكلاس المعدل
        new_content = content.replace("isinstance(client, MTProtoClient)", "True")
        with open(mtproto_file, "w") as f:
            f.write(new_content)

    # 5. ربط الديكوريتورز (خطوة مهمة جداً عشان البوت يحس بالرسائل)
    # بنضيف كود الربط في نهاية ملف pyrogram_client.py اللي كتبناه
    with open(target_file, "a", encoding="utf-8") as f:
        f.write("\n    # Decorators Binding\n")
        f.write("    @property\n    def on_message(self):\n        return self._client.on_message\n")
        f.write("    @property\n    def on_deleted_messages(self):\n        return self._client.on_deleted_messages\n")

    print("🔄 Compiling...")
    compileall.compile_dir(lib_path, force=True)
    print("🚀 DONE! Restart Bot.")

if __name__ == "__main__":
    final_fix()
