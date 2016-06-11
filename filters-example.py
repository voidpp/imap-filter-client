
from imap_filter_client import SpamChecker
import re

white_list = [,
    ('received', re.compile('\.google\.com ')),
]

spam_checker = SpamChecker(white_list)

def on_message(message):

    if message['from'].find("notifications@github.com") >= 0:
        message.move_to('INBOX.github')
        return

    try:
        if spam_checker.test(message):
            message.move_to('Spam')
    except Exception as e:
        print(e)
        return
