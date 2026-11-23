"""
Inline and Reply keyboard generators for Telegram Bot.
Includes Persistent Dashboard Keyboard, Action Menus, and Post Cards.
"""

import urllib.parse
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from postpilot.utils.config import settings


def get_dashboard_reply_keyboard() -> ReplyKeyboardMarkup:
    """
    Persistent reply keyboard grid pinned below the chat box.
    Provides instant 1-tap access to core workflows.
    """
    keyboard = [
        [
            KeyboardButton("🔥 Live Niche Trends"),
            KeyboardButton("⚡ Quick Ideas (2)"),
        ],
        [
            KeyboardButton("🧵 Viral Thread"),
            KeyboardButton("💬 Smart Reply"),
        ],
        [
            KeyboardButton("👥 Tracked Creators"),
            KeyboardButton("📝 Review Drafts"),
        ],
        [
            KeyboardButton("📊 System Status"),
            KeyboardButton("📖 Guide & Help"),
        ],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)


def get_welcome_inline_keyboard() -> InlineKeyboardMarkup:
    """Inline menu buttons shown on /start."""
    keyboard = [
        [
            InlineKeyboardButton("🔥 Live Niche Trends", callback_data="menu_trends"),
            InlineKeyboardButton("⚡ Quick Ideas (2)", callback_data="menu_ideas_2"),
        ],
        [
            InlineKeyboardButton("🧵 Viral Thread", callback_data="menu_thread"),
            InlineKeyboardButton("💬 Smart Reply", callback_data="menu_reply"),
        ],
        [
            InlineKeyboardButton("👥 My Creators", callback_data="menu_creators"),
            InlineKeyboardButton("📝 Review Drafts", callback_data="menu_drafts"),
        ],
        [
            InlineKeyboardButton("🗓️ View Queue", callback_data="menu_queue"),
            InlineKeyboardButton("📊 System Status", callback_data="menu_status"),
        ],
        [
            InlineKeyboardButton("📖 Help Guide", callback_data="menu_help"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_status_keyboard() -> InlineKeyboardMarkup:
    """Action buttons attached to System Health card."""
    keyboard = [
        [
            InlineKeyboardButton("🔄 Refresh Diagnostics", callback_data="refresh_status"),
            InlineKeyboardButton("⚡ Quick Ideas (2)", callback_data="menu_ideas_2"),
        ],
        [
            InlineKeyboardButton("👥 Tracked Creators", callback_data="menu_creators"),
            InlineKeyboardButton("📝 Review Drafts", callback_data="menu_drafts"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_draft_keyboard(draft_id: int, content: str = "") -> InlineKeyboardMarkup:
    """
    Buttons for managing a generated draft card.
    Direct 1-tap 'Post to X Now' launches the native mobile X composer immediately
    without going through any external browser or redirect pages.
    """
    encoded_text = urllib.parse.quote(content)
    composer_url = f"https://twitter.com/intent/tweet?text={encoded_text}"

    keyboard = [
        [
            InlineKeyboardButton("🚀 Post to X Now", url=composer_url),
            InlineKeyboardButton("✅ Mark as Posted", callback_data=f"posted_{draft_id}"),
        ],
        [
            InlineKeyboardButton("🗓️ Schedule (2h)", callback_data=f"sched_{draft_id}"),
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{draft_id}"),
            InlineKeyboardButton("❌ Dismiss", callback_data=f"reject_{draft_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_queue_keyboard(schedule_id: int, draft_id: int = 0, content: str = "") -> InlineKeyboardMarkup:
    """Buttons for an item in the queue."""
    buttons = []
    if content:
        encoded_text = urllib.parse.quote(content)
        composer_url = f"https://twitter.com/intent/tweet?text={encoded_text}"
        buttons.append([InlineKeyboardButton("🚀 Post to X Now (Early)", url=composer_url)])
    elif draft_id:
        encoded_text = urllib.parse.quote("PostPilot Content")
        composer_url = f"https://twitter.com/intent/tweet?text={encoded_text}"
        buttons.append([InlineKeyboardButton("🚀 Post to X Now (Early)", url=composer_url)])

    buttons.append([InlineKeyboardButton("🚫 Cancel Schedule", callback_data=f"cancelsched_{schedule_id}")])
    return InlineKeyboardMarkup(buttons)


def get_reply_card_keyboard(url: str) -> InlineKeyboardMarkup:
    """Button attached to each individual reply card for direct posting."""
    keyboard = [
        [
            InlineKeyboardButton("🚀 Post Reply on X", url=url),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_thread_keyboard(hook_url: str, topic: str = "") -> InlineKeyboardMarkup:
    """Action buttons attached to a completed viral thread card."""
    buttons = []
    if hook_url:
        buttons.append([InlineKeyboardButton("🚀 Post Tweet 1 (Hook)", url=hook_url)])
    buttons.append([
        InlineKeyboardButton("⚡ Quick Ideas (2)", callback_data="menu_ideas_2"),
        InlineKeyboardButton("🔥 Niche Trends", callback_data="menu_trends"),
    ])
    return InlineKeyboardMarkup(buttons)
