from aiogram import F, Router
from aiogram.types import CallbackQuery

from database.db import get_session
from database.models import PlanCategory
from keyboards.subscription_menus import CATEGORY_LABELS, duration_selection_keyboard
from services.pricing_service import list_plans

router = Router(name="buy_subscription.duration_select")


@router.callback_query(F.data.startswith("cat:"))
async def show_durations(callback: CallbackQuery):
    category = PlanCategory(callback.data.split(":", 1)[1])

    async with get_session() as session:
        plans = await list_plans(session, category)

    if not plans:
        await callback.answer("فعلا پلنی برای این دسته تعریف نشده — بعدا امتحان کن.", show_alert=True)
        return

    await callback.message.edit_text(
        f"{CATEGORY_LABELS[category]}\n\nمدت زمان اشتراک رو انتخاب کن:",
        reply_markup=duration_selection_keyboard(plans),
    )
    await callback.answer()
