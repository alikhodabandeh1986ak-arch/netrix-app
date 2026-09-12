from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from keyboards.main_menu import CB_SUPPORT, back_to_main_menu_button

router = Router(name="menu.support")


@router.callback_query(F.data == CB_SUPPORT)
async def show_support(callback: CallbackQuery):
    # TODO: آیدی/لینک پشتیبانی واقعیت رو اینجا بذار
    await callback.message.edit_text(
        "برای پشتیبانی می‌تونی به آیدی @your_support_id پیام بدی.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[back_to_main_menu_button()]),
    )
    await callback.answer()
