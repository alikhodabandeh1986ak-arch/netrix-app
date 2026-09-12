"""
مدل‌های دیتابیس. با SQLAlchemy 2.x async نوشته شده و روی هر Postgres
(Supabase / Neon / رندر) بدون تغییر کار می‌کنه.
"""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------- کاربران
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    wallet_balance_toman: Mapped[int] = mapped_column(BigInteger, default=0)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    deposits: Mapped[list["DepositRequest"]] = relationship(back_populates="user")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")


# ---------------------------------------------------------- درخواست‌های شارژ
class DepositStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DepositRequest(Base):
    """
    هر درخواست شارژ یه شناسه‌ی سه‌رقمی رندوم (100-900) می‌گیره که به مبلغ
    درخواستی چسبونده میشه (مثلا 50000 -> باید 50340 واریز بشه).
    بعد از تایید، کیف‌پول کاربر به‌اندازه‌ی «مبلغ درخواستی + DEPOSIT_BONUS_TOMAN»
    شارژ میشه (نه مبلغ واریزیِ همراه با شناسه).
    """

    __tablename__ = "deposit_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    requested_amount_toman: Mapped[int] = mapped_column(BigInteger)
    identifier: Mapped[int] = mapped_column(Integer)  # عدد 100 تا 900
    amount_to_pay_toman: Mapped[int] = mapped_column(BigInteger)  # requested + identifier
    credited_amount_toman: Mapped[int] = mapped_column(BigInteger)  # requested + بونوس هزار تومنی
    receipt_file_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[DepositStatus] = mapped_column(Enum(DepositStatus), default=DepositStatus.PENDING)
    review_group_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reviewed_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="deposits")


class UsedIdentifier(Base):
    """
    آرشیو شناسه‌های استفاده‌شده، برای اجرای قانون «هر شناسه دو هفته
    غیرقابل استفاده‌ست». وقتی یه شناسه صادر میشه (نه لزوما تایید‌شده) اینجا ثبت میشه.
    """

    __tablename__ = "used_identifiers"

    id: Mapped[int] = mapped_column(primary_key=True)
    identifier: Mapped[int] = mapped_column(Integer, index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# --------------------------------------------------------------- پلن‌ها و قیمت‌ها
class PlanCategory(str, enum.Enum):
    VOLUME_BASED = "volume_based"          # حجمی — پنل معمولی
    UNLIMITED = "unlimited"                # نامحدود — پنل معمولی
    MULTI_LOCATION = "multi_location"              # مولتی‌لوکیشن — پنل مولتی
    MULTI_LOCATION_UNLIMITED = "multi_location_unlimited"  # مولتی‌لوکیشن نامحدود — پنل مولتی


class Plan(Base):
    """
    هر ردیف = یه ترکیب «دسته + مدت زمان» با قیمت خودش.
    قیمت‌ها کاملا از پنل ادمین توی خود ربات قابل تغییرن (جدول pricing_service.py).
    """

    __tablename__ = "plans"
    __table_args__ = (UniqueConstraint("category", "duration_days", name="uq_plan_category_duration"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[PlanCategory] = mapped_column(Enum(PlanCategory))
    duration_days: Mapped[int] = mapped_column(Integer)
    # فقط برای اشتراک‌های حجمی معنی داره؛ برای نامحدود/مولتی نادیده گرفته میشه
    data_limit_gb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_toman: Mapped[int] = mapped_column(BigInteger)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# --------------------------------------------------------------- اشتراک‌ها
class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    panel_name: Mapped[str] = mapped_column(String(32))  # "regular" یا "multiloc"
    panel_username: Mapped[str] = mapped_column(String(64))  # یوزرنیم ساخته‌شده روی پنل
    subscription_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="subscriptions")
