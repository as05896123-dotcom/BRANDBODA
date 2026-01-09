import os
import shutil
from ..logging import LOGGER

def dirr():
    # 1. تنظيف الصور من المجلد الرئيسي (باستخدام Tuple لتسريع الفحص)
    for file in os.listdir():
        if file.lower().endswith((".jpg", ".jpeg", ".png")):
            try:
                os.remove(file)
            except Exception:
                pass  # لو الملف مستخدم حالياً، تجاهله ومتقفلش البوت

    # 2. إنشاء المجلدات بأمان (exist_ok=True تمنع الأخطاء لو المجلد موجود)
    os.makedirs("downloads", exist_ok=True)
    os.makedirs("cache", exist_ok=True)

    # 3. 🔥 تنظيف "داخل" مجلدات التحميل (مهم جداً لتفريغ المساحة)
    # هذا الجزء يمنع السيرفر من الامتلاء بملفات الأغاني القديمة
    for folder in ["downloads", "cache"]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path) # حذف الملفات
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path) # حذف المجلدات الفرعية
            except Exception as e:
                # تسجيل الخطأ فقط بدون إيقاف البوت
                LOGGER(__name__).warning(f"Failed to delete {file_path}. Reason: {e}")

    LOGGER(__name__).info("Directories Updated & Cleaned Successfully.")
