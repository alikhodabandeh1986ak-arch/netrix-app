"""
نقطه‌ی شروع ربات.

اجرای لوکال (تست توی VS Code):
    RUN_MODE=polling در .env بذار و فقط اجرا کن:
    python main.py

اجرای روی رندر:
    RUN_MODE=webhook و WEBHOOK_BASE_URL (آدرس سرویس رندرت) رو ست کن.
    رندر خودش دستور استارت رو با همین فایل صدا می‌زنه.
"""
import asyncio
import logging

from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from bot import bot, dp
from config import settings
from database.db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("netrix")


async def _on_startup_common():
    await init_db()
    logger.info("دیتابیس آماده‌ست.")


async def run_polling():
    await _on_startup_common()
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("ربات با حالت polling اجرا شد (مناسب تست لوکال).")
    await dp.start_polling(bot)


async def health_check(request: web.Request) -> web.Response:
    # همین endpoint رو توی UptimeRobot / cron-job.org پینگ می‌کنیم تا سرویس نخوابه
    return web.json_response({"status": "ok"})


def run_webhook():
    app = web.Application()
    app.router.add_get("/health", health_check)

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.WEBHOOK_SECRET,
    ).register(app, path=settings.WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    async def _startup(app: web.Application):
        await _on_startup_common()
        webhook_url = settings.WEBHOOK_BASE_URL.rstrip("/") + settings.WEBHOOK_PATH
        await bot.set_webhook(
            url=webhook_url,
            secret_token=settings.WEBHOOK_SECRET,
            drop_pending_updates=True,
        )
        logger.info("Webhook ست شد روی: %s", webhook_url)

    app.on_startup.append(_startup)
    web.run_app(app, host="0.0.0.0", port=settings.PORT)


if __name__ == "__main__":
    if settings.RUN_MODE == "webhook":
        run_webhook()
    else:
        asyncio.run(run_polling())
