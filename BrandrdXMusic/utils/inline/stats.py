from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def stats_buttons(_, is_sudo: bool):
    """
    Stats main buttons
    - is_sudo = True  → show sudo stats buttons
    - is_sudo = False → show normal user stats buttons
    """

    user_buttons = [
        InlineKeyboardButton(
            text=_["SA_B_1"],
            callback_data="TopOverall",
        )
    ]

    sudo_buttons = [
        InlineKeyboardButton(
            text=_["SA_B_2"],
            callback_data="bot_stats_sudo",
        ),
        InlineKeyboardButton(
            text=_["SA_B_3"],
            callback_data="TopOverall",
        ),
    ]

    return InlineKeyboardMarkup(
        [
            sudo_buttons if is_sudo else user_buttons,
            [
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"],
                    callback_data="close",
                ),
            ],
        ]
    )


def back_stats_buttons(_):
    """
    Back button for stats panels
    """
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data="stats_back",
                ),
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"],
                    callback_data="close",
                ),
            ],
        ]
    )
