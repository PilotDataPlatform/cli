import logging
from logging.handlers import RotatingFileHandler
import os


class Logger(object):

    def __init__(self, name='log'):
        if not os.path.exists("./logs/"):
            os.makedirs("./logs/")
        if os.path.isfile("./logs/" + name):
            os.remove("./logs/" + name)
        self.name = name
        self.logger = logging.getLogger(name)
        level = logging.INFO

        self.logger.setLevel(level)
        fh = RotatingFileHandler("./logs/"+name, maxBytes=500000, backupCount=1)
        formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s',
                                      '%Y-%m-%d %H:%M:%S')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

    def info(self, msg):
        self.logger.info(msg)

    def debug(self, msg):
        self.logger.debug(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)
