import random
import requests
import time
import html
from deep_translator import GoogleTranslator

from pyrogram import filters
from pyrogram.enums import PollType, ChatAction
from BrandrdXMusic import app

last_command_time = {}

# كلمات ممنوعة (رقابة دينية وأدبية)
BANNED_WORDS = [
    "خمر", "نبيذ", "كحول",
    "جنس", "علاقة", "عشيق",
    "إله", "آلهة", "مسيح",
    "مقامرة", "قمار",
    "تمرد", "إباحية",
]

def is_clean(text: str) -> bool:
    """يتأكد إن النص خالي من الكلمات الممنوعة"""
    text = text.lower()
    for word in BANNED_WORDS:
        if word in text:
            return False
    return True


@app.on_message(filters.command(["quiz", "سؤال", "اختبار"], prefixes=["/", ""]))
async def quiz(client, message):
    user_id = message.from_user.id
    now = time.time()

    if user_id in last_command_time and now - last_command_time[user_id] < 5:
        return await message.reply_text(
            "مـهـلـاً يـا صـديـقـي\n"
            "انـتـظـر قـلـيـلاً قـبـل طـلـب سـؤال آخـر"
        )

    last_command_time[user_id] = now
    await app.send_chat_action(message.chat.id, ChatAction.TYPING)

    translator = GoogleTranslator(source="auto", target="ar")

    try:
        for _ in range(5):  # نحاول 5 مرات لحد ما نجيب سؤال نظيف
            categories = [9, 17, 18, 22, 23]  # ثقافة – علوم – تاريخ – جغرافيا
            url = f"https://opentdb.com/api.php?amount=1&category={random.choice(categories)}&type=multiple"
            data = requests.get(url, timeout=10).json()

            if data["response_code"] != 0:
                continue

            q = data["results"][0]

            # تنظيف النص الإنجليزي
            eng_q = html.unescape(q["question"])
            eng_correct = html.unescape(q["correct_answer"])
            eng_wrong = [html.unescape(x) for x in q["incorrect_answers"]]

            # ترجمة
            ar_q = translator.translate(eng_q)
            ar_correct = translator.translate(eng_correct)
            ar_wrong = [translator.translate(x) for x in eng_wrong]

            # رقابة
            texts = [ar_q, ar_correct] + ar_wrong
            if not all(is_clean(t) for t in texts):
                continue

            # عنوان بالكشيدة
            title = (
                "سـؤال ثـقـافـي عـام\n"
                "اخـتـبـر مـعـلـومـاتـك\n\n"
            )

            # تجهيز الإجابات
            options = ar_wrong + [ar_correct]
            random.shuffle(options)
            correct_id = options.index(ar_correct)

            return await app.send_poll(
                chat_id=message.chat.id,
                question=title + ar_q,
                options=options,
                type=PollType.QUIZ,
                is_anonymous=False,
                correct_option_id=correct_id,
            )

        await message.reply_text(
            "لـم نـجـد سـؤالاً مـنـاسـبـاً حـالـيـاً\n"
            "يـرجـى الـمـحـاولـة لاحـقـاً"
        )

    except Exception as e:
        print("Quiz Error:", e)
        await message.reply_text(
            "حـدث خـطـأ أثـنـاء جـلـب السـؤال\n"
            "حـاول مـرة أخـرى لاحـقـاً"
        )
