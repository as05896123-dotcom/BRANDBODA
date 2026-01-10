import os
import sys
import subprocess
import shutil
import compileall
import re

def setup_library():
    LIB_NAME = "pytgcalls"
    cwd = os.getcwd()
    lib_path = os.path.join(cwd, LIB_NAME)

    # 1. تنظيف الذاكرة القديمة (Cache Nuke) 🧹
    print("🧹 Cleaning old cache...")
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

    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    # 3. الإصلاح الذكي (Smart Patch) 🧠
    print("🔧 Applying Smart Fix...")
    file_path = os.path.join(lib_path, "mtproto", "pyrogram_client.py")
    
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            lines = f.readlines()
        
        new_lines = []
        fixed = False
        
        for line in lines:
            # بندور على السطر اللي بيعمل المشكلة (سواء القديم أو اللي حاولنا نصلحه)
            if "chat_id = self.chat_id(chats[update.chat_id])" in line or \
               "chat_id = self.chat_id(chats[update.chat.id])" in line:
                
                # بنحسب المسافة البادئة (Indentation) عشان الكود ميبوظش
                indent = line[:line.find("chat_id")]
                
                # ده الكود البديل: بيجرب كله، ولو فشل بيعمل continue
                patch_block = (
                    f"{indent}try:\n"
                    f"{indent}    c_id = getattr(update, 'chat_id', getattr(getattr(update, 'chat', None), 'id', None))\n"
                    f"{indent}    if c_id is None: continue\n"
                    f"{indent}    chat_id = self.chat_id(chats[c_id])\n"
                    f"{indent}except (AttributeError, KeyError):\n"
                    f"{indent}    continue\n"
                )
                new_lines.append(patch_block)
                fixed = True
                print("✅ Found and replaced crashing line with SAFE BLOCK.")
            else:
                new_lines.append(line)
        
        if fixed:
            with open(file_path, "w") as f:
                f.writelines(new_lines)
            
            # إعادة بناء الذاكرة
            print("🔄 Recompiling library...")
            compileall.compile_dir(lib_path, force=True)
            print("✅ Fix Applied & Compiled.")
        else:
            print("⚠️ Code already patched or line not found.")
            
    else:
        print(f"❌ Critical: Could not find {file_path}")

if __name__ == "__main__":
    setup_library()
