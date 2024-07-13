import os
import requests
from bs4 import BeautifulSoup
import time

# Read the Telegram bot token from environment variables
bot_token = os.getenv('BOT_TOKEN')
chat_id = '1311416362'  # Replace with your actual chat ID

# List of msiaf IDs
msiaf = [821080481, 821080696, 821080725, 821080716, 821080713, 821080823]

# Dictionary to store the last row count for each user ID
row_counts = {user_id: 0 for user_id in msiaf}

# Function to send a message to Telegram
def send_telegram_message(chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': message}
    response = requests.post(url, data=payload)
    response.raise_for_status()

# Function to scrape data for a specific user ID and get the row count
def scrape_user_data(user_id):
    url = f"http://app.hama-univ.edu.sy/StdMark/Student/{user_id}?college=1"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    additional_info = soup.find('span', class_="bottom").text.strip()
    tables = soup.find_all('table')
    last_table = tables[-1] if tables else None

    if last_table:
        row_count = 0
        message = f"الاسم: {additional_info}\n\n"
        for row in last_table.find_all('tr'):
            cells = row.find_all(['th', 'td'])
            if len(cells) >= 2:
                message += "{:<20} {:<20}\n".format(cells[0].text.strip(), cells[2].text.strip())
                row_count += 1
        send_telegram_message(chat_id, message)
        return row_count
    else:
        send_telegram_message(chat_id, f"No tables found on the page for user {user_id}.")
        return 0

# Function to handle commands
def handle_command(chat_id, command):
    if command.lower() == 'msiaf':
        for friend_id in msiaf:
            row_count = scrape_user_data(friend_id)
            send_telegram_message(chat_id, f"User ID {friend_id} has {row_count} rows in the last table.")
    else:
        try:
            user_id = int(command)
            row_count = scrape_user_data(user_id)
            send_telegram_message(chat_id, f"User ID {user_id} has {row_count} rows in the last table.")
        except ValueError:
            send_telegram_message(chat_id, "Invalid command. Use `msiaf` or a specific user ID.")

# Function to get updates from Telegram
def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    params = {'timeout': 100, 'offset': offset}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

# Function to process updates
def process_updates(updates):
    for update in updates['result']:
        if 'message' in update and 'text' in update['message']:
            text = update['message']['text']
            chat_id = update['message']['chat']['id']
            if text.lower().startswith('/run'):
                try:
                    command = text.split()[1]
                    handle_command(chat_id, command)
                except IndexError:
                    send_telegram_message(chat_id, "Please provide a valid /run command.")
            elif text.lower() == '/msiaf':
                handle_command(chat_id, 'msiaf')
        return update['update_id']

# Function to check for new grades and notify
def check_for_new_grades():
    for user_id in msiaf:
        row_count = scrape_user_data(user_id)
        if row_count > row_counts[user_id]:
            # New grades detected
            message = f"New grades detected for user {user_id}."
            send_telegram_message(chat_id, message)
            row_counts[user_id] = row_count

# Main function to poll for updates and check for new grades
def main():
    offset = None
    while True:
        updates = get_updates(offset)
        if 'result' in updates and updates['result']:
            offset = process_updates(updates) + 1
        check_for_new_grades()
        time.sleep(300)  # Wait for 5 minutes

if __name__ == '__main__':
    main()