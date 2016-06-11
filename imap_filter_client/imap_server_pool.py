import logging
from .imap_server import IMAPServer

logger = logging.getLogger(__name__)

class ImapServerPool(object):

    def __init__(self, config):
        self.__servers = {}
        self.__config = config

    def fetch(self, name, readonly = False):
        """Fetch an IMAP server connection.

        If the connection is not opened already or dead, create a new connection.

        Args:
            name (str): the name of the server in the config
            readonly (bool): set the connection to readonly

        Returns:
            An IMAPServer instance
        """
        # maybe add folder to args? the readonly flag used when select folder

        if name not in self.__config:
            return None

        if name in self.__servers:
            server = self.__servers[name]
            server.alive()
            server.readonly = readonly
        else:
            server = self.__servers[name] = IMAPServer(self.__config[name], name, readonly = readonly)
            server.connect()

        return server

