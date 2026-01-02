import random
import asyncio
from pyrogram import filters, enums
from BrandrdXMusic import app
from g4f.client import AsyncClient

# --- دالة الإيموجي (سبتها عشان تدي شكل جمالي بسيط في الآخر) ---
def get_emoji():
    if random.randint(1, 3) == 1:
        return f" {random.choice(['🤍', '🧚', '⚡'])}"
    return ""

# --- معالج الأوامر ---
@app.on_message(filters.command(["gpt", "ai", "ask", "سؤال", "ذكاء"]))
async def smart_ai(client, message):
    try:
        # التحقق من وجود السؤال
        if len(message.command) < 2:
            await message.reply_text("**اكتب سؤالك بجانب الامر..** 🤍", quote=True)
            return

        query = message.text.split(None, 1)[1]
        
        # إرسال أكشن "جاري الكتابة"
        await client.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
        wait_msg = await message.reply_text("**جاري التفكير...**", quote=True)

        # تعريف العميل الجديد (للتوافق مع آخر تحديث)
        ai_client = AsyncClient()
        
        try:
            # المحاولة الأولى: موديل GPT-4
            response = await ai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "أنت مساعد ذكي، ردودك مختصرة ومفيدة."},
                    {"role": "user", "content": query}
                ],
            )
            final_response = response.choices[0].message.content

        except Exception:
            # المحاولة الاحتياطية: موديل GPT-3.5 (أسرع وأخف)
            response = await ai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": query}],
            )
            final_response = response.choices[0].message.content

        # تنسيق الرد وإرساله
        if final_response:
            clean_reply = final_response.strip()
            emoji = get_emoji()
            
            await wait_msg.edit(
                f"**{clean_reply}**{emoji}",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await wait_msg.edit("حدث خطأ، لم يتم استلام رد.")

    except Exception as e:
        print(f"AI Error: {e}")
        await wait_msg.edit("الخوادم مشغولة الان، جرب مرة أخرى لاحقاً.")
