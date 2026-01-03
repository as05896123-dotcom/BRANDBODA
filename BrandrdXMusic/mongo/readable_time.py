def get_readable_time(seconds: int) -> str:
    count = 0
    time_list = []

    # تسميات الوقت بالكشيدة (مطوّلة)
    time_units_singular = {
        "second": "ثـانـيـة",
        "minute": "دقـيـقـة",
        "hour": "سـاعـة",
        "day": "يـوم",
    }

    time_units_plural = {
        "second": "ثـوانـي",
        "minute": "دقـائـق",
        "hour": "سـاعـات",
        "day": "أيـام",
    }

    units_order = ["second", "minute", "hour", "day"]

    while count < 4:
        count += 1

        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)

        if seconds == 0 and remainder == 0:
            break

        time_list.append(int(result))
        seconds = int(remainder)

    readable_parts = []

    for index, value in enumerate(time_list):
        if value == 0:
            continue

        unit_key = units_order[index]

        if value == 1:
            unit_name = time_units_singular[unit_key]
        else:
            unit_name = time_units_plural[unit_key]

        readable_parts.append(f"{value} {unit_name}")

    readable_parts.reverse()

    if not readable_parts:
        return "0 ثـانـيـة"

    # إخراج مطوّل بالكشيدة
    return " و ".join(readable_parts)
