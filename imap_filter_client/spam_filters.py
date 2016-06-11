import re
import logging
from backports import ssl
from email.utils import parseaddr

logger = logging.getLogger(__name__)

class Context(dict):

    sender_server_pattern = re.compile('from (.+) \((.+) \[\d')
    sender_server_ip_pattern = re.compile('from .+ \[(\d{1,3}).(\d{1,3}).(\d{1,3}).(\d{1,3})\]\)')

    def __init__(self, message):
        self.message = message

    def fetch(self, key):
        if key in self:
            return self[key]
        name = 'fetch_{}'.format(key)

        if not hasattr(self, name):
            raise Exception("Unknown context var '{}'".format(key))

        self[key] = getattr(self, name)()
        return self[key]

    def fetch_email_domain(self):
        addr = parseaddr(self.message['from'])
        return addr[1].rsplit('@', 1)[-1]

    def fetch_sender_server_domain(self):
        matches = self.sender_server_pattern.search(self.message['received'])
        if matches is None:
            logger.error('Cannot fetch sender_server_domain. Received header: %s', self.message['received'])
            return ''
        return matches.group(2)

    def fetch_sender_server_ip(self):
        matches = self.sender_server_ip_pattern.search(self.message['received'])
        if matches is None:
            logger.error('Cannot fetch sender_server_ip. Received header: %s', self.message['received'])
            return ''
        return matches.groups()

def filter_(label):
    def decor(func):
        func.label = label
        return func
    return decor

class SpamFilters(object):

    unknown_sender_pattern = re.compile('\(unknown \[\d.{7,15}\]\)')
    magic_words = ['dyn', 'static']
    isp_ip_pattern = re.compile('(\d{1,3}).(\d{1,3}).(\d{1,3}).(\d{1,3})')

    def get_filters(self):
        filters = []
        for name in dir(self):
            attr = getattr(self, name)
            if hasattr(attr, 'label'):
                filters.append(dict(
                    callback = attr,
                    label = getattr(attr, 'label'),
                ))
        return filters

    @filter_('unknown sender')
    def unknown(self, context):
        return self.unknown_sender_pattern.search(context.message['received']) is not None

    @filter_('sender email - sender server mismatch')
    def email_mismatch(self, context):
        email_domain = context.fetch('email_domain')
        server_domain = '.'.join(context.fetch('sender_server_domain').split('.')[-2:])
        return email_domain != server_domain

    @filter_('magic words in sender server domain')
    def magic_doimain_words(self, context):
        server_domain = context.fetch('sender_server_domain')
        for word in self.magic_words:
            if server_domain.find(word) != -1:
                logger.debug("Magic word '%s' found in server domain (%s)", word, server_domain)
                return True
        return False

    @filter_('the sender is an end-user')
    def end_user(self, context):
        sender_ip = context.fetch('sender_server_ip')
        server_domain = context.fetch('sender_server_domain')
        matches = self.isp_ip_pattern.search(server_domain)
        if matches is None:
            return False
        sender_domain_ip = matches.groups()
        if sender_ip == sender_domain_ip:
            return True
        if sender_ip == reversed(sender_domain_ip):
            return True
        return False


class SpamChecker(object):

    def __init__(self, white_list = []):
        self.white_list = white_list
        self.filters = SpamFilters().get_filters()

    def is_in_white_list(self, message):
        for field, pattern in self.white_list:
            try:
                value = message[field]
            except:
                logger.error("Unknown field: '%s' in white list", field)
                # raise?
                continue

            if pattern.search(value):
                return True

    def test(self, message):

        if message.is_inner:
            return False

        if self.is_in_white_list(message):
            return False

        context = Context(message)
        for filter_desc in self.filters:
            result = filter_desc['callback'](context)
            if result:
                logger.info("Email (%s) from <%s> looks like spam (%s)", message.id, parseaddr(message['from'])[1], filter_desc['label'])
                return True
        return False
