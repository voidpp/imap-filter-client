import logging
import imaplib
from threading import Thread
from queue import Queue
from .imap_server import IMAPServer

logger = logging.getLogger(__name__)

class MessageProcessor(Thread):

    def __init__(self, server_pool):
        super(MessageProcessor, self).__init__()
        self.setDaemon(True)
        self.__tasks = Queue()
        self.message_filter_callback = None
        self.__server_pool = server_pool

    def queue(self, messages, server_name):
        """Add messages to the queue

        Args:
            messages (list): list of Message instance
            server_name (str): the name of the server in the config
        """
        logger.debug("Add messages to queue: %s", len(messages))
        for message in messages:
            self.__tasks.put_nowait((message, server_name))

    def run(self):
        while True:
            message, server_name = self.__tasks.get()
            logger.debug("Start processing a message")
            message.parse()
            """
            However the IMAPListener has a server connection, waits for the new emails with idle_check, but meanwhile the server
            checking there is no way to perform any command (move, mark as read, etc) in this server instance
            se need to open an other connection.
            """
            message.server = self.__server_pool.fetch(server_name)

            if self.message_filter_callback:
                logger.debug("Call filter callback for message id: %s, from: '%s'", message.id, message.sender)
                try:
                    self.message_filter_callback(message)
                except Exception as e:
                    logger.exception("Exception during run message filters.", e)
            else:
                logger.warning("There is no message filter callback set in MessageProcessor!")

            self.__tasks.task_done()
