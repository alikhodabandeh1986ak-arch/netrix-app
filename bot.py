from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from admin import deposit_review, panel_menu, pricing
from config import settings
from handlers import start
from handlers.buy_subscription import category_select, confirm_purchase, duration_select
from handlers.menu import my_subscriptions, navigation, support
from handlers.wallet import balance, charge_wallet
from middlewares.channel_gate import ChannelGateMiddleware

bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

# نکته: MemoryStorage یعنی وضعیت مکالمه‌ها (FSM) با هر ری‌استارت ربات پاک میشه.
# برای شروع کار کاملا کافیه؛ وقتی کاربر زیاد شد و روی رندر چند بار ری‌استارت
# اتفاق افتاد، می‌تونیم به RedisStorage آپگرید کنیم بدون تغییر توی هندلرها.
dp = Dispatcher(storage=MemoryStorage())

dp.message.middleware(ChannelGateMiddleware())
dp.callback_query.middleware(ChannelGateMiddleware())

# ترتیب مهمه: هندلرهای خاص‌تر (مثل ادمین) رو زودتر ثبت می‌کنیم
routers = [
    panel_menu.router,
    pricing.router,
    deposit_review.router,
    start.router,
    navigation.router,
    category_select.router,
    duration_select.router,
    confirm_purchase.router,
    balance.router,
    charge_wallet.router,
    my_subscriptions.router,
    support.router,
]

for r in routers:
    dp.include_router(r)
