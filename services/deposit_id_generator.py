"""
تولید شناسه‌ی سه‌رقمی رندوم (پیش‌فرض 100 تا 900) برای هر درخواست شارژ.
هر شناسه‌ای که صادر بشه، تا DEPOSIT_ID_COOLDOWN_DAYS روز دیگه قابل صدور
دوباره نیست (چه تایید بشه چه نشه — چون همین که به یه کاربر گفتیم این عدد
رو واریز کن، دیگه نباید هم‌زمان به کس دیگه‌ای هم بگیم).
"""
import random
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.models import UsedIdentifier


class NoAvailableIdentifierError(Exception):
    """وقتی همه‌ی بازه‌ی 100-900 توی کول‌داون دو هفته‌ای گیر کرده باشن."""


async def issue_deposit_identifier(session: AsyncSession) -> int:
    cutoff = datetime.utcnow() - timedelta(days=settings.DEPOSIT_ID_COOLDOWN_DAYS)

    result = await session.execute(
        select(UsedIdentifier.identifier).where(UsedIdentifier.issued_at >= cutoff)
    )
    recently_used = {row[0] for row in result.all()}

    all_possible = set(range(settings.DEPOSIT_ID_MIN, settings.DEPOSIT_ID_MAX + 1))
    available = list(all_possible - recently_used)

    if not available:
        # این یعنی باید فوری به ادمین اطلاع داد — بازه‌ی شناسه‌ها تموم شده
        raise NoAvailableIdentifierError(
            f"همه‌ی {len(all_possible)} شناسه توی {settings.DEPOSIT_ID_COOLDOWN_DAYS} روز اخیر استفاده شدن."
        )

    identifier = random.choice(available)
    session.add(UsedIdentifier(identifier=identifier))
    return identifier
