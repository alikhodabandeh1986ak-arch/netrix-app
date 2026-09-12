"""
مدیریت برگشت به منوی اصلی — چون همه‌جا (کیف‌پول، خرید، پشتیبانی) دکمه‌ی
«منوی اصلی» به همینجا وصله. همچنین چک مجدد عضویت کانال بعد از زدن «عضو شدم».
"""
from aiogram import F, Router
from aiogram.types import CallbackQuery

from keyboards.main_menu import CB_MAIN_MENU, MAIN_MENU_TEXT, main_menu_keyboard

router = Router(name="menu.navigation")


@router.callback_query(F.data == CB_MAIN_MENU)
async def back_to_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "check_channel_membership")
async def recheck_membership(callback: CallbackQuery):
    # خودِ ChannelGateMiddleware دوباره چک می‌کنه؛ اگه اینجا رسیدیم یعنی عضو شده
    await callback.answer("عضویتت تایید شد ✅")
    await callback.message.edit_text(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())
