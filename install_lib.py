import os
import sys
import subprocess
import shutil
import compileall

def setup_library():
    LIB_NAME = "pytgcalls"
    cwd = os.getcwd()
    lib_path = os.path.join(cwd, LIB_NAME)

    # 1. تنظيف الذاكرة القديمة (أهم خطوة دلوقتي) 🧹
    print("🧹 Nuking old cache files...")
    for root, dirs, files in os.walk(cwd):
        for file in files:
            if file.endswith(".pyc"):
                os.remove(os.path.join(root, file))
        for dir in dirs:
            if dir == "__pycache__":
                shutil.rmtree(os.path.join(root, dir), ignore_errors=True)

    # 2. تنزيل المكتبة لو مش موجودة
    if not os.path.exists(lib_path):
        print("⏳ Installing PyTgCalls v2.2.8...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "py-tgcalls==2.2.8", 
                "--target", cwd,
                "--no-deps",
                "--upgrade"
            ])
            print("✅ Install successful.")
        except Exception as e:
            print(f"❌ Install failed: {e}")
            return

    # 3. التأكد من المسار
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    # 4. الإصلاح (Fix chat_id error)
    print("🔧 Applying Fix...")
    file_path = os.path.join(lib_path, "mtproto", "pyrogram_client.py")
    
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            code = f.read()
        
        # التعديل
        old = "chat_id = self.chat_id(chats[update.chat_id])"
        new = "chat_id = self.chat_id(chats[update.chat.id])"
        
        if old in code:
            code = code.replace(old, new)
            with open(file_path, "w") as f:
                f.write(code)
            print("✅ CODE FIXED: chat_id replaced with chat.id")
        
        # 5. إعادة بناء الذاكرة على نضيف
        print("🔄 Recompiling library...")
        compileall.compile_dir(lib_path, force=True)
        print("✅ Ready to launch.")

    else:
        print(f"❌ Critical: Could not find {file_path}")

if __name__ == "__main__":
    setup_library()
