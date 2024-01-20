import logging
import sys
from aiohttp.web import Application, run_app
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from os import getenv

from containers import BotContainer, Configs
from api.routes import routes

# Path to webhook route, on which Telegram will send requests
# Also set this as a public path as Telegram servers will request it
WEBHOOK_PATH = "/tg_webhook"

def debugger_is_active() -> bool:
    """Return if the debugger is currently active"""
    return hasattr(sys, 'gettrace') and sys.gettrace() is not None

def log_integration():
    logging.basicConfig(level=logging.DEBUG if debugger_is_active() else logging.INFO)
    sentry_dsn = getenv("SENTRY_DSN", "")
    if not debugger_is_active() and len(sentry_dsn) > 0:
        logging.info("Setting up Sentry")        
        sentry_sdk.init(
            dsn=sentry_dsn,
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            traces_sample_rate=1.0,
            # Set profiles_sample_rate to 1.0 to profile 100%
            # of sampled transactions.
            # We recommend adjusting this value in production.
            profiles_sample_rate=0.3,
            environment=getenv('ENV', 'dev'),
            integrations=[
                LoggingIntegration(
                    level=logging.INFO,        # Capture info and above as breadcrumbs
                    event_level=logging.WARNING,   # Send records as events
                )
            ]
        )

def init_bot(app: Application):
    configs = Configs
    # Bot token can be obtained via https://t.me/BotFather
    configs.bot_config.token.from_env("BOT_TOKEN", required=True)
    # Base URL for webhook will be used to generate webhook URL for Telegram
    configs.bot_config.webhook_host.from_env("APP_HOSTNAME", required=True)
    # Secret key to validate requests from Telegram (optional)
    configs.bot_config.webhook_secret.from_env("WEBHOOK_SECRET", default='')

    # API key can be obtained via https://platform.openai.com/account/api-keys
    configs.chat_config.api_key.from_env("GOOGLE_API_KEY", required=True)
    # Bing cookie for using Bing image search
    configs.chat_config.bing_cookie.from_env("BING_COOKIE")
    # Voice API URL
    configs.chat_config.voice_api_url.from_env("VOICE_API_URL")
    # Voice engine
    configs.chat_config.tts_voice.from_env("TTS_VOICE", default="flite:cmu_us_slt")
    # Proxy URL
    configs.chat_config.proxy_url.from_env("PROXY_URL")

    BotContainer.tg_bot().register_webhook_handler(app, WEBHOOK_PATH)

    # This will start the voice engine and bring it up
    BotContainer.voice_engine()

async def web_app():
    log_integration()

    app = Application()
    init_bot(app)
    app.router.add_routes(routes)

    return app


if __name__ == "__main__":
    run_app(web_app(), port=8080, host="0.0.0.0")