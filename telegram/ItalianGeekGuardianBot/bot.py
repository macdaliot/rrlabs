#!/usr/bin/env python3

import datetime, logging, os, requests, sqlite3, sys, time, yaml

# Configure logging
logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.ERROR)
urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.ERROR)

def deleteMessage(chat_id, message_id):
    # Delete a message
    # https://core.telegram.org/bots/api#deletemessage
    response = requests.get(api_url + 'deleteMessage?chat_id={}&message_id={}'.format(chat_id, message_id))
    if response.status_code == 400:
        # message not found or bot is not an administrator
        response_2 = requests.get(api_url + 'getMessage?chat_id={}&message_id={}'.format(chat_id, message_id))
        if response_2.status_code == 404:
            logging.warning('message "{}" is already been deleted'.format(message_id))
            return True
        else:
            logger.error('Telegram API failed with code "{}"'.format(response.status_code))
            logger.debug(response.text)
            return False
    elif response.status_code != 200:
        logger.error('Telegram API failed with code "{}"'.format(response.status_code))
        logger.debug(response.text)
        return False
    try:
        response_json = response.json()
    except Exception as err:
        logger.error('response is not a valid JSON', exc_info = debug)
        logger.debug(response.text)
        return False
    if not response_json['ok']:
        logger.error('Telegram API failed "{}"'.format(response_json))
        logger.debug(response.text)
        return False
    return True

def getChatMember(chat_id, user_id):
    # Get a chat member
    # https://core.telegram.org/bots/api#getchatmember
    logging.debug('getting user "{}"'.format(user_id))
    response = requests.get(api_url + 'getChatMember?chat_id={}&user_id={}'.format(chat_id, user_id))
    if response.status_code != 200:
        logger.error('Telegram API failed with code "{}"'.format(response.status_code))
        logger.debug(response.text)
        sys.exit(1)
    try:
        response_json = response.json()
    except Exception as err:
        logger.error('response is not a valid JSON', exc_info = debug)
        logger.debug(response.text)
        sys.exit(1)
    if not response_json['ok']:
        logger.error('Telegram API failed "{}"'.format(response_json))
        logger.debug(response.text)
        sys.exit(1)
    logger.debug('found user "{}"'.format(user_id))
    return response_json['result']

def getChatMembersCount(chat_id):
    # Get the number of members in a chat
    # https://core.telegram.org/bots/api#getchatmemberscount
    logging.debug('getting total chat users')
    response = requests.get(api_url + 'getChatMembersCount?chat_id={}'.format(chat_id))
    if response.status_code != 200:
        logger.error('Telegram API failed with code "{}"'.format(response.status_code))
        logger.debug(response.text)
        sys.exit(1)
    try:
        response_json = response.json()
    except Exception as err:
        logger.error('response is not a valid JSON', exc_info = debug)
        logger.debug(response.text)
        sys.exit(1)
    if not response_json['ok']:
        logger.error('Telegram API failed "{}"'.format(response_json))
        logger.debug(response.text)
        sys.exit(1)
    logger.debug('there are {} chat User(s)'.format(response_json['result']))
    return response_json['result']

def getUpdates(offset = 0):
    # Get updates (100 each time by default)
    # https://core.telegram.org/bots/api#getupdates
    logging.debug('getting updates from offset "{}"'.format(offset))
    response = requests.get(api_url + 'getUpdates?offset={}'.format(offset))
    if response.status_code != 200:
        logger.error('Telegram API failed with code "{}"'.format(response.status_code))
        logger.debug(response.text)
        sys.exit(1)
    try:
        response_json = response.json()
    except Exception as err:
        logger.error('response is not a valid JSON', exc_info = debug)
        logger.debug(response.text)
        sys.exit(1)
    if not response_json['ok']:
        logger.error('Telegram API failed "{}"'.format(response_json))
        logger.debug(response.text)
        sys.exit(1)
    if not response_json['result']:
        logger.debug('response is empty')
        return []
    logger.debug('got {} update(s)'.format(len(response_json['result'])))
    return response_json['result']

def getAllUpdates(offset = 0):
    all_updates = []
    updates = getUpdates(offset)

    while len(updates) == 100:
        # Got 100 updates, maybe we have more
        all_updates.extend(updates)
        offset = updates[-1]['update_id'] + 1
        updates = getUpdates(offset)
    all_updates.extend(updates)
    return all_updates

def sendMessage(chat_id, message):
    # Get a message
    # https://core.telegram.org/bots/api#sendmessage
    # TODO: should add to the history database here
    logging.debug('sending message "{}"'.format(message))
    response = requests.get(api_url + 'sendMessage?chat_id={}&parse_mode=Markdown&text={}'.format(chat_id, message))
    if response.status_code != 200:
        logger.error('Telegram API failed with code "{}"'.format(response.status_code))
        logger.debug(response.text)
        sys.exit(1)
    try:
        response_json = response.json()
    except Exception as err:
        logger.error('response is not a valid JSON', exc_info = debug)
        logger.debug(response.text)
        sys.exit(1)
    if not response_json['ok']:
        logger.error('Telegram API failed "{}"'.format(response_json))
        logger.debug(response.text)
        sys.exit(1)
    logger.debug('message sent')
    return response_json['result']

