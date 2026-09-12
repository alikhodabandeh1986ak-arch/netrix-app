from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User


async def get_or_create_user(session: AsyncSession, telegram_id: int, username: str | None, full_name: str | None) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_id=telegram_id, username=username, full_name=full_name)
        session.add(user)
        await session.flush()
    return user


async def credit_wallet(session: AsyncSession, user: User, amount_toman: int) -> User:
    user.wallet_balance_toman += amount_toman
    await session.flush()
    return user


async def debit_wallet(session: AsyncSession, user: User, amount_toman: int) -> bool:
    """اگه موجودی کافی نباشه False برمی‌گردونه و چیزی کم نمی‌کنه."""
    if user.wallet_balance_toman < amount_toman:
        return False
    user.wallet_balance_toman -= amount_toman
    await session.flush()
    return True
