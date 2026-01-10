# core/pytgcalls_patch.py
# This patch injects the missing 'chat_id' property directly into the UpdateGroupCall class.
# It is much more robust than trying to wrap the on_update method.

import sys

try:
    # محاولة استيراد الكلاس المسبب للمشكلة
    from pytgcalls.types import UpdateGroupCall
    
    # التأكد هل الخاصية ناقصة فعلاً؟
    if not hasattr(UpdateGroupCall, "chat_id"):
        
        # إنشاء الخاصية المفقودة
        @property
        def chat_id(self):
            # محاولة جلب الـ ID من كائن chat الداخلي
            return getattr(getattr(self, "chat", None), "id", 0)
        
        # حقن الخاصية داخل الكلاس
        UpdateGroupCall.chat_id = chat_id
        print("✅ FORCE PATCH APPLIED: UpdateGroupCall.chat_id injected successfully.")
        
    else:
        print("ℹ️ Patch skipped: UpdateGroupCall already has chat_id.")

except ImportError:
    # لو المكتبة لسه مش محملة، بنحاول نجيبها من sys.modules
    pass
except Exception as e:
    print(f"⚠️ Patch Error: {e}")
