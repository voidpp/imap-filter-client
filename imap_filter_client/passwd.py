from base64 import b64decode, b64encode
from simplecrypt import encrypt, decrypt

VERY_SECRET_SALT = '5klj4h35'

#TODO: oauth?

def encode(password):
    return b64encode(encrypt(VERY_SECRET_SALT, password))

def decode(crypted_data):
    return decrypt(VERY_SECRET_SALT, b64decode(crypted_data))
