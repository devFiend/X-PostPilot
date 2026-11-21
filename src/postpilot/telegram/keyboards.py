"""
Inline keyboard generators for Telegram Bot.
"""

import urllib.parse
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from postpilot.utils.config import settings


def get_draft_keyboard(draft_id: int, content: str = "") -> InlineKeyboardMarkup:
    """
    Buttons for managing a generated draft.
    If hosted on Render (or APP_URL set), clicking 'Post to X Now' routes through
    our /post/{draft_id} endpoint, which instantly auto-approves the draft in the database
    and redirects directly into the X composer with the tweet pre-filled!
    """
    base = settings.base_url
    if base:
        composer_url = f"{base.rstrip('/')}/post/{draft_id}"
    else:
        encoded_text = urllib.parse.quote(content)
        composer_url = f"https://twitter.com/intent/tweet?text={encoded_text}"

    keyboard = [
        [
            InlineKeyboardButton("🚀 Post to X Now (Auto-Approves)", url=composer_url),
        ],
        [
            InlineKeyboardButton("✅ Approve Only", callback_data=f"approve_{draft_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{draft_id}"),
            InlineKeyboardButton("🗓️ Schedule (2h)", callback_data=f"sched_{draft_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_queue_keyboard(schedule_id: int, draft_id: int = 0, content: str = "") -> InlineKeyboardMarkup:
    """Buttons for an item in the queue."""
    buttons = []
    base = settings.base_url
    if base and draft_id:
        composer_url = f"{base.rstrip('/')}/post/{draft_id}"
        buttons.append([InlineKeyboardButton("🚀 Post to X Now (Early)", url=composer_url)])
    elif content:
        encoded_text = urllib.parse.quote(content)
        composer_url = f"https://twitter.com/intent/tweet?text={encoded_text}"
        buttons.append([InlineKeyboardButton("🚀 Post to X Now (Early)", url=composer_url)])

    buttons.append([InlineKeyboardButton("🚫 Cancel Schedule", callback_data=f"cancelsched_{schedule_id}")])
    return InlineKeyboardMarkup(buttons)
