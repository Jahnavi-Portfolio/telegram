# Custom Telegram AI Personal Assistant

This is a powerful, self-hosted Telegram bot that acts as a personalized AI assistant. It integrates deeply with your Google Workspace account and uses OpenAI's Assistants API to perform complex, multi-step tasks.

## Features

- **Deep Google Workspace Integration**: Connects to your Google Calendar, Gmail, Drive, Docs, and Sheets.
- **Autonomous Task Execution**: Powered by OpenAI's GPT-4o and the Assistants API, the bot can understand complex commands, break them down into steps, and execute them.
- **Multi-Tool Capability**: Can browse websites, generate DOCX and PDF reports, create folders in Google Drive, and upload files.
- **Background Task Processing**: Uses Redis and RQ (Redis Queue) to handle long-running tasks without blocking the bot, providing real-time progress updates in Telegram.
- **Secure OAuth 2.0 Flow**: Securely authenticates with your Google account using the standard OAuth 2.0 protocol, storing refresh tokens to maintain access without re-prompting.
- **Flexible & Deployable**: Supports local development (with or without Docker) and one-click deployment to platforms like Railway using Docker.

## Architecture

- **Bot Framework**: `python-telegram-bot` (v20+)
- **Web Server**: `FastAPI` (for handling Telegram webhooks)
- **AI Backend**: `openai` (Assistants API v2)
- **Task Queue**: `rq` (Redis Queue)
- **Containerization**: `Docker`
- **Hosting**: Designed for Railway, Render, or any container-based platform.

## 1. Initial Setup (Do this first)

### 1.1. Get Credentials

You need to gather several secrets before you can run the application.

1.  **Telegram Bot Token**: Get one from [@BotFather](https://t.me/botfather) on Telegram.
2.  **OpenAI API Key**: Get one from the [OpenAI Platform](https://platform.openai.com/api-keys).
3.  **Google Cloud Credentials**:
    -   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    -   Create a new project.
    -   Enable the **Google Drive API**, **Google Docs API**, **Google Sheets API**, **Gmail API**, and **Google Calendar API**.
    -   Go to "APIs & Services" -> "OAuth consent screen". Configure it for "External" users and add your own Google account as a test user. Add all the scopes listed in `utils/auth.py`.
    -   Go to "Credentials", click "Create Credentials" -> "OAuth client ID". Select "Web application".
    -   Under "Authorized redirect URIs", add `urn:ietf:wg:oauth:2.0:oob`.
    -   Create the client ID. A modal will appear with your **Client ID** and **Client Secret**. You will also get your **Project ID** from the project dashboard.
4.  **Create an OpenAI Assistant**:
    -   Go to the [OpenAI Platform Assistants page](https://platform.openai.com/assistants).
    -   Create a new Assistant, name it, and set the model to `gpt-4o`.
    -   For instructions, use a prompt like: `You are a world-class personal assistant integrated with a user's Google Workspace and other tools. When given a task, break it down into logical steps and use the available functions to execute it.`
    -   Under **Tools**, add Function tools. For each function in the `tools/` directory (e.g., `browse_website`), you need to provide its JSON schema. Example for `browse_website`:
        ```json
        {
          "name": "browse_website",
          "description": "Fetches the content of a given URL and returns the clean text.",
          "parameters": {
            "type": "object",
            "properties": { "url": { "type": "string", "description": "The URL of the website to browse." } },
            "required": ["url"]
          }
        }
        ```
    -   Save the Assistant and copy its **Assistant ID**.

### 1.2. Configure Environment

Copy `.env.example` to a new file named `.env` and fill in all the values you just gathered.

```bash
cp .env.example .env
# Open .env and add your secrets
```

## 2. Running the Application

Choose one of the following methods.

### Method A: Local Development (No Docker)

This is the fastest way to get started locally.

**Prerequisites**:
- Python 3.10+
- PowerShell (for the startup script)
- `ngrok` for exposing your local server.

**Steps**:
1.  **Start ngrok** in a separate terminal to get a public URL for your local server.
    ```bash
    ngrok http 8000
    ```
2.  Copy the `https://` URL provided by ngrok and set it as your `WEBHOOK_URL` in the `.env` file.
3.  **Run the startup script**. It will handle creating a virtual environment, installing dependencies, checking for Redis, and starting the required processes.
    ```powershell
    ./start-local.ps1
    ```
    If you get a script execution error on Windows, you may need to run this command in your PowerShell session first: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`

### Method B: Local Development (With Docker)

This method is more isolated and mirrors the production deployment environment.

**Prerequisites**:
- Docker and Docker Compose.
- `ngrok`.

**Steps**:
1.  **Start ngrok** and update your `WEBHOOK_URL` in `.env` as described in Method A.
2.  **Add `docker-compose.yml`**: Create a file named `docker-compose.yml` with the following content:
    ```yaml
    version: '3.8'
    services:
      redis:
        image: redis:alpine
        ports:
          - "6379:6379"

      app:
        build: .
        command: uvicorn main:app --host 0.0.0.0 --port 8000
        volumes:
          - .:/app
        ports:
          - "8000:8000"
        depends_on:
          - redis
        env_file: .env

      worker:
        build: .
        command: rq worker -u $$REDIS_URL default
        volumes:
          - .:/app
        depends_on:
          - redis
        env_file: .env
    ```
3.  **Run Docker Compose**:
    ```bash
    docker-compose up --build
    ```
    This will build the Docker image and start the `redis`, `app` (web server), and `worker` services all at once.

### Method C: Deploying to Railway

1.  **Push your code** to a GitHub repository.
2.  **Create a new Project** on Railway and link it to your GitHub repo. Railway will automatically detect the `Dockerfile`.
3.  **Add a Redis service** to your project. Railway will provide the `REDIS_URL`.
4.  Go to your bot service's "Variables" tab and **add all the secrets** from your `.env` file. Set the `WEBHOOK_URL` to the public URL Railway provides for the service.
5.  Go to the "Deployments" tab and ensure the deployment is using the `Procfile`. If not, you may need to specify the start commands manually. The `Procfile` should be detected automatically.
6.  Railway will build the Docker image and deploy both the `web` and `worker` processes as defined in the `Procfile`. Monitor the logs for any errors.
