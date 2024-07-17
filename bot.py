import os
import telebot
import requests
from bs4 import BeautifulSoup

# Read the Telegram bot token from environment variables
bot_token = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(bot_token)

# List of msiaf IDs
msiaf = [821080481, 821080696, 821080725, 821080716, 821080713, 821080823]

# Function to scrape data for a specific user ID
def scrape_user_data(user_id):
    url = f"http://app.hama-univ.edu.sy/StdMark/Student/{user_id}?college=1"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    additional_info_tag = soup.find('span', class_="bottom")
    if not additional_info_tag:
        return f"No student information found for user {user_id}."

    additional_info = additional_info_tag.text.strip()
    tables = soup.find_all('table')
    last_table = tables[-1] if tables else None

    if last_table:
        message = f"الاسم: {additional_info}\n\n"
        for row in last_table.find_all('tr'):
            cells = row.find_all(['th', 'td'])
            if len(cells) >= 2:
                message += "{:<20} {:<20}\n".format(cells[0].text.strip(), cells[2].text.strip())
        return message
    else:
        return f"No tables found on the page for user {user_id}."

# Command handler for /run and /msiaf commands
@bot.message_handler(commands=['run'])
def handle_run_command(message):
    try:
        command = message.text.split()[1]
        if command.lower() == 'msiaf':
            for friend_id in msiaf:
                response_message = scrape_user_data(friend_id)
                bot.send_message(message.chat.id, response_message)
        else:
            user_id = int(command)
            response_message = scrape_user_data(user_id)
            bot.send_message(message.chat.id, response_message)
    except IndexError:
        bot.send_message(message.chat.id, "Please provide a valid /run command.")
    except ValueError:
        bot.send_message(message.chat.id, "Invalid command. Use `msiaf` or a specific user ID.")

@bot.message_handler(commands=['msiaf'])
def handle_msiaf_command(message):
    for friend_id in msiaf:
        response_message = scrape_user_data(friend_id)
        bot.send_message(message.chat.id, response_message)

# Start polling for updates
bot.polling()