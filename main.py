import asyncio
import logging
import sys
from aiohttp.web import Application, run_app
from bot.bot import TgBot
from bot.enums import BotEventMethods

from containers import BotContainer, Configs
from api.routes import routes

# Path to webhook route, on which Telegram will send requests
# Also set this as a public path as Telegram servers will request it
WEBHOOK_PATH = "/tg_webhook"

def debugger_is_active() -> bool:
    """Return if the debugger is currently active"""
    return hasattr(sys, 'gettrace') and sys.gettrace() is not None

# async def start_bot(bot: TgBot):
#     logging.info("Starting up bot...")
#     await bot.delete_webhook()
#     asyncio.create_task(bot.start_polling())

# async def on_startup(_):
#     bot = BotContainer.tg_bot()
    
#     if bot.method != BotEventMethods.polling:
#         await start_bot(bot)

# async def on_shutdown(_):
#     logging.info("Shutting down bot...")
    
#     bot = BotContainer.tg_bot()
#     # stop polling
#     if bot.method == BotEventMethods.polling:
#         await bot.stop_polling()
#     # set webhook on app shutdown
#     bot.webhook_path = WEBHOOK_PATH
#     await bot.set_webhook()

def init_bot(app: Application):
    logging.basicConfig(level=logging.DEBUG if debugger_is_active() else logging.INFO, stream=sys.stdout)
    
    configs = Configs
    # Bot token can be obtained via https://t.me/BotFather
    configs.bot_config.token.from_env("BOT_TOKEN", required=True)
    # Base URL for webhook will be used to generate webhook URL for Telegram
    configs.bot_config.webhook_host.from_env("DETA_SPACE_APP_HOSTNAME", required=True)
    # Secret key to validate requests from Telegram (optional)
    configs.bot_config.webhook_secret.from_env("WEBHOOK_SECRET", default='')

    # API key can be obtained via https://platform.openai.com/account/api-keys
    configs.chat_config.api_key.from_env("GOOGLE_API_KEY", required=True)

    BotContainer.tg_bot().register_webhook_handler(app, WEBHOOK_PATH)

async def web_app():
    app = Application()

    init_bot(app)
    app.router.add_routes(routes)

    return app


if __name__ == "__main__":
    run_app(web_app(), port=8080, host="0.0.0.0")