def main():
    global api_url
    config_file = 'secrets.yaml'
    now = int(time.time())

    # Reading config file
    try:
        with open(config_file, 'r') as f:
            config = yaml.load(f)
    except Exception as err:
        # Cannot read config file
        logging.error('cannot read config file "{}"'.format(config_file), exc_info = debug)
        sys.exit(1)

    if not 'token' in config:
        logging.error('no token found in config file "{}"'.format(config_file))
        sys.exit(1)

    api_url = 'https://api.telegram.org/bot{}/'.format(config['token'])
    config_save = False

    # Reading options or setting defaults
    if 'debug' in config and config['debug']:
        logger.setLevel(logging.DEBUG)
    else:
        logging.debug('debug not found, setting it to "False"')
        config['debug'] = False
        config_save = True
    if not 'max_message_age' in config:
        logging.debug('max_message_age not found, setting it to "2*24*3600" seconds')
        config['max_message_age'] = 2*24*3600
        config_save = True
    if not 'max_user_idle' in config:
        logging.debug('max_user_idle not found, setting it to "60*24*3600" seconds')
        config['max_user_idle'] = 60*24*3600
        config_save = True
    if not 'database_file' in config:
        logging.debug('database_file not set, setting to "history.sdb"')
        config['database_file'] = 'history.sdb'
        config_save = True
    if os.path.isfile(config['database_file']):
        db = sqlite3.connect(config['database_file'])
        cur = db.cursor()
    else:
        logging.debug('database "{}" does not exists, creating it'.format(config['database_file']))
        db = sqlite3.connect(config['database_file'])
        cur = db.cursor()
        cur.execute('''CREATE TABLE messages (chat_id INT, message_id INT, date INT, PRIMARY KEY (chat_id, message_id))''')
        cur.execute('''CREATE TABLE users (user_id INT, chat_id INT, last_activity INT, PRIMARY KEY (user_id, chat_id))''')
        cur.execute('''PRAGMA user_version = 0''')
        db.commit()

    # Saving config file
    if config_save:
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style = False)

    # Getting the last offset
    offset = cur.execute('''PRAGMA user_version''').fetchone()[0]

    # Getting all pending updates
    updates = getAllUpdates(offset)

    if updates:
        # Setting the offset
        offset = updates[-1]['update_id'] + 1
        cur.execute('''PRAGMA user_version = {}'''.format(offset))

        # Reading all updates
        for update in updates:
            chat_id = update['message']['chat']['id']
            message_id = update['message']['message_id']
            date = update['message']['date']
            user_id = update['message']['from']['id']

            # Updating the history
            cur.execute('''INSERT OR REPLACE INTO messages(chat_id, message_id, date) VALUES(?, ?, ?)''', (chat_id, message_id, date))
            cur.execute('''INSERT OR REPLACE INTO users(user_id, chat_id, last_activity) VALUES(?, ?, ?)''', (user_id, chat_id, date))
        db.commit()

    # Checking users
    cur.execute('''SELECT DISTINCT chat_id FROM users''')
    for row in cur.fetchall():
        print(row)
        chat_id = row[0]
        tot_users = getChatMembersCount(chat_id)
        cur.execute('''SELECT COUNT(*) user_id FROM USERS WHERE chat_id = ?''', (chat_id,))
        found_users = cur.fetchone()[0]
        if tot_users > found_users:
            logging.warning('only {} out of {} users have been discovered'.format(found_users, tot_users))

    # Deleting old messages
    min_message_date = now - config['max_message_age']
    cur.execute('''SELECT chat_id, message_id, date FROM messages WHERE messages.date < ?''', (min_message_date,))
    for row in cur.fetchall():
        chat_id = row[0]
        message_id = row[1]
        date = row[2]
        readable_date = datetime.datetime.utcfromtimestamp(date)
        if deleteMessage(chat_id, message_id):
            # Message deleted
            logging.debug('deleting message_id "{}" on chat_id "{}" wrote on {}'.format(message_id, chat_id, readable_date))
    # If everything is ok we can delete all outdated messages
    cur.execute('''DELETE FROM messages WHERE messages.date < ?''', (min_message_date,))
    logging.debug('old messages have been deleted')
    db.commit()

    # Removing idle users
    min_user_activity = now - config['max_user_idle']
    cur.execute('''SELECT user_id, chat_id, last_activity FROM users WHERE users.last_activity < ?''', (min_user_activity,))
    for row in cur.fetchall():
        user_id = row[0]
        chat_id = row[1]
        last_activity = row[2]
        readable_date = datetime.datetime.utcfromtimestamp(last_activity)
        user = getChatMember(chat_id, user_id)
        if user['user']['is_bot']:
            # Not deleting bot
            logging.debug('skipping bot with user_id = "{}" on chat_id "{}"'.format(user_id, chat_id))
            continue
        elif user['status'] in ['creator', 'administrator']:
            # Skipping creator/administrators
            logging.debug('skipping {} with user_id = "{}" on chat_id "{}"'.format(user['status'], user_id, chat_id))
            continue
        # Warning the user for inactivity
        message = sendMessage(chat_id, 'Removing user "{}" after {} days of inactivity'.format(user['user']['first_name'], int((now - last_activity) / 3600 / 24)))
        # Adding message to the history
        chat_id = message['chat']['id']
        message_id = message['message_id']
        date = message['date']
        user_id = message['from']['id']
        cur.execute('''INSERT OR REPLACE INTO messages(chat_id, message_id, date) VALUES(?, ?, ?)''', (chat_id, message_id, date))
        cur.execute('''INSERT OR REPLACE INTO users(user_id, chat_id, last_activity) VALUES(?, ?)''', (user_id, chat_id, date))
        # Removing user for inactivity
        """
        if removeUser(chat_id, user_id):
            # TODO
            # User removed
            cur.execute('''DELETE FROM users WHERE user_id = ? and chat_id = ?''', (user_id, chat_id))
            logging.debug('removing user_id "{}" from chat_id "{}" because last_activity was on {}'.format(user_id, chat_id, readable_date))
            db.commit()
        """
    logging.debug('idle users have been removed')
    db.close()

if __name__ == '__main__':
    main()
