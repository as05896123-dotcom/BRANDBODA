from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import SUPPORT_CHAT


def song_markup(_, vidid):
    """
    Inline buttons for single song actions (audio / video)
    Compatible with Pyrogram 2.x
    """

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["SG_B_2"],
                    callback_data=f"song_helper audio|{vidid}",
                ),
                InlineKeyboardButton(
                    text=_["SG_B_3"],
                    callback_data=f"song_helper video|{vidid}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🥀 sᴜᴩᴩᴏʀᴛ 🥀",
                    url=SUPPORT_CHAT,
                ),
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"],
                    callback_data="close",
                ),
            ],
        ]
    )
