import logging
import imapclient
import email
import email.header
from email.utils import parseaddr

logger = logging.getLogger(__name__)

class Message(object):

    def __init__(self, id, raw_data):
        self.__id = id
        self.__raw_data = raw_data
        self.__data = None
        self.server = None

    def parse(self):
        logger.info("Parse message, id: '%s'", self.__id)
        self.__data = email.message_from_bytes(self.__raw_data)

    @property
    def id(self):
        return self.__id

    @property
    def data(self):
        return self.__data

    @property
    def sender(self):
        try:
            return parseaddr(self['from'])[1]
        except:
            return 'unknown'

    @property
    def is_inner(self):
        return self['received'].startswith('by {}'.format(self.server.host))

    def _log(self, msg):
        logger.info("Message (%s) action: %s", self.id, msg)

    def __getitem__(self, name):
        parts = email.header.decode_header(self.data[name])
        if type(parts[0][0]) == bytes:
            glue = b" "
        else:
            glue = " "
        return str(glue.join([part[0] for part in parts]))

    def mark_as_read(self):
        res = self.server.remote.set_flags([self.id], [imapclient.SEEN])
        self._log("set seen: {}".format(res))

    def mark_as_unread(self):
        res = self.server.remote.remove_flags([self.id], [imapclient.SEEN])
        self._log("set unseen: {}".format(res))

    def move_to(self, folder):
        self.copy_to(folder)
        self.delete()

    def copy_to(self, folder):
        self.server.remote.copy([self.id], folder)
        self._log("copy to '{}'".format(folder))

    def delete(self):
        res = self.server.remote.delete_messages([self.id])
        self.server.remote.expunge()
        self._log("delete: {}".format(res))
