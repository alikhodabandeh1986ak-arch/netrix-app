from aiogram import F, Router
from aiogram.types import CallbackQuery

from keyboards.main_menu import CB_BUY_SUBSCRIPTION
from keyboards.subscription_menus import category_selection_keyboard

router = Router(name="buy_subscription.category_select")


@router.callback_query(F.data == CB_BUY_SUBSCRIPTION)
async def show_categories(callback: CallbackQuery):
    await callback.message.edit_text(
        "نوع اشتراکی که می‌خوای رو انتخاب کن:",
        reply_markup=category_selection_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    await callback.message.edit_text(
        "نوع اشتراکی که می‌خوای رو انتخاب کن:",
        reply_markup=category_selection_keyboard(),
    )
    await callback.answer()
