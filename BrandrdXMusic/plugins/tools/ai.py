import random
import asyncio
import time
from pyrogram import filters, enums
from BrandrdXMusic import app
from g4f.client import AsyncClient

# ================== إعدادات ==================
ANTI_SPAM_SECONDS = 8
AI_TIMEOUT = 40
MAX_CONTEXT = 6   # عدد الرسائل اللي الذكاء يفتكرها
# ============================================

user_last_message = {}
user_context = {}

# --- دالة الإيموجي ---
def get_emoji():
    if random.randint(1, 3) == 1:
        return f" {random.choice(['🤍', '🧚', '⚡'])}"
    return ""

# --- معالج الأوامر ---
@app.on_message(filters.command(["gpt", "ai", "ask", "شات", "ذكاء"]))
async def smart_ai(client, message):
    try:
        user_id = message.from_user.id
        now = time.time()

        # ---- Anti Spam ----
        if user_id in user_last_message:
            if now - user_last_message[user_id] < ANTI_SPAM_SECONDS:
                return
        user_last_message[user_id] = now

        # ---- تحقق من السؤال ----
        if len(message.command) < 2:
            await message.reply_text("**اكتب سؤالك بجانب الامر..** 🤍", quote=True)
            return

        query = message.text.split(None, 1)[1].strip()
        if not query:
            await message.reply_text("**اكتب سؤالك بجانب الامر..** 🤍", quote=True)
            return

        # ---- حفظ السياق ----
        if user_id not in user_context:
            user_context[user_id] = []

        user_context[user_id].append({"role": "user", "content": query})

        # الحفاظ على عدد رسائل محدود
        user_context[user_id] = user_context[user_id][-MAX_CONTEXT:]

        # ---- جاري الكتابة ----
        await client.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
        wait_msg = await message.reply_text("**جاري التفكير...**", quote=True)

        ai_client = AsyncClient()

        async def ask_ai():
            try:
                return await ai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "أنت مساعد ذكي. افهم لغة المستخدم تلقائيًا "
                                "ورد بنفس لغته. احترم سياق الحوار السابق "
                                "واجعل الردود مختصرة ومفيدة."
                            ),
                        },
                        *user_context[user_id],
                    ],
                )
            except:
                return await ai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=user_context[user_id],
                )

        try:
            response = await asyncio.wait_for(ask_ai(), timeout=AI_TIMEOUT)
            final_response = response.choices[0].message.content
        except asyncio.TimeoutError:
            await wait_msg.edit("الخوادم مشغولة الان، جرب مرة أخرى لاحقاً.")
            return

        if final_response:
            clean = final_response.strip()
            user_context[user_id].append(
                {"role": "assistant", "content": clean}
            )
            user_context[user_id] = user_context[user_id][-MAX_CONTEXT:]

            await wait_msg.edit(
                f"**{clean}**{get_emoji()}",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await wait_msg.edit("حدث خطأ، لم يتم استلام رد.")

    except Exception as e:
        print(f"AI Error: {e}")
        try:
            await wait_msg.edit("الخوادم مشغولة الان، جرب مرة أخرى لاحقاً.")
        except:
            pass
