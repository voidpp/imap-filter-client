import logging
from importlib.machinery import SourceFileLoader
from voidpp_web_tools.remote_controller_daemon import RemoteControllerDeamon, rpc

"""
This processor create a thread for each imap server for listening. The imapclient use the socket and select modules in that way to cause
some problem when started from a thread. The gevent.monkey.patch_all makes some modifications in the related modules so the imapclient
idle, idle_check will works. The gevent used only for this.
"""
from gevent import monkey
monkey.patch_all()

from .imap_listener import IMAPListener
from .message_processor import MessageProcessor
from .imap_server_pool import ImapServerPool
from .passwd import encode
from .imap_server import ALL_IMAP_FIELD
from .message import Message

logger = logging.getLogger(__name__)

def cli(name = None, help = None, arguments = []):
    def wrapper(func):
        func._command_line = dict(
            name = name or func.__name__,
            help = help or name or func.__name__,
            arguments = arguments,
            func = func.__name__,
        )
        return func
    return wrapper

class FilterProcessor(RemoteControllerDeamon):

    def __init__(self, pid, logger, config):
        super(FilterProcessor, self).__init__(pid, logger)
        self.__config = config
        self.__sever_pool = ImapServerPool(self.__config['servers'])
        self.__processor = MessageProcessor(self.__sever_pool)

    @cli('passwd-encrypt', 'encrypt password for config', [dict(name = 'text')])
    def passwd_encrypt(self, text):
        print(text)
        return '42'
        return str(encode(text))

    @cli('folder-list', 'get full folder list', [dict(name = 'server')])
    def folder_list(self, server):
        server = self.__sever_pool.fetch(server, readonly = True)
        res = []
        if server is None:
            return 'No such server'
        for folder in server.remote.list_sub_folders():
            res.append(folder[2])
        return "\n".join(res)

    @cli(help = 'reload the filters')
    @rpc
    def reload(self):
        return 'Filters reloaded successfully.' if self.__load_filters() else 'Errors in the filters. See log for details.'

    @cli('run', 'run filters now', [
            dict(name = 'server', help = 'the IMAP server'), #  choices = self.__config['servers'].keys()
            dict(name = ('-f', '--folder'), default = 'INBOX', help = 'the name of the imap folder (default: INBOX)'),
            dict(name = ('-l', '--limit'), type = int, default = 10, help = 'limits the fetching mails (default: 10)')
        ])
    @rpc
    def rerun(self, server, folder, limit):
        name = server
        server = self.__sever_pool.fetch(name)
        server.set_folder(folder, readonly = True)

        all_uids = server.remote.search()
        uids = all_uids[(-1*limit):] if limit > 0 else all_uids

        raw_messages = server.remote.fetch(uids, ALL_IMAP_FIELD)
        messages = [Message(id, data[b'RFC822']) for id, data in raw_messages.items()]

        self.__processor.queue(messages, name)

        return "Filtering started in {} mails...".format(len(messages))

    def __load_filters(self):
        logger.info("Load filter file '%s'", self.__config['filters'])

        loader = SourceFileLoader('filters', self.__config['filters'])

        try:
            module = loader.load_module()
        except Exception as e:
            logger.exception("Cannot load filter file, because of: %r", e)
            return False

        if not hasattr(module, 'on_message'):
            logger.error("There is no 'on_message' in filter file %s", module)
            return False

        logger.info("Filter file successfully loaded")

        self.__processor.message_filter_callback = module.on_message
        return True

    def __create_listeners(self):
        for name, config in list(self.__config['servers'].items()):
            listener = IMAPListener(config, name, self.__processor)
            listener.setDaemon(True)
            listener.start()

    def start(self):
        self.__processor.start()
        self.__load_filters()
        self.__create_listeners()
        super(FilterProcessor, self).start()
