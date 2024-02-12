# Gemi Chat Bot

Gemi is a Telegram chat bot that leverages the `gemini-pro` API for text-based message generation and Bing for image generation. It is designed to interact with users by processing text and image inputs and responding appropriately.

## Features

- Text conversation with users using the `gemini-pro` generative model.
- Image generation based on prompts using Bing.
- Search query handling with informative responses.
- PDF and document understanding capabilities.
- Built-in logging and error tracking via Sentry.
- Extendable with middleware and custom route handlers.

## One-Click Deployment
Use the button below to deploy your own Gemi bot on Render.

<a href="https://render.com/deploy?repo=https://github.com/Akash98Sky/gemi-bot/tree/main">
  <img src="https://render.com/images/deploy-to-render-button.svg" alt="Deploy to Render">
</a>

Note: You need a Render account to use this. Or, create your free account [here](https://dashboard.render.com/register).

## Quick Start

To get started with Gemi chat bot, follow these steps:

### Prerequisites

- Python 3.10+
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

# Webhook settings to wake up the bot (optional) - required only if your service spins down while idle (e.g.: Heroku, Render)
APP_HOSTNAME=<your_webhook_host> (e.g.: abc.xyz.com)
WEBHOOK_SECRET=<your_webhook_secret>

# Voice API settings
VOICE_API_URL=<your_voice_api_url>
TTS_VOICE=festival:cmu_us_slt_arctic_hts
STT_ENGINE=vosk
```

### Running the bot
Use gunicorn to launch the application:

```bash
gunicorn main:web_app --bind 0.0.0.0:8080 -k aiohttp.GunicornWebWorker
```

Replace 8080 with the port you want to run your web server on.

### Running the Gemi voice API

If you want to use the Gemi voice API, follow the instructions below:

- Clone the Gemi voice repository.
```bash
git clone https://github.com/Akash98Sky/gemi-voice.git
```
- Install all its dependencies.
```bash
cd gemi-voice && pip install -r requirements.txt
```
- Run the voice API on a different port.
```bash
uvicorn main:app --host 0.0.0.0 --port 2024
```
- Update the gemi-bot .env file with the voice API URL.
```bash
VOICE_API_URL=http://0.0.0.0:2024
TTS_VOICE=edge:en-IN-NeerjaExpressiveNeural
STT_ENGINE=vosk
```

### Webhook on localhost
- Have `ngrok` installed on your local machine. If you don't have it installed, download it from [ngrok's website](https://ngrok.com/) and follow their installation instructions.
- Ensure your local server is ready to receive webhooks.

- Steps

    1. **Start Your Local Server**
    Ensure that your local server is running on a specific port. For example, if you're using a Node.js Express server, it might be running on port 8080.

    2. **Run Ngrok**
    Open a new terminal window and run ngrok to expose your local server to the internet. Replace `8080` with the port number your local server is using.

    ```bash
    ngrok http 8080
    ```

    3. Copy the Ngrok URL Once ngrok is running, it will display a public URL (e.g., https://abc123.ngrok.io). Copy this URL; it will be used as your webhook endpoint.

### Documentation
For more details on how to use and extend the bot, refer to the inline documentation within the code and the official [aiogram](https://docs.aiogram.dev/en/latest/) and [google-generativeai](https://ai.google.dev/tutorials/python_quickstart) libraries documentation.

### Contributing
Contributions are welcome. Please submit pull requests or create issues for any features or fixes.

### License
This project is open-sourced under the MIT License.
