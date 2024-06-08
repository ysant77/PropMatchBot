import os
import telebot
import logging
from .handlers import handle_message, subscribe_handler, property_suggestions_handler, tenant_profile_handler, status_handler

# Configure logging
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ['BOT_TOKEN']
API_URL = os.environ['API_URL']  # Replace with your FastAPI Repl URL

bot = telebot.TeleBot(BOT_TOKEN)

# Helper function to get the user's display name
def get_display_name(user):
    if user.username:
        return user.username
    else:
        return f"{user.first_name} {user.last_name}".strip()

# Start and hello commands
@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    logging.info(f"Received {message.text} command")
    user_name = get_display_name(message.from_user)
    welcome_message = (
        f"Welcome to PropertyMatchBot, {user_name}!\n"
        "I can help you find the best property deals based on your preferences.\n"
        "Use /subscribe to manage your subscription.\n"
        "Use /tenant_profile to create or update your tenant profile.\n"
        "Use /property_suggestions to get property suggestions."
    )
    bot.reply_to(message, welcome_message)

# Register handlers
@bot.message_handler(commands=['subscribe'])
def subscribe(message):
    subscribe_handler(bot, message)

@bot.message_handler(commands=['property_suggestions'])
def property_suggestions(message):
    property_suggestions_handler(bot, message)

@bot.message_handler(commands=['tenant_profile'])
def tenant_profile(message):
    tenant_profile_handler(bot, message)

@bot.message_handler(commands=['status'])
def status(message):
    status_handler(bot, message)

@bot.message_handler(func=lambda msg: True)
def handle_all_messages(message):
    handle_message(bot, message)

bot.infinity_polling()
