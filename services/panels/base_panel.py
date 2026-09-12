"""
اینترفیس مشترک همه‌ی پنل‌ها. هر پنل جدید (PasarGuard، بعدا OpenVPN و ...)
باید همین متدها رو پیاده کنه. بقیه‌ی کد ربات فقط با این اینترفیس کار می‌کنه
و اصلا نمی‌دونه پشتش چه پنلی‌ست — همینه که اضافه‌کردن پنل جدید رو راحت می‌کنه.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PanelUser:
    username: str
    subscription_url: str
    expire_timestamp: int | None
    data_limit_bytes: int | None


class BasePanel(ABC):
    @abstractmethod
    async def create_user(
        self,
        username: str,
        duration_days: int,
        data_limit_gb: int | None = None,
    ) -> PanelUser:
        """یه کاربر جدید روی پنل می‌سازه و لینک اشتراکش رو برمی‌گردونه."""
        raise NotImplementedError

    @abstractmethod
    async def get_user(self, username: str) -> PanelUser | None:
        raise NotImplementedError

    @abstractmethod
    async def extend_user(self, username: str, extra_days: int) -> PanelUser:
        raise NotImplementedError

    @abstractmethod
    async def disable_user(self, username: str) -> None:
        raise NotImplementedError
