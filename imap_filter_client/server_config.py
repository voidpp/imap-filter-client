import logging

from .passwd import decode

logger = logging.getLogger(__name__)

class ServerConfig(object):

    def __init__(self, data):
        self.__data = data
        self.__password = None

    @property
    def host(self):
        return self.__data['host']

    @property
    def port(self):
        return self.__data['port']

    @property
    def ssl(self):
        return self.__data['ssl']

    @property
    def username(self):
        return self.__data['username']

    @property
    def password(self):
        if self.__password is None:
            if 'password_plain' in self.__data:
                self.__password = self.__data['password_plain']
            else:
                logger.info("Decrypting password...")
                self.__password = decode(self.__data['password'])
        return self.__password

    @property
    def folder(self):
        return self.__data['folder']
