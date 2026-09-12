"""
از اینجا ادمین بدون دست‌زدن به کد می‌تونه:
- قیمت پلن‌های موجود رو عوض کنه
- پلن جدید (مدت‌زمان جدید برای یه دسته) اضافه کنه
همه‌چیز مستقیم توی جدول plans دیتابیس ذخیره میشه.
"""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from admin.panel_menu import _is_admin
from database.db import get_session
from database.models import PlanCategory
from keyboards.subscription_menus import CATEGORY_LABELS
from services.pricing_service import list_plans, upsert_plan

router = Router(name="admin.pricing")


class PricingStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_duration = State()
    waiting_for_price = State()
    waiting_for_data_limit = State()


def _category_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=label, callback_data=f"admin_cat:{cat.value}")]
        for cat, label in CATEGORY_LABELS.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data == "admin:pricing")
async def open_pricing(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        return
    await callback.message.answer(
        "کدوم دسته رو می‌خوای ویرایش/اضافه کنی؟", reply_markup=_category_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_cat:"))
async def pick_category(callback: CallbackQuery, state: FSMContext):
    if not _is_admin(callback.from_user.id):
        return
    category = PlanCategory(callback.data.split(":", 1)[1])

    async with get_session() as session:
        plans = await list_plans(session, category)

    lines = [f"پلن‌های فعلی «{CATEGORY_LABELS[category]}»:"]
    if plans:
        for p in plans:
            extra = f" — {p.data_limit_gb} گیگ" if p.data_limit_gb else ""
            lines.append(f"• {p.duration_days} روزه{extra} → {p.price_toman:,} تومان")
    else:
        lines.append("هنوز پلنی تعریف نشده.")
    lines.append("\nحالا مدت‌زمان (روز) پلنی که می‌خوای اضافه/ویرایش کنی رو بفرست:")

    await state.update_data(category=category.value)
    await state.set_state(PricingStates.waiting_for_duration)
    await callback.message.answer("\n".join(lines))
    await callback.answer()


@router.message(PricingStates.waiting_for_duration)
async def set_duration(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    if not message.text.strip().isdigit():
        await message.answer("یه عدد صحیح برای تعداد روز بفرست:")
        return
    await state.update_data(duration_days=int(message.text.strip()))
    await state.set_state(PricingStates.waiting_for_price)
    await message.answer("قیمت این پلن به تومان چقدر باشه؟")


@router.message(PricingStates.waiting_for_price)
async def set_price(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    if not message.text.strip().isdigit():
        await message.answer("یه عدد صحیح برای قیمت بفرست:")
        return
    await state.update_data(price_toman=int(message.text.strip()))

    data = await state.get_data()
    category = PlanCategory(data["category"])
    if category == PlanCategory.VOLUME_BASED:
        await state.set_state(PricingStates.waiting_for_data_limit)
        await message.answer("این پلن حجمیه — حجمش چند گیگ باشه؟")
        return

    await _save_plan(message, state)


@router.message(PricingStates.waiting_for_data_limit)
async def set_data_limit(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    if not message.text.strip().isdigit():
        await message.answer("یه عدد صحیح برای حجم (گیگابایت) بفرست:")
        return
    await state.update_data(data_limit_gb=int(message.text.strip()))
    await _save_plan(message, state)


async def _save_plan(message: Message, state: FSMContext):
    data = await state.get_data()
    category = PlanCategory(data["category"])

    async with get_session() as session:
        plan = await upsert_plan(
            session,
            category=category,
            duration_days=data["duration_days"],
            price_toman=data["price_toman"],
            data_limit_gb=data.get("data_limit_gb"),
        )

    await message.answer(
        f"✅ ثبت شد: {CATEGORY_LABELS[category]} — {plan.duration_days} روزه — {plan.price_toman:,} تومان"
    )
    await state.clear()
