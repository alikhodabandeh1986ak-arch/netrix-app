"""
مدیریت قیمت‌ها — کاملا دیتابیسی، هیچ عددی توی کد هاردکد نیست.
همینه که ادمین می‌تونه از پنل مدیریت داخل ربات (admin/pricing.py) بدون
دست‌زدن به کد، قیمت‌ها رو عوض کنه یا پلن جدید (مثلا مدت‌زمان جدید) اضافه کنه.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Plan, PlanCategory


async def list_plans(session: AsyncSession, category: PlanCategory) -> list[Plan]:
    result = await session.execute(
        select(Plan)
        .where(Plan.category == category, Plan.is_active.is_(True))
        .order_by(Plan.duration_days)
    )
    return list(result.scalars().all())


async def get_plan(session: AsyncSession, plan_id: int) -> Plan | None:
    return await session.get(Plan, plan_id)


async def upsert_plan(
    session: AsyncSession,
    category: PlanCategory,
    duration_days: int,
    price_toman: int,
    data_limit_gb: int | None = None,
) -> Plan:
    result = await session.execute(
        select(Plan).where(Plan.category == category, Plan.duration_days == duration_days)
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        plan = Plan(
            category=category,
            duration_days=duration_days,
            price_toman=price_toman,
            data_limit_gb=data_limit_gb,
        )
        session.add(plan)
    else:
        plan.price_toman = price_toman
        if data_limit_gb is not None:
            plan.data_limit_gb = data_limit_gb
    await session.flush()
    return plan


async def set_plan_active(session: AsyncSession, plan_id: int, is_active: bool) -> None:
    plan = await session.get(Plan, plan_id)
    if plan:
        plan.is_active = is_active
        await session.flush()
