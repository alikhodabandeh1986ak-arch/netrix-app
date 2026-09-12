from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from database.db import get_session
from keyboards.main_menu import CB_WALLET, back_to_main_menu_button
from services.wallet_service import get_or_create_user

router = Router(name="wallet.balance")


@router.callback_query(F.data == CB_WALLET)
async def show_wallet(callback: CallbackQuery):
    async with get_session() as session:
        user = await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            full_name=callback.from_user.full_name,
        )
        balance = user.wallet_balance_toman

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ شارژ کیف‌پول", callback_data="start_charge_wallet")],
            back_to_main_menu_button(),
        ]
    )
    await callback.message.edit_text(f"💰 موجودی فعلی: {balance:,} تومان", reply_markup=keyboard)
    await callback.answer()
