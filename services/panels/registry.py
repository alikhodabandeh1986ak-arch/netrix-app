"""
تشخیص می‌ده هر دسته‌ی پلن باید از کدوم پنل سرویس بگیره:
- حجمی / نامحدود ساده        -> پنل «regular»
- مولتی‌لوکیشن / مولتی نامحدود -> پنل «multiloc»

وقتی بعدا OpenVPN یا تک‌ایپی اضافه شد، فقط اینجا یه mapping جدید اضافه می‌کنیم.
"""
from config import settings
from database.models import PlanCategory
from services.panels.base_panel import BasePanel
from services.panels.pasarguard_panel import PasarGuardPanel

_regular_panel: BasePanel | None = None
_multiloc_panel: BasePanel | None = None


def get_regular_panel() -> BasePanel:
    global _regular_panel
    if _regular_panel is None:
        _regular_panel = PasarGuardPanel(
            base_url=settings.PANEL_REGULAR_URL,
            username=settings.PANEL_REGULAR_USERNAME,
            password=settings.PANEL_REGULAR_PASSWORD,
        )
    return _regular_panel


def get_multiloc_panel() -> BasePanel:
    global _multiloc_panel
    if _multiloc_panel is None:
        _multiloc_panel = PasarGuardPanel(
            base_url=settings.PANEL_MULTILOC_URL,
            username=settings.PANEL_MULTILOC_USERNAME,
            password=settings.PANEL_MULTILOC_PASSWORD,
        )
    return _multiloc_panel


def get_panel_for_category(category: PlanCategory) -> tuple[BasePanel, str]:
    """برمی‌گردونه: (نمونه‌ی پنل, اسم کوتاه پنل برای ذخیره توی دیتابیس)"""
    if category in (PlanCategory.MULTI_LOCATION, PlanCategory.MULTI_LOCATION_UNLIMITED):
        return get_multiloc_panel(), "multiloc"
    return get_regular_panel(), "regular"
