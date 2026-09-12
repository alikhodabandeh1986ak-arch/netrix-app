from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import settings

router = Router(name="admin.panel_menu")


def _is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💵 مدیریت قیمت‌ها", callback_data="admin:pricing")],
            [InlineKeyboardButton(text="📊 آمار کلی", callback_data="admin:stats")],
        ]
    )


@router.message(Command("admin"))
async def open_admin_panel(message: Message):
    if not _is_admin(message.from_user.id):
        return  # سکوت کامل — حتی نمی‌گیم این دستور وجود داره
    await message.answer("🛠 پنل مدیریت NETRIX", reply_markup=admin_menu_keyboard())
