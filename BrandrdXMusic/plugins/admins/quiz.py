import random
import requests
import time
import html
from deep_translator import GoogleTranslator

from pyrogram import filters
from pyrogram.enums import PollType, ChatAction
from BrandrdXMusic import app

last_command_time = {}

@app.on_message(filters.command(["quiz", "سؤال", "اختبار"]))
async def quiz(client, message):
    user_id = message.from_user.id
    current_time = time.time()

    if user_id in last_command_time and current_time - last_command_time[user_id] < 5:
        await message.reply_text("يرجى الانتظار قليلاً قبل طلب سؤال آخر.")
        return

    last_command_time[user_id] = current_time

    await app.send_chat_action(message.chat.id, ChatAction.TYPING)

    try:
        # جلب السؤال من الموقع
        categories = [9, 17, 18, 22, 23]
        url = f"https://opentdb.com/api.php?amount=1&category={random.choice(categories)}&type=multiple"
        response = requests.get(url).json()

        if response["response_code"] != 0:
            return await message.reply_text("حدث خطأ في جلب السؤال.")

        question_data = response["results"][0]

        # تنظيف النصوص الإنجليزية
        eng_question = html.unescape(question_data["question"])
        eng_correct = html.unescape(question_data["correct_answer"])
        eng_incorrect = [html.unescape(ans) for ans in question_data["incorrect_answers"]]

        # الترجمة للعربية
        translator = GoogleTranslator(source='auto', target='ar')
        
        ar_question = translator.translate(eng_question)
        ar_correct = translator.translate(eng_correct)
        ar_incorrect = [translator.translate(ans) for ans in eng_incorrect]

        # تجهيز الإجابات وخلطها
        all_answers = ar_incorrect + [ar_correct]
        random.shuffle(all_answers)

        cid = all_answers.index(ar_correct)
        
        # إرسال الاستطلاع (بدون parameter explanation)
        await app.send_poll(
            chat_id=message.chat.id,
            question=ar_question,
            options=all_answers,
            is_anonymous=False,
            type=PollType.QUIZ,
            correct_option_id=cid
        )

    except Exception as e:
        print(f"Quiz Error: {e}")
        await message.reply_text("حدث خطأ أثناء جلب السؤال.")
