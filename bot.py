import os
import requests
import telebot
from bs4 import BeautifulSoup
import threading
import time

# Read the Telegram bot token from environment variables
bot_token = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(bot_token)

# Chat IDs to send notifications to
notification_chat_id = 1311416362
group_chat_id = -1002160075956

# List of msiaf IDs
msiaf = [821080481, 821080696, 821080725, 821080716, 821080713, 821080823]

# Initialize the grade count variable
grade_count = 0

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

# Function to scrape grades and return the count and data
def scrape_grades():
    url = f"http://app.hama-univ.edu.sy/StdMark/Student/{msiaf[0]}?college=1"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    grades_data = []
    for tr in soup.find_all('tr', class_='bg-light'):
        td_elements = tr.find_all('td')
        subject_name = td_elements[0].get_text(strip=True)
        grade = td_elements[2].get_text(strip=True)
        term = td_elements[1].get_text(strip=True)
        grades_data.append((subject_name, grade, term))

    return len(grades_data), grades_data

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

# Function to handle msiaf notifications
def notify_msiaf():
    for friend_id in msiaf:
        response_message = scrape_user_data(friend_id)
        bot.send_message(notification_chat_id, response_message)
        bot.send_message(group_chat_id, response_message)

# Background function to check for new grades periodically
def check_for_new_grades():
    global grade_count
    while True:
        current_grade_count, _ = scrape_grades()
        if current_grade_count > grade_count:
            notify_msiaf()  # Trigger msiaf command in both chats
            grade_count = current_grade_count
        time.sleep(2 * 60)  # Check every 2 minutes

# Function to start bot polling
def bot_polling():
    bot.polling()

# Start bot polling in a separate thread
bot_thread = threading.Thread(target=bot_polling)
bot_thread.start()

# Initialize grade count on startup
grade_count, _ = scrape_grades()

# Start the background grade checking
check_thread = threading.Thread(target=check_for_new_grades)
check_thread.start()