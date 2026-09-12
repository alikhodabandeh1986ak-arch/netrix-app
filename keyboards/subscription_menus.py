from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.models import Plan, PlanCategory
from keyboards.main_menu import back_to_main_menu_button

CATEGORY_LABELS = {
    PlanCategory.VOLUME_BASED: "📶 اشتراک حجمی",
    PlanCategory.UNLIMITED: "♾ اشتراک نامحدود",
    PlanCategory.MULTI_LOCATION: "🌍 اشتراک مولتی‌لوکیشن",
    PlanCategory.MULTI_LOCATION_UNLIMITED: "🌍♾ مولتی‌لوکیشن نامحدود",
}


def category_selection_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=CATEGORY_LABELS[PlanCategory.VOLUME_BASED], callback_data=f"cat:{PlanCategory.VOLUME_BASED.value}")],
        [InlineKeyboardButton(text=CATEGORY_LABELS[PlanCategory.UNLIMITED], callback_data=f"cat:{PlanCategory.UNLIMITED.value}")],
        [InlineKeyboardButton(text=CATEGORY_LABELS[PlanCategory.MULTI_LOCATION], callback_data=f"cat:{PlanCategory.MULTI_LOCATION.value}")],
        [InlineKeyboardButton(text=CATEGORY_LABELS[PlanCategory.MULTI_LOCATION_UNLIMITED], callback_data=f"cat:{PlanCategory.MULTI_LOCATION_UNLIMITED.value}")],
        back_to_main_menu_button(),
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def duration_selection_keyboard(plans: list[Plan]) -> InlineKeyboardMarkup:
    rows = []
    for plan in plans:
        label = f"{plan.duration_days} روزه — {plan.price_toman:,} تومان"
        if plan.data_limit_gb:
            label = f"{plan.duration_days} روزه — {plan.data_limit_gb} گیگ — {plan.price_toman:,} تومان"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"plan:{plan.id}")])
    rows.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_categories")])
    rows.append(back_to_main_menu_button())
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_purchase_keyboard(plan_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ تایید و خرید", callback_data=f"confirm_purchase:{plan_id}")],
            [InlineKeyboardButton(text="🔙 انصراف", callback_data="back_to_categories")],
        ]
    )
