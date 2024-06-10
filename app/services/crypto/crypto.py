# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

import app.services.output_manager.error_handler as ehandler


def generate_secret():
    """
    generate a random secret key for encryption
    return: string type secret key
    """
    secret = os.urandom(16)
    secret_token = base64.b64encode(secret).decode('utf-8')
    # convert byte to string
    return secret_token


def encryption(message_to_encrypt, secret):
    """
    encrypt string message into byte
    message_to_encrypt: a string that need to encrypt
    secret: the secret key used to encrypt the string,
    generated by generate_secret
    return: encrypted string
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=base64.b64decode(secret),  # input binary string secret key
        iterations=600000,
        backend=default_backend(),
    )
    # generate key to involve current device information
    key = base64.urlsafe_b64encode(kdf.derive('SECRETKEYPASSWORD'.encode()))
    message_encode = message_to_encrypt.encode()
    f = Fernet(key)
    encrypt_message = f.encrypt(message_encode)
    encrypted = base64.b64encode(encrypt_message).decode('utf-8')
    # convert byte to string
    return encrypted


def decryption(encrypted_message, secret, interactive=True):
    """
    decrypt byte that encrypted by encryption function
    encrypted_message: the string that need to decrypt to string
    secret: the string type secret key used to encrypt message
    return: string of the message
    """
    if encrypted_message:
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=base64.b64decode(secret),
                iterations=600000,
                backend=default_backend(),
            )
            # use the key from current device information
            key = base64.urlsafe_b64encode(kdf.derive('SECRETKEYPASSWORD'.encode()))
            f = Fernet(key)
            decrypted = f.decrypt(base64.b64decode(encrypted_message))
            return decrypted.decode()
        except Exception as ex:
            if interactive:
                ehandler.SrvErrorHandler.default_handle(str(ex) + ', please try login as a valid user.')
            else:
                raise ex
    else:
        ehandler.SrvErrorHandler.customized_handle(ehandler.ECustomizedError.LOGIN_SESSION_INVALID, True)
