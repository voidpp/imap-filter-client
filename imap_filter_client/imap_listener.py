import logging
from threading import Thread
from voidpp_tools.timer import Timer

from .imap_server import IMAPServer, ALL_IMAP_FIELD
from .message import Message

logger = logging.getLogger(__name__)

class IMAPListener(Thread):
    def __init__(self, config, name, message_processor):
        super(IMAPListener, self).__init__()
        self.__message_processor = message_processor
        self.__name = name

        # Need to set readonly. Without this the fetch command will set the seen flag.
        # (the BODY.PEEK or RFC822.PEEK maybe not supported by the server)
        self.__server = IMAPServer(config, name, readonly = True)
        self.__last_uid = self.__server.connect()
        self.__timer = Timer(12 * 3600, self.alive)

    def alive(self):
        logger.info("Automatic reconnect...")
        self.__server.alive()

    def run(self):
        self.__timer.start()
        server = self.__server.remote
        logger.info("Start listening on '%s'", self.__name)
        while 1:
            server.idle()
            # idle check is blocking until something is happened in the server

            try:
                response = server.idle_check()
            except AssertionError: # whoa.... NOOP caused some AssertionError need to catch
                continue

            server.idle_done()

            logger.debug("Idle check response: %s", response)

            if not len(response):
                continue

            # search for new messages
            message_uids = server.search([u'UID', u'{}:*'.format(self.__last_uid)])

            # for some reason the imap server gives back at least one uid outside search range
            message_uids = [uid for uid in message_uids if uid > self.__last_uid]

            if not len(message_uids):
                continue

            logger.info("Found new messages on server '%s': %s", self.__name, message_uids)

            message_uids = sorted(message_uids)

            self.__last_uid = message_uids[-1:][0]

            # need to set the readonly flag to the server, because "idle" unset it
            self.__server.readonly = True

            # fetch all the email data
            raw_messages = server.fetch(message_uids, ALL_IMAP_FIELD)
            messages = []
            for id, data in raw_messages.items():
                content = None
                try:
                    content = data[b'RFC822']
                except:
                    logger.error("Email data without 'RFC822' field! id: %s", id)
                    continue
                messages.append(Message(id, content))

            if len(messages):
                self.__message_processor.queue(messages, self.__name)
