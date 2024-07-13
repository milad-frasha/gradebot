import os
import requests
from bs4 import BeautifulSoup
import sqlite3

# Read the Telegram bot token from environment variables
bot_token = os.getenv('BOT_TOKEN')

# List of msiaf IDs
msiaf = [821080481, 821080696, 821080725, 821080716, 821080713, 821080823]

# Initialize the SQLite database
conn = sqlite3.connect('row_count.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS row_counts (
                 id INTEGER PRIMARY KEY,
                 user_id INTEGER,
                 row_count INTEGER
             )''')
conn.commit()

# Function to send message to Telegram
def send_telegram_message(chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': message}
    print(f"Sending message to chat_id: {chat_id}")
    print(f"Message: {message}")
    response = requests.post(url, data=payload)
    print(f"Response: {response.status_code}, {response.text}")
    response.raise_for_status()

# Function to scrape data for a specific user ID
def scrape_user_data(chat_id, user_id):
    url = f"http://app.hama-univ.edu.sy/StdMark/Student/{user_id}?college=1"
    print(f"Scraping URL: {url}")
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    additional_info = soup.find('span', class_="bottom").text.strip()
    tables = soup.find_all('table')
    last_table = tables[-1] if tables else None

    if last_table:
        message = f"الاسم: {additional_info}\n\n"
        row_count = 0
        for row in last_table.find_all('tr'):
            cells = row.find_all(['th', 'td'])
            if len(cells) >= 2:
                message += "{:<20} {:<20}\n".format(cells[0].text.strip(), cells[2].text.strip())
                row_count += 1
        send_telegram_message(chat_id, message)
        
        # Update the row count in the database
        c.execute('''INSERT OR REPLACE INTO row_counts (user_id, row_count)
                     VALUES ((SELECT user_id FROM row_counts WHERE user_id = ?), ?)''',
                  (user_id, row_count))
        conn.commit()
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
    print(f"Updates response: {response.status_code}, {response.text}")
    response.raise_for_status()
    return response.json()

# Function to process updates
def process_updates(updates):
    for update in updates['result']:
        if 'message' in update and 'text' in update['message']:
            text = update['message']['text']
            chat_id = update['message']['chat']['id']
            print(f"Received message: {text} from chat_id: {chat_id}")
            if text.lower().startswith('/run'):
                try:
                    command = text.split()[1]
                    handle_command(chat_id, command)
                except IndexError:
                    send_telegram_message(chat_id, "Please provide a valid /run command.")
            elif text.lower() == '/msiaf':
                handle_command(chat_id, 'msiaf')
        return update['update_id']

# Main function to poll for updates
def main():
    offset = None
    while True:
        updates = get_updates(offset)
        if 'result' in updates and updates['result']:
            offset = process_updates(updates) + 1

if __name__ == '__main__':
    main()