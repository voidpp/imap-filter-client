import logging
import imapclient
import imaplib
from backports import ssl

logger = logging.getLogger(__name__)

ALL_IMAP_FIELD = ['FLAGS', 'INTERNALDATE', 'RFC822', 'ENVELOPE']

class IMAPServer(object):
    def __init__(self, config, name, readonly = False):
        self.__config = config
        self.__server = None
        self.__name = name
        self.__readonly = readonly
        self.__folder = config.folder

    @property
    def host(self):
        return self.__config.host

    @property
    def name(self):
        return self.__name

    @property
    def remote(self):
        return self.__server

    @property
    def readonly(self):
        return self.__readonly

    @readonly.setter
    def readonly(self, val):
        if val == self.__readonly:
            return
        self.__readonly = val
        self.set_folder(self.__config.folder, val)

    def alive(self):
        try:
            self.__server.noop()
        except (imaplib.IMAP4.abort, ssl.core.SSLZeroReturnError):
            logger.info("Connection server '%s' is lost.", self.name)
            self.connect()

    def set_folder(self, folder, readonly = False):
        self.__folder = folder
        self.__readonly = readonly
        info = self.__server.select_folder(folder, readonly = self.__readonly)
        return info[b'UIDNEXT'] - 1

    def connect(self):
        params = dict(
            use_uid = True,
            ssl = self.__config.ssl,
        )

        if self.__config.ssl:
            context = imapclient.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            params['ssl_context'] = context

        if self.__config.port:
            params['port'] = self.__config.port

        self.__server = imapclient.IMAPClient(self.__config.host, **params)
        self.__server.login(self.__config.username, self.__config.password)
        last_uid = self.set_folder(self.__folder)

        logger.info("Connect and login %s is successfull. Last uid is %s", self.__config.host, last_uid)

        return last_uid
