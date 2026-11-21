"""
Inline keyboard generators for Telegram Bot.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_draft_keyboard(draft_id: int) -> InlineKeyboardMarkup:
    """Buttons for managing a generated draft."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{draft_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{draft_id}"),
        ],
        [
            InlineKeyboardButton("📋 Copy Post", callback_data=f"copy_{draft_id}"),
            InlineKeyboardButton("🗓️ Schedule (2h)", callback_data=f"sched_{draft_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_queue_keyboard(schedule_id: int) -> InlineKeyboardMarkup:
    """Buttons for an item in the queue."""
    keyboard = [
        [
            InlineKeyboardButton("🚫 Cancel Schedule", callback_data=f"cancelsched_{schedule_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
