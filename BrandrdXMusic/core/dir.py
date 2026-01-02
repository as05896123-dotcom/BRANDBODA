import os

from ..logging import LOGGER


def dirr():
    # حذف الصور المؤقتة من المجلد الرئيسي
    for file in os.listdir():
        if file.endswith(".jpg"):
            os.remove(file)
        elif file.endswith(".jpeg"):
            os.remove(file)
        elif file.endswith(".png"):
            os.remove(file)

    # إنشاء المجلدات الضرورية إذا لم تكن موجودة
    os.makedirs("downloads", exist_ok=True)
    os.makedirs("cache", exist_ok=True)

    LOGGER(__name__).info("تم تحديث المجلدات بنجاح.")
