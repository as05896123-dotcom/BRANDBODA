# BrandrdXMusic/plugins/tools/healer.py
# ==============================================================================
# 🚑 HEALER TOOL: أداة العلاج الذكي
# المكان: plugins/tools/healer.py
# الوظيفة: إصلاح خطأ chat_id في pytgcalls تلقائياً
# ==============================================================================

import sys

def apply_cure():
    try:
        # 1. استدعاء المكتبة
        from pytgcalls.types import UpdateGroupCall
        
        # 2. الكشف عن المشكلة
        if not hasattr(UpdateGroupCall, "chat_id"):
            
            # 3. تجهيز العلاج (getter ذكي)
            def _healed_chat_id(self):
                # بيحاول يجيب الـ ID من self.chat
                # لو مش موجود بيرجع 0 بدل ما يعمل كراش
                return getattr(getattr(self, "chat", None), "id", 0)
            
            # 4. حقن العلاج
            UpdateGroupCall.chat_id = property(_healed_chat_id)
            
            print("✅ [TOOLS] Healer applied: 'UpdateGroupCall' is now safe.")
            
    except ImportError:
        # لو المكتبة لسه متحملتش، مش مشكلة
        pass
    except Exception as e:
        print(f"⚠️ [TOOLS] Healer Error: {e}")

# تنفيذ العلاج فوراً
apply_cure()
