import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import settings
from database.db import get_session
from database.models import DepositRequest
from handlers.wallet.states import ChargeWalletStates
from keyboards.main_menu import back_to_main_menu_button
from services.deposit_id_generator import NoAvailableIdentifierError, issue_deposit_identifier
from services.wallet_service import get_or_create_user

router = Router(name="wallet.charge_wallet")
logger = logging.getLogger("netrix.wallet")


@router.callback_query(F.data == "start_charge_wallet")
async def ask_amount(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("چقدر می‌خوای شارژ کنی؟ مبلغ رو به تومان بفرست (مثلا 50000):")
    await state.set_state(ChargeWalletStates.waiting_for_amount)
    await callback.answer()


@router.message(ChargeWalletStates.waiting_for_amount, F.text)
async def receive_amount(message: Message, state: FSMContext):
    raw = message.text.strip().replace(",", "")
    if not raw.isdigit() or int(raw) < 1000:
        await message.answer("مبلغ معتبر نیست. یه عدد درست به تومان بفرست (حداقل 1000):")
        return

    amount = int(raw)

    try:
        async with get_session() as session:
            user = await get_or_create_user(
                session,
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                full_name=message.from_user.full_name,
            )

            try:
                identifier = await issue_deposit_identifier(session)
            except NoAvailableIdentifierError:
                await message.answer(
                    "الان امکان صدور شناسه‌ی شارژ جدید نیست (ظرفیت پر شده). "
                    "چند دقیقه دیگه دوباره امتحان کن یا با پشتیبانی تماس بگیر."
                )
                await state.clear()
                return

            amount_to_pay = amount + identifier
            credited_amount = amount + settings.DEPOSIT_BONUS_TOMAN

            deposit = DepositRequest(
                user_id=user.id,
                requested_amount_toman=amount,
                identifier=identifier,
                amount_to_pay_toman=amount_to_pay,
                credited_amount_toman=credited_amount,
            )
            session.add(deposit)
            await session.flush()
            deposit_id = deposit.id
    except Exception:
        logger.exception("ساخت درخواست شارژ برای کاربر %s با خطا مواجه شد", message.from_user.id)
        await message.answer(
            "⚠️ یه مشکل فنی پیش اومد و نتونستم درخواست شارژت رو ثبت کنم. "
            "لطفا دوباره امتحان کن؛ اگه ادامه داشت به پشتیبانی بگو."
        )
        await state.clear()
        return

    await state.update_data(deposit_id=deposit_id)
    await state.set_state(ChargeWalletStates.waiting_for_receipt)

    await message.answer(
        "💳 لطفا دقیقا همین مبلغ رو کارت‌به‌کارت کن (عدد آخر رو تغییر نده، همین شناسه‌ی تشخیصه):\n\n"
        f"مبلغ دقیق واریزی: *{amount_to_pay:,} تومان*\n"
        f"شماره کارت: `{settings.CARD_NUMBER}`\n"
        f"به نام: {settings.CARD_OWNER_NAME}\n\n"
        "بعد از واریز، عکس رسید رو همینجا بفرست تا برای تایید ارسال بشه.",
        parse_mode="Markdown",
    )


@router.message(ChargeWalletStates.waiting_for_amount)
async def receive_amount_wrong_type(message: Message):
    await message.answer("لطفا فقط یه عدد (مبلغ به تومان) بفرست:")


@router.message(ChargeWalletStates.waiting_for_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    deposit_id = data.get("deposit_id")
    photo_file_id = message.photo[-1].file_id

    if not deposit_id:
        await message.answer("این درخواست شارژ پیدا نشد، لطفا دوباره از منوی کیف‌پول شروع کن.")
        await state.clear()
        return

    if not settings.DEPOSIT_REVIEW_GROUP_ID:
        # این یعنی خود ادمین هنوز DEPOSIT_REVIEW_GROUP_ID رو توی .env تنظیم نکرده —
        # به‌جای شکست خوردن بی‌صدا، هم به کاربر هم توی لاگ واضح اعلام می‌کنیم.
        logger.error("DEPOSIT_REVIEW_GROUP_ID تنظیم نشده — نمی‌تونم رسید رو ارسال کنم.")
        await message.answer(
            "⚠️ سیستم تایید رسید فعلا تنظیم نشده. لطفا این پیام رو به ادمین ربات نشون بده "
            "(DEPOSIT_REVIEW_GROUP_ID توی تنظیمات خالیه)."
        )
        return

    try:
        async with get_session() as session:
            deposit = await session.get(DepositRequest, deposit_id)
            if deposit is None:
                await message.answer("این درخواست شارژ پیدا نشد، دوباره از اول امتحان کن.")
                await state.clear()
                return
            deposit.receipt_file_id = photo_file_id

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ تایید", callback_data=f"deposit_approve:{deposit.id}"),
                        InlineKeyboardButton(text="❌ رد", callback_data=f"deposit_reject:{deposit.id}"),
                    ]
                ]
            )

            caption = (
                "🧾 رسید شارژ جدید\n\n"
                f"کاربر: {message.from_user.full_name} (@{message.from_user.username or '-'})\n"
                f"آیدی عددی: {message.from_user.id}\n"
                f"مبلغ درخواستی: {deposit.requested_amount_toman:,} تومان\n"
                f"مبلغ واریزی مورد انتظار (با شناسه): {deposit.amount_to_pay_toman:,} تومان\n"
                f"مبلغی که در صورت تایید شارژ میشه: {deposit.credited_amount_toman:,} تومان\n"
                f"شناسه‌ی سه‌رقمی: {deposit.identifier}"
            )

            try:
                sent = await message.bot.send_photo(
                    chat_id=settings.DEPOSIT_REVIEW_GROUP_ID,
                    photo=photo_file_id,
                    caption=caption,
                    reply_markup=keyboard,
                )
            except TelegramAPIError:
                logger.exception(
                    "ارسال رسید به گروه تایید (%s) شکست خورد — بررسی کن ربات عضو/ادمین اون گروهه.",
                    settings.DEPOSIT_REVIEW_GROUP_ID,
                )
                await message.answer(
                    "⚠️ رسیدت ثبت شد ولی ارسالش برای بررسی با مشکل مواجه شد. "
                    "لطفا کمی بعد دوباره همین عکس رو بفرست یا مستقیم به پشتیبانی بگو."
                )
                return

            deposit.review_group_message_id = sent.message_id
    except Exception:
        logger.exception("پردازش رسید شارژ برای کاربر %s با خطا مواجه شد", message.from_user.id)
        await message.answer(
            "⚠️ یه مشکل فنی پیش اومد. رسیدت الان ثبت نشد — لطفا دوباره امتحان کن یا به پشتیبانی بگو."
        )
        return

    await state.clear()
    await message.answer(
        "رسیدت برای بررسی ارسال شد ✅ به محض تایید، کیف‌پولت شارژ میشه.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[back_to_main_menu_button()]),
    )


@router.message(ChargeWalletStates.waiting_for_receipt)
async def receive_receipt_wrong_type(message: Message):
    await message.answer("لطفا عکس رسید واریزی رو بفرست (نه متن).")
