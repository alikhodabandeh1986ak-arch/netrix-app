import logging
import uuid
from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from database.db import get_session
from database.models import Subscription
from keyboards.main_menu import back_to_main_menu_button
from keyboards.subscription_menus import confirm_purchase_keyboard
from services.panels.registry import get_panel_for_category
from services.pricing_service import get_plan
from services.wallet_service import credit_wallet, debit_wallet, get_or_create_user

router = Router(name="buy_subscription.confirm_purchase")
logger = logging.getLogger("netrix.purchase")


def _back_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[back_to_main_menu_button()])


@router.callback_query(F.data.startswith("plan:"))
async def ask_confirmation(callback: CallbackQuery):
    plan_id = int(callback.data.split(":", 1)[1])

    try:
        async with get_session() as session:
            plan = await get_plan(session, plan_id)
    except Exception:
        logger.exception("خطا در خوندن پلن %s", plan_id)
        await callback.answer("مشکل فنی پیش اومد، دوباره امتحان کن.", show_alert=True)
        return

    if not plan:
        await callback.answer("این پلن دیگه در دسترس نیست.", show_alert=True)
        return

    text = f"مدت: {plan.duration_days} روز\nقیمت: {plan.price_toman:,} تومان\n\n"
    if plan.data_limit_gb:
        text += f"حجم: {plan.data_limit_gb} گیگابایت\n\n"
    text += "برای ادامه‌ی خرید تایید کن. مبلغ از کیف‌پولت کسر میشه."

    await callback.message.edit_text(text, reply_markup=confirm_purchase_keyboard(plan.id))
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_purchase:"))
async def do_purchase(callback: CallbackQuery):
    plan_id = int(callback.data.split(":", 1)[1])

    try:
        async with get_session() as session:
            plan = await get_plan(session, plan_id)
            if not plan:
                await callback.answer("این پلن دیگه در دسترس نیست.", show_alert=True)
                return

            user = await get_or_create_user(
                session,
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
                full_name=callback.from_user.full_name,
            )

            if not await debit_wallet(session, user, plan.price_toman):
                await callback.answer(
                    "موجودی کیف‌پولت کافی نیست. اول کیف‌پولت رو شارژ کن.", show_alert=True
                )
                return

            panel, panel_name = get_panel_for_category(plan.category)
            panel_username = f"netrix_{callback.from_user.id}_{uuid.uuid4().hex[:6]}"

            try:
                panel_user = await panel.create_user(
                    username=panel_username,
                    duration_days=plan.duration_days,
                    data_limit_gb=plan.data_limit_gb,
                )
            except Exception:
                logger.exception("ساخت کاربر روی پنل %s شکست خورد", panel_name)
                # اگه ساخت روی پنل شکست خورد، پول رو برگردون که کاربر ضرر نکنه
                await credit_wallet(session, user, plan.price_toman)
                await callback.message.edit_text(
                    "❌ ساخت اشتراک روی پنل با خطا مواجه شد. پول به کیف‌پولت برگشت داده شد.\n"
                    "لطفا کمی بعد دوباره امتحان کن یا با پشتیبانی تماس بگیر.",
                    reply_markup=_back_menu_keyboard(),
                )
                await callback.answer()
                return

            expires_at = datetime.now(timezone.utc) + timedelta(days=plan.duration_days)
            session.add(
                Subscription(
                    user_id=user.id,
                    plan_id=plan.id,
                    panel_name=panel_name,
                    panel_username=panel_user.username,
                    subscription_url=panel_user.subscription_url,
                    expires_at=expires_at,
                )
            )
    except Exception:
        logger.exception("خرید اشتراک برای کاربر %s با خطا مواجه شد", callback.from_user.id)
        await callback.message.edit_text(
            "⚠️ یه مشکل فنی پیش اومد و خرید انجام نشد. اگه پولی کسر شده باشه به پشتیبانی بگو تا بررسی بشه.",
            reply_markup=_back_menu_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "✅ اشتراکت با موفقیت ساخته شد!\n\n"
        f"لینک اشتراک:\n`{panel_user.subscription_url}`\n\n"
        "این لینک رو توی اپلیکیشن کلاینتت وارد کن.",
        parse_mode="Markdown",
        reply_markup=_back_menu_keyboard(),
    )
    await callback.answer()
