import asyncio
import logging
import sys
from os.path import exists

from containers import BotContainer, Configs
from api.app import app as api

if exists(".env"):
    from dotenv import load_dotenv
    # Load .env file if it exists
    load_dotenv(".env")
    logging.info("Loaded local .env file")

@api.on_event("startup")
async def on_server_startup():
    configs = Configs

    # API key can be obtained via https://platform.openai.com/account/api-keys
    configs.chat_config.api_key.from_env("GOOGLE_API_KEY", required=True)

async def main():
    logging.info("Starting bot...")
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = BotContainer.tg_bot()
    # And the run events dispatching
    await bot.start_polling()

if __name__ == "__main__":
    configs = Configs
    # Bot token can be obtained via https://t.me/BotFather
    configs.bot_config.token.from_env("BOT_TOKEN", required=True)

    # API key can be obtained via https://platform.openai.com/account/api-keys
    configs.chat_config.api_key.from_env("GOOGLE_API_KEY", required=True)

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())