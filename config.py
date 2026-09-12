"""
تنظیمات مرکزی ربات — همه‌چیز از Environment Variables خونده میشه.
هیچ‌وقت مقدار واقعی توکن/رمز رو مستقیم اینجا ننویس؛ توی فایل .env بذارش
(و روی رندر توی بخش Environment پنل ست کن).
"""
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"متغیر محیطی {name} ست نشده — توی .env اضافه‌اش کن.")
    return value


@dataclass
class Settings:
    # --- ربات ---
    BOT_TOKEN: str = field(default_factory=lambda: _get("BOT_TOKEN", required=True))

    # حالت اجرا: polling (برای تست لوکال توی VS Code) یا webhook (برای رندر)
    RUN_MODE: str = field(default_factory=lambda: _get("RUN_MODE", "polling"))
    WEBHOOK_BASE_URL: str = field(default_factory=lambda: _get("WEBHOOK_BASE_URL", ""))
    WEBHOOK_PATH: str = field(default_factory=lambda: _get("WEBHOOK_PATH", "/webhook"))
    WEBHOOK_SECRET: str = field(default_factory=lambda: _get("WEBHOOK_SECRET", "change-me"))
    PORT: int = field(default_factory=lambda: int(_get("PORT", "10000")))

    # --- دیتابیس (Supabase / Neon / هر Postgres دیگه) ---
    DATABASE_URL: str = field(default_factory=lambda: _get("DATABASE_URL", required=True))

    # --- ادمین‌ها و گروه تایید رسید ---
    ADMIN_IDS: list[int] = field(
        default_factory=lambda: [
            int(x) for x in _get("ADMIN_IDS", "").replace(" ", "").split(",") if x
        ]
    )
    DEPOSIT_REVIEW_GROUP_ID: int = field(
        default_factory=lambda: int(_get("DEPOSIT_REVIEW_GROUP_ID", "0"))
    )

    # --- گیت عضویت اجباری کانال ---
    REQUIRED_CHANNEL_ID: str = field(default_factory=lambda: _get("REQUIRED_CHANNEL_ID", ""))
    REQUIRED_CHANNEL_LINK: str = field(default_factory=lambda: _get("REQUIRED_CHANNEL_LINK", ""))

    # --- کارت بانکی برای واریز ---
    CARD_NUMBER: str = field(default_factory=lambda: _get("CARD_NUMBER", ""))
    CARD_OWNER_NAME: str = field(default_factory=lambda: _get("CARD_OWNER_NAME", ""))

    # --- منطق شارژ کیف‌پول ---
    DEPOSIT_ID_MIN: int = 100
    DEPOSIT_ID_MAX: int = 900
    DEPOSIT_ID_COOLDOWN_DAYS: int = 14
    DEPOSIT_BONUS_TOMAN: int = 1000

    # --- پنل‌های PasarGuard ---
    PANEL_REGULAR_URL: str = field(default_factory=lambda: _get("PANEL_REGULAR_URL", ""))
    PANEL_REGULAR_USERNAME: str = field(default_factory=lambda: _get("PANEL_REGULAR_USERNAME", ""))
    PANEL_REGULAR_PASSWORD: str = field(default_factory=lambda: _get("PANEL_REGULAR_PASSWORD", ""))

    PANEL_MULTILOC_URL: str = field(default_factory=lambda: _get("PANEL_MULTILOC_URL", ""))
    PANEL_MULTILOC_USERNAME: str = field(default_factory=lambda: _get("PANEL_MULTILOC_USERNAME", ""))
    PANEL_MULTILOC_PASSWORD: str = field(default_factory=lambda: _get("PANEL_MULTILOC_PASSWORD", ""))


settings = Settings()
