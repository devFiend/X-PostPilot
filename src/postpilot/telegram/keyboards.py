"""
Inline keyboard generators for Telegram Bot.
"""

import urllib.parse
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_draft_keyboard(draft_id: int, content: str = "") -> InlineKeyboardMarkup:
    """
    Buttons for managing a generated draft.
    Includes direct 1-tap 'Open in X Composer' URL button that launches the X app with text prefilled.
    """
    encoded_text = urllib.parse.quote(content)
    composer_url = f"https://twitter.com/intent/tweet?text={encoded_text}"

    keyboard = [
        [
            InlineKeyboardButton("🚀 Post to X Now", url=composer_url),
        ],
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{draft_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{draft_id}"),
            InlineKeyboardButton("🗓️ Schedule (2h)", callback_data=f"sched_{draft_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_queue_keyboard(schedule_id: int, content: str = "") -> InlineKeyboardMarkup:
    """Buttons for an item in the queue."""
    buttons = []
    if content:
        encoded_text = urllib.parse.quote(content)
        composer_url = f"https://twitter.com/intent/tweet?text={encoded_text}"
        buttons.append([InlineKeyboardButton("🚀 Post to X Now", url=composer_url)])

    buttons.append([InlineKeyboardButton("🚫 Cancel Schedule", callback_data=f"cancelsched_{schedule_id}")])
    return InlineKeyboardMarkup(buttons)
