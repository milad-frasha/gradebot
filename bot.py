import os
import requests
from bs4 import BeautifulSoup
import time

bot_token = os.getenv('BOT_TOKEN')
chat_id = '1311416362' 

msiaf = [821080481, 821080696, 821080725, 821080716, 821080713, 821080823]
row_counts = {user_id: 0 for user_id in msiaf}

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': message}
    requests.post(url, data=payload)

def scrape_user_data(user_id):
    url = f"http://app.hama-univ.edu.sy/StdMark/Student/{user_id}?college=1"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    additional_info = soup.find('span', class_="bottom").text.strip()
    tables = soup.find_all('table')
    last_table = tables[-1] if tables else None
    
    if last_table:
        message = f"الاسم: {additional_info}\n\n"
        for row in last_table.find_all('tr'):
            cells = row.find_all(['th', 'td'])
            if len(cells) >= 2:
                message += f"{cells[0].text.strip():<20} {cells[2].text.strip():<20}\n"
        return message, len(last_table.find_all('tr'))
    return None, 0

def handle_command(command):
    if command.lower() == 'msiaf':
        for friend_id in msiaf:
            message, row_count = scrape_user_data(friend_id)
            if message:
                send_telegram_message(message)
    else:
        try:
            user_id = int(command)
            message, row_count = scrape_user_data(user_id)
            if message:
                send_telegram_message(message)
        except ValueError:
            send_telegram_message("Invalid command. Use `msiaf` or a specific user ID.")

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    params = {'timeout': 100, 'offset': offset}
    response = requests.get(url, params=params)
    return response.json()

def process_updates(updates):
    for update in updates['result']:
        if 'message' in update and 'text' in update['message']:
            text = update['message']['text']
            chat_id = update['message']['chat']['id']
            if text.lower().startswith('/run'):
                command = text.split()[1] if len(text.split()) > 1 else ''
                handle_command(command)
            elif text.lower() == '/msiaf':
                handle_command('msiaf')
        return update['update_id']

def check_for_new_grades():
    for user_id in msiaf:
        _, row_count = scrape_user_data(user_id)
        if row_count > row_counts[user_id]:
            message, _ = scrape_user_data(user_id)
            send_telegram_message(message)
            row_counts[user_id] = row_count

def main():
    offset = None
    while True:
        updates = get_updates(offset)
        if 'result' in updates and updates['result']:
            offset = process_updates(updates) + 1
        check_for_new_grades()
        time.sleep(60)

if __name__ == '__main__':
    main()