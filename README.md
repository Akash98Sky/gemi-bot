# Gemi Chat Bot

Gemi is a Telegram chat bot that leverages the `gemini-pro` API for text-based message generation and Bing for image generation. It is designed to interact with users by processing text and image inputs and responding appropriately.

## Features

- Text conversation with users using the `gemini-pro` generative model.
- Image generation based on prompts using Bing.
- Search query handling with informative responses.
- PDF and document understanding capabilities.
- Built-in logging and error tracking via Sentry.
- Extendable with middleware and custom route handlers.

## Quick Start

To get started with Gemi chat bot, follow these steps:

### Prerequisites

- Python 3.8+
- A Telegram bot token from [BotFather](https://t.me/BotFather)
- API keys for `gemini-pro` from [here](https://makersuite.google.com/app/apikey)
- Auth cookies of `Bing AI` from [here](https://github.com/Integration-Automation/ReEdgeGPT?tab=readme-ov-file#getting-authentication), used for image generation (optional)
- A configured webhook host. For localhost, follow [this](#webhook-on-localhost). (optional)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/Akash98Sky/gemi-chat-bot.git
cd gemi-chat-bot
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Configuration

Create a .env file at the root of the project directory with the following environment variables:
```
BOT_TOKEN=<your_telegram_bot_token>
GOOGLE_API_KEY=<your_gemini_pro_api_key>
BING_COOKIE=<your_bing_auth_cookie>
APP_HOSTNAME=<your_webhook_host> (e.g.: abc.xyz.com)
WEBHOOK_SECRET=<your_webhook_secret> (optional)
```

### Running the bot
Use gunicorn to launch the application:

```bash
gunicorn main:web_app --bind 0.0.0.0:8080 -k aiohttp.GunicornWebWorker
```

Replace 8080 with the port you want to run your web server on.

### Webhook on localhost
- Have `ngrok` installed on your local machine. If you don't have it installed, download it from [ngrok's website](https://ngrok.com/) and follow their installation instructions.
- Ensure your local server is ready to receive webhooks.

- Steps

    1. **Start Your Local Server**
    Ensure that your local server is running on a specific port. For example, if you're using a Node.js Express server, it might be running on port 3000.

    2. **Run Ngrok**
    Open a new terminal window and run ngrok to expose your local server to the internet. Replace `8080` with the port number your local server is using.

    ```bash
    ngrok http 3000
    ```

    3. Copy the Ngrok URL Once ngrok is running, it will display a public URL (e.g., https://abc123.ngrok.io). Copy this URL; it will be used as your webhook endpoint.

### Documentation
For more details on how to use and extend the bot, refer to the inline documentation within the code and the official [aiogram](https://docs.aiogram.dev/en/latest/) and [google-generativeai](https://ai.google.dev/tutorials/python_quickstart) libraries documentation.

### Contributing
Contributions are welcome. Please submit pull requests or create issues for any features or fixes.

### License
This project is open-sourced under the MIT License.
