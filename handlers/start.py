from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from database.db import get_session
from keyboards.main_menu import MAIN_MENU_TEXT, main_menu_keyboard
from services.wallet_service import get_or_create_user

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message):
    async with get_session() as session:
        await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )

    await message.answer(
        f"سلام {message.from_user.first_name} 👋\nبه ربات NETRIX خوش اومدی.\n\n{MAIN_MENU_TEXT}",
        reply_markup=main_menu_keyboard(),
    )
