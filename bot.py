import os
import requests
from bs4 import BeautifulSoup
import time

# Read the Telegram bot token from environment variables
bot_token = os.getenv('BOT_TOKEN')

# List of msiaf IDs
msiaf = [821080481, 821080696, 821080725, 821080716, 821080713, 821080823]

# Chat ID
chat_id = 1311416362

# Variable to store the number of rows (grades) of the last table for the last ID in msiaf
x = 0

# Function to send message to Telegram
def send_telegram_message(chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': message}
    response = requests.post(url, data=payload)
    response.raise_for_status()

# Function to scrape data for a specific user ID
def scrape_user_data(chat_id, user_id):
    url = f"http://app.hama-univ.edu.sy/StdMark/Student/{user_id}?college=1"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    additional_info = soup.find('span', class_="bottom").text.strip()
    tables = soup.find_all('table')
    last_table = tables[-1] if tables else None

    if last_table:
        message = f"الاسم: {additional_info}\n\n"
        for row in last_table.find_all('tr'):
            cells = row.find_all(['th', 'td'])
            if len(cells) >= 2:
                message += "{:<20} {:<20}\n".format(cells[0].text.strip(), cells[2].text.strip())
        send_telegram_message(chat_id, message)
    else:
        send_telegram_message(chat_id, f"No tables found on the page for user {user_id}.")

# Function to handle commands
def handle_command(chat_id, command):
    if command.lower() == 'msiaf':
        for friend_id in msiaf:
            scrape_user_data(chat_id, friend_id)
    else:
        try:
            user_id = int(command)
            scrape_user_data(chat_id, user_id)
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

# Function to get the number of rows in the last table for a specific user ID
def get_last_table_row_count(user_id):
    url = f"http://app.hama-univ.edu.sy/StdMark/Student/{user_id}?college=1"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    tables = soup.find_all('table')
    last_table = tables[-1] if tables else None

    if last_table:
        return len(last_table.find_all('tr'))
    return 0

# Main function to poll for updates
def main():
    global x
    x = get_last_table_row_count(msiaf[-1])

    while True:
        current_row_count = get_last_table_row_count(msiaf[-1])
        if x > 0 and current_row_count > x:
            x = current_row_count
            handle_command(chat_id, 'msiaf')
        time.sleep(60)  # Wait for 1 minute before checking again

if __name__ == '__main__':
    main()