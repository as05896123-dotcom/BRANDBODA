# core/pytgcalls_patch.py
# ==============================================================================
# 🛡️ THE IRONCLAD HEALER PATCH (نص الملعب الحديد)
# 1. Injects missing attributes (Correction).
# 2. Wraps critical methods to swallow errors (Protection).
# 3. Auto-heals broken updates (Recovery).
# ==============================================================================

import logging
import sys
import asyncio

# إعداد لوجر خاص للباتش عشان نعرف هو شغال ولا لا
PATCH_LOGGER = logging.getLogger("PatchGuard")

def apply_ironclad_patch():
    try:
        # ------------------------------------------------------------------
        # 🟢 LAYER 1: THE INJECTOR (تصحيح الكلاسات المكسورة)
        # ------------------------------------------------------------------
        from pytgcalls.types import UpdateGroupCall, GroupCallConfig

        # 1. إصلاح UpdateGroupCall (المشكلة الرئيسية)
        if not hasattr(UpdateGroupCall, "chat_id"):
            @property
            def chat_id_healer(self):
                try:
                    # محاولة ذكية لاستخراج ID
                    if hasattr(self, "chat") and self.chat:
                        return self.chat.id
                    # لو مفيش chat، نحاول نجيبه من الـ internal dict لو متاح
                    if hasattr(self, "__dict__"):
                        return self.__dict__.get("chat_id", 0)
                    return 0
                except:
                    return 0

            UpdateGroupCall.chat_id = chat_id_healer
            PATCH_LOGGER.info("✅ [Layer 1] UpdateGroupCall.chat_id injected.")

        # ------------------------------------------------------------------
        # 🟡 LAYER 2: THE DEFENDER (تغليف استقبال التحديثات)
        # ------------------------------------------------------------------
        from pytgcalls.mtproto import pyrogram_client as _pc
        
        PyrogramClient = getattr(_pc, "PyrogramClient", None)
        
        if PyrogramClient and hasattr(PyrogramClient, "on_update"):
            original_on_update = PyrogramClient.on_update

            async def safe_on_update(self, update):
                try:
                    # 1. فحص مبدئي: لو التحديث فاضي، ارميه
                    if not update:
                        return
                    
                    # 2. فحص الشفاء: هل التحديث ده تبعنا ومكسور؟
                    if isinstance(update, UpdateGroupCall):
                        # تأكد إن chat_id موجود، ولو مش موجود، الديكوريتور اللي فوق هيعالجه
                        # بس زيادة أمان، هنتأكد هنا كمان
                        try:
                            _ = update.chat_id
                        except:
                            # لو فشل الاستدعاء، نلغي التحديث ده تماماً لأنه فاسد
                            return

                    # 3. تمرير التحديث للدالة الأصلية بسلام
                    if original_on_update:
                        await original_on_update(self, update)

                except AttributeError:
                    # تجاهل أخطاء الخصائص المفقودة (ده هدفنا أصلاً)
                    pass
                except Exception as e:
                    # لو خطأ غير متوقع، سجله بس متوقفش البوت
                    error_msg = str(e)
                    if "chat_id" not in error_msg: # تجاهل رسائل chat_id المزعجة
                        PATCH_LOGGER.warning(f"⚠️ [Layer 2] Swallowed Error: {e}")

            # استبدال الدالة الأصلية بالدالة المحمية
            PyrogramClient.on_update = safe_on_update
            PATCH_LOGGER.info("✅ [Layer 2] PyrogramClient.on_update secured.")

    except ImportError:
        PATCH_LOGGER.error("❌ Failed to import pytgcalls modules. Is it installed?")
    except Exception as e:
        PATCH_LOGGER.error(f"❌ Patch failed to apply: {e}")

# تنفيذ الحقنة فوراً عند استدعاء الملف
apply_ironclad_patch()
