"""
قبل از هر اکشنی توی ربات، چک می‌کنه کاربر عضو کانال اجباری هست یا نه.
اگه نیست، یه پیام با دکمه‌ی «عضو شدم» نشونش می‌ده و اجازه نمی‌ده ادامه بده.
"""
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, TelegramObject

from config import settings


def _join_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    if settings.REQUIRED_CHANNEL_LINK:
        buttons.append([InlineKeyboardButton(text="📢 عضویت در کانال", url=settings.REQUIRED_CHANNEL_LINK)])
    buttons.append([InlineKeyboardButton(text="✅ عضو شدم", callback_data="check_channel_membership")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


class ChannelGateMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not settings.REQUIRED_CHANNEL_ID:
            # اگه کانال اجباری تنظیم نشده، گیت غیرفعاله
            return await handler(event, data)

        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        if user.id in settings.ADMIN_IDS:
            # ادمین‌ها همیشه بدون گیت عبور می‌کنن — وگرنه ممکنه توی گروه تایید رسید گیر کنن
            return await handler(event, data)

        bot = data["bot"]
        try:
            member = await bot.get_chat_member(settings.REQUIRED_CHANNEL_ID, user.id)
            is_member = member.status not in ("left", "kicked")
        except Exception:
            # اگه ربات ادمین کانال نیست یا خطای دیگه‌ای خورد، برای امنیت جلوی کاربر رو نمی‌گیریم
            # ولی توی لاگ حتما باید دید — این یعنی یه‌جای تنظیمات مشکل داره
            is_member = True

        if is_member:
            return await handler(event, data)

        text = "برای استفاده از ربات، اول باید عضو کانال ما بشی 👇"
        if isinstance(event, Message):
            await event.answer(text, reply_markup=_join_keyboard())
        elif isinstance(event, CallbackQuery):
            await event.answer("اول باید عضو کانال بشی!", show_alert=True)
            await event.message.answer(text, reply_markup=_join_keyboard())
        return None
