from aiogram import F, Router
from aiogram.types import CallbackQuery

from config import settings
from database.db import get_session
from database.models import DepositRequest, DepositStatus, User
from services.wallet_service import credit_wallet

router = Router(name="admin.deposit_review")


def _is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


@router.callback_query(F.data.startswith("deposit_approve:"))
async def approve_deposit(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await callback.answer("این دکمه فقط برای ادمین‌هاست.", show_alert=True)
        return

    deposit_id = int(callback.data.split(":", 1)[1])

    async with get_session() as session:
        deposit = await session.get(DepositRequest, deposit_id)
        if deposit is None:
            await callback.answer("این درخواست پیدا نشد.", show_alert=True)
            return
        if deposit.status != DepositStatus.PENDING:
            await callback.answer("این درخواست قبلا بررسی شده.", show_alert=True)
            return

        user = await session.get(User, deposit.user_id)
        await credit_wallet(session, user, deposit.credited_amount_toman)

        deposit.status = DepositStatus.APPROVED
        deposit.reviewed_by_admin_id = callback.from_user.id
        telegram_id = user.telegram_id
        credited = deposit.credited_amount_toman
        new_balance = user.wallet_balance_toman

    await callback.message.edit_caption(
        caption=callback.message.caption + f"\n\n✅ تایید شد توسط {callback.from_user.full_name}",
        reply_markup=None,
    )
    await callback.bot.send_message(
        telegram_id,
        f"✅ واریزیت تایید شد و {credited:,} تومان به کیف‌پولت اضافه شد.\n"
        f"موجودی فعلی: {new_balance:,} تومان",
    )
    await callback.answer("تایید شد.")


@router.callback_query(F.data.startswith("deposit_reject:"))
async def reject_deposit(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await callback.answer("این دکمه فقط برای ادمین‌هاست.", show_alert=True)
        return

    deposit_id = int(callback.data.split(":", 1)[1])

    async with get_session() as session:
        deposit = await session.get(DepositRequest, deposit_id)
        if deposit is None:
            await callback.answer("این درخواست پیدا نشد.", show_alert=True)
            return
        if deposit.status != DepositStatus.PENDING:
            await callback.answer("این درخواست قبلا بررسی شده.", show_alert=True)
            return

        deposit.status = DepositStatus.REJECTED
        deposit.reviewed_by_admin_id = callback.from_user.id
        user = await session.get(User, deposit.user_id)
        telegram_id = user.telegram_id

    await callback.message.edit_caption(
        caption=callback.message.caption + f"\n\n❌ رد شد توسط {callback.from_user.full_name}",
        reply_markup=None,
    )
    await callback.bot.send_message(
        telegram_id,
        "❌ رسید واریزیت تایید نشد. اگه فکر می‌کنی اشتباهی شده، با پشتیبانی تماس بگیر.",
    )
    await callback.answer("رد شد.")
