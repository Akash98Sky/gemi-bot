import logging
from os import getenv
from os.path import exists
import sys
from aiohttp.web import Application, run_app

from containers import BotContainer, Configs
from api.routes import routes

# if exists(".env"):
#     from dotenv import load_dotenv
#     # Load .env file if it exists
#     load_dotenv(".env")
#     api_reload = True
#     logging.info("Loaded local .env file")

# Path to webhook route, on which Telegram will send requests
# Also set this as a public path as Telegram servers will request it
WEBHOOK_PATH = "/tg_webhook"

async def on_startup(app: Application):
    logging.info("Starting bot...")
    # If you have a self-signed SSL certificate, then you will need to send a public
    # certificate to Telegram
    await BotContainer.tg_bot().set_webhook()

async def on_shutdown(app: Application):
    logging.info("Shutting down bot...")

def init_bot(app: Application):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    configs = Configs
    # Bot token can be obtained via https://t.me/BotFather
    configs.bot_config.token.from_env("BOT_TOKEN", required=True)
    # Base URL for webhook will be used to generate webhook URL for Telegram
    configs.bot_config.webhook_host.from_env("DETA_SPACE_APP_HOSTNAME", required=True)
    # Secret key to validate requests from Telegram (optional)
    configs.bot_config.webhook_secret.from_env("WEBHOOK_SECRET", default='')

    # API key can be obtained via https://platform.openai.com/account/api-keys
    configs.chat_config.api_key.from_env("GOOGLE_API_KEY", required=True)

    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = BotContainer.tg_bot()

    # Register webhook handler on application
    bot.register_webhook_handler(app, WEBHOOK_PATH)


async def web_app():
    app = Application()

    init_bot(app)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    app.router.add_routes(routes)

    return app


if __name__ == "__main__":
    run_app(web_app(), port=8080, host="0.0.0.0")