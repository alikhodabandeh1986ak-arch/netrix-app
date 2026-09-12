from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from sqlalchemy import select

from database.db import get_session
from database.models import Subscription, User
from keyboards.main_menu import CB_MY_SUBSCRIPTIONS, back_to_main_menu_button

router = Router(name="menu.my_subscriptions")


def _back_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[back_to_main_menu_button()])


@router.callback_query(F.data == CB_MY_SUBSCRIPTIONS)
async def show_subscriptions(callback: CallbackQuery):
    async with get_session() as session:
        user_result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = user_result.scalar_one_or_none()

        subs = []
        if user:
            result = await session.execute(
                select(Subscription)
                .where(Subscription.user_id == user.id, Subscription.is_active.is_(True))
                .order_by(Subscription.expires_at)
            )
            subs = list(result.scalars().all())

    if not subs:
        await callback.message.edit_text(
            "هنوز اشتراک فعالی نداری. از منو می‌تونی یکی بخری 🛒",
            reply_markup=_back_menu_keyboard(),
        )
        await callback.answer()
        return

    now = datetime.now(timezone.utc)
    lines = ["📦 اشتراک‌های فعال تو:\n"]
    for sub in subs:
        remaining_days = max((sub.expires_at - now).days, 0)
        lines.append(f"• {sub.panel_username} — {remaining_days} روز باقی‌مونده\n`{sub.subscription_url}`\n")

    await callback.message.edit_text(
        "\n".join(lines), parse_mode="Markdown", reply_markup=_back_menu_keyboard()
    )
    await callback.answer()
