# PropertyMatchBot

## Overview
PropertyMatchBot is a Telegram bot integrated with a FastAPI backend to provide personalized property recommendations based on user profiles and preferences. The bot also handles subscriptions, tenant profiles, and property suggestions.

## Project Structure
```
PropMatchBot/
│
├── requirements.txt
│
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── utils.py
│
├── bot/
│   ├── __init__.py
│   ├── bot.py
│   └── handlers.py
│
├── .env
└── README.md
```


## Setup

1. Clone the repository:
    ```sh
    git clone https://github.com/ysant77/PropMatchBot
    cd PropMatchBot
    ```

2. Create and activate a virtual environment:
    ```sh
    python3 -m venv env
    source env/bin/activate  # On Windows use `env\Scripts\activate`
    ```

3. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Set up environment variables:
    - Create a `.env` file in the project root directory with your configuration details.

5. Run the FastAPI backend:
    ```sh
    cd backend
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```

6. Run the Telegram bot:
    ```sh
    cd ../bot
    python bot.py
    ```

## Usage

- Interact with the bot on Telegram by sending commands such as `/start`, `/subscribe`, `/tenant_profile`, and `/property_suggestions`.

## Notes

- Ensure your environment variables are correctly set in the `.env` file.
- For local testing, you can run the FastAPI server and Telegram bot on your machine and interact with the bot via Telegram.

