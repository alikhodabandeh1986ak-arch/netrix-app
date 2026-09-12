from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

MAIN_MENU_TEXT = "🤖 منوی اصلی NETRIX\n\nیکی از گزینه‌های زیر رو انتخاب کن:"

CB_BUY_SUBSCRIPTION = "menu:buy_subscription"
CB_MY_SUBSCRIPTIONS = "menu:my_subscriptions"
CB_WALLET = "menu:wallet"
CB_SUPPORT = "menu:support"
CB_MAIN_MENU = "menu:main"


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 خرید اشتراک جدید", callback_data=CB_BUY_SUBSCRIPTION)],
            [
                InlineKeyboardButton(text="📦 اشتراک‌های من", callback_data=CB_MY_SUBSCRIPTIONS),
                InlineKeyboardButton(text="💰 کیف پول من", callback_data=CB_WALLET),
            ],
            [InlineKeyboardButton(text="🆘 پشتیبانی", callback_data=CB_SUPPORT)],
        ]
    )


def back_to_main_menu_button() -> list[InlineKeyboardButton]:
    """یه ردیف تکی برای اضافه‌کردن به پایین هر صفحه‌ی دیگه، برای برگشت به منوی اصلی."""
    return [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data=CB_MAIN_MENU)]
