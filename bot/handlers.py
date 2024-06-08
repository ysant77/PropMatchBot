import requests
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

API_URL = os.environ['API_URL']  # Replace with your FastAPI Repl URL

def handle_message(bot, message):
    user_id = message.from_user.id
    question = message.text
    logging.info(f"Received unknown command/message: {message.text}")
    bot.reply_to(message, "I'm sorry, I don't understand that command. Please use /start to view all available commands.")

def subscribe_handler(bot, message):
    logging.info(f"Received /subscribe command from user {message.from_user.id}")
    try:
        markup = InlineKeyboardMarkup()
        standard_button = InlineKeyboardButton("Standard - $100/year", callback_data="subscribe_standard")
        premium_button = InlineKeyboardButton("Premium - $200/year", callback_data="subscribe_premium")
        markup.add(standard_button, premium_button)
        bot.send_message(message.chat.id, "Choose your subscription plan:", reply_markup=markup)
    except Exception as e:
        logging.error(f"Error in /subscribe handler: {e}")

def property_suggestions_handler(bot, message):
    logging.info(f"Received /property_suggestions command from user {message.from_user.id}")
    user_id = message.from_user.id

    # Fetch user profile and subscription
    profile_response = requests.get(f"{API_URL}/profile/{user_id}")
    if profile_response.status_code != 200:
        bot.send_message(message.chat.id, "Failed to fetch your profile. Please ensure you have a profile set up.")
        return

    profile = profile_response.json()

    # Fetch property suggestions
    suggestion_response = requests.post(f"{API_URL}/property_suggestions", json={"user_id": user_id, "subscription": profile['subscription']})
    if suggestion_response.status_code == 200:
        suggestions = suggestion_response.json()["suggested_properties"]
        if suggestions:
            suggestion_text = "Here are some properties based on your profile:\n"
            for idx, suggestion in enumerate(suggestions, 1):
                suggestion_text += (
                    f"\n<b>{idx}. Property Name:</b> {suggestion['PropertyName']}\n"
                    f"<b>Type:</b> {suggestion['Type']}\n"
                    f"<b>Price:</b> {suggestion['Price']}\n"
                    f"<b>Bedrooms:</b> {suggestion['Bedrooms']}\n"
                    f"<b>Bathrooms:</b> {suggestion['Bathrooms']}\n"
                    f"<b>Square Feet:</b> {suggestion['Sqft']}\n"
                    f"<b>Author:</b> {suggestion['Author']}\n"
                    f"<b>Move In Date:</b> {suggestion['MoveInDate']}\n"
                    f"<a href='{suggestion['ImageURL']}'>Property Image</a>\n"
                    f"<a href='{suggestion['VirtualTourLink']}'>Virtual Tour</a>\n"
                )
            bot.send_message(message.chat.id, suggestion_text, parse_mode='HTML')
        else:
            bot.send_message(message.chat.id, "No matching properties found.")
    else:
        bot.send_message(message.chat.id, "Failed to fetch property suggestions. Please try again.")
        logging.error(f"Failed to fetch property suggestions: {suggestion_response.text}")

def tenant_profile_handler(bot, message):
    logging.info(f"Received /tenant_profile command from user {message.from_user.id}")
    chat_id = message.chat.id
    profile_template = (
        "Please provide your tenant profile information in the following format:\n"
        "Gender: <Your Gender>\n"
        "Age: <Your Age>\n"
        "Nationality: <Your Nationality>\n"
        "Race: <Your Race>\n"
        "Occupation: <Your Occupation>\n"
        "Type of work pass: <Your Work Pass>\n"
        "Moving in date: <Your Moving In Date>\n"
        "Length of stay: <Your Length of Stay>\n"
        "Budget: <Your Budget>"
    )
    bot.send_message(chat_id, profile_template)
    msg = bot.send_message(chat_id, "Please enter your profile information:")
    bot.register_next_step_handler(msg, process_tenant_profile)

def process_tenant_profile(bot, message):
    user_id = message.from_user.id
    profile_text = message.text

    # Parse the profile text
    profile_lines = profile_text.split('\n')
    profile = {}
    for line in profile_lines:
        key, value = line.split(': ', 1)
        profile[key.strip().lower().replace(' ', '_')] = value.strip()

    # Ensure all required fields are present
    required_fields = ['gender', 'age', 'nationality', 'race', 'occupation', 'type_of_work_pass', 'moving_in_date', 'length_of_stay', 'budget']
    if not all(field in profile for field in required_fields):
        bot.send_message(message.chat.id, "Some fields are missing or incorrectly formatted. Please try again using the format provided.")
        return

    profile['user_id'] = user_id

    # Send profile to backend
    response = requests.post(f"{API_URL}/tenant_profile", json=profile)
    if response.status_code == 200:
        bot.send_message(message.chat.id, "Tenant profile updated successfully!")
    else:
        bot.send_message(message.chat.id, "Failed to update tenant profile. Please try again.")
        logging.error(f"Failed to update tenant profile: {response.text}")

def status_handler(bot, message):
    logging.info(f"Received /status command from user {message.from_user.id}")
    try:
        user_id = message.from_user.id
        response = requests.get(f"{API_URL}/profile/{user_id}")
        if response.status_code == 200:
            profile = response.json()
            display_subscription_status(bot, user_id, profile)
        else:
            bot.send_message(message.chat.id, "Failed to fetch your subscription status. Please try again.")
            logging.error(f"Failed to fetch profile: {response.text}")
    except Exception as e:
        logging.error(f"Error in status_handler: {e}")

def display_subscription_status(bot, user_id, profile):
    try:
        markup = InlineKeyboardMarkup()
        subscription_status = f"Your current subscription level: *{profile['subscription'].capitalize()}*"
        if profile['subscription'] == "premium":
            text = f"{subscription_status}\n\nYou have the highest subscription level."
            cancel_button = InlineKeyboardButton("Cancel Subscription", callback_data="cancel_subscription")
            markup.add(cancel_button)
        else:
            text = f"{subscription_status}\n\nWould you like to update your subscription or cancel it?"
            update_button = InlineKeyboardButton("Update Subscription", callback_data="update_subscription")
            cancel_button = InlineKeyboardButton("Cancel Subscription", callback_data="cancel_subscription")
            markup.add(update_button, cancel_button)

        bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error in display_subscription_status: {e}")
