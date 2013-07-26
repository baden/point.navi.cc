#!/usr/bin/env python
# -*- coding: utf-8 -

import logging
from config import MONGO_URL, MONGO_DATABASE, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_SOCKET_PATH
from pymongo import Connection
import pickle
from redis import Redis

connection = Connection(MONGO_URL)
db = connection[MONGO_DATABASE]
redis = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, unix_socket_path=REDIS_SOCKET_PATH)


class DBBase(object):
    db = db
    redis = redis

    def __init__(self, key=None, cached=False):
        logging.info("DBBase.__init__(%s, %s) as %s", str(key), str(cached), str(self.__class__.__name__))
        self.cached = cached
        self.collection = self.db[self.__class__.__name__]
        self.document = self.get_by_key(key)
        logging.info("  + self.document=%s", repr(self.document))

    def __repr__(self):
        return "DB:'{0}' collection:'{0}' document:'{1}'".format(self.__class__.__name__, repr(self.document))

    def get_by_key(self, key):
        if key is None:
            return None

        if self.cached:
            prefix = self.__class__.__name__
            s = self.redis.get('%s.%s' % (prefix, key))
            if s is not None:
                try:
                    s = pickle.loads(s)
                    s["__cache__"] = 'from cache'
                except:
                    self.redis.delete('%s.%s' % (prefix, key))
                    s = None
                return s
            else:
                s = self.collection.find_one({"_id": key})
                if s is not None:
                    self.redis.set('%s.%s' % (prefix, key), pickle.dumps(s))
                    s["__cache__"] = 'from db'
                    return s
            return None
        else:
            s = self.collection.find_one({"_id": key})
            if s is not None:
                s["__cache__"] = 'disabled'
            return s

    def reset_cache(self):
        prefix = self.__class__.__name__
        logging.info('== RESET CACHE = %s.%s' % (repr(prefix), repr(self.key)))
        self.redis.delete('%s.%s' % (prefix, self.key))

    def update(self, param):
        self.reset_cache()
        self.collection.update({"_id": self.key}, param)

    @property
    def isNone(self):
        return self.document is None

    @property
    def key(self):
        if self.document is None:
            return None
        return self.document["_id"]

    def insert(self, document):
        self.document = document
        self.collection.save(self.document)

    def save(self, document):
        self.document = document
        self.collection.save(self.document)

    @staticmethod
    def tokey(key):
        return key.replace(".", "#")

    @staticmethod
    def fromkey(key):
        return key.replace("#", ".")

    '''
    @classmethod
    def save(cls, value, key=None):
        logging.info("DBBase.save(%s, %s) to %s", str(key), str(value), str(cls.col))
        if cls.col == None:
            logging.error("DBBase.insert col must by set.")
        else:
            if isinstance(value, dict):
                if key is not None:
                    value["_id"] = key
                cls.db[cls.col].save(value)
            else:
                logging.error("DBBase.insert col must by set.")

    @classmethod
    def find_by_key(cls, key):
        #logging.info("find[%s]({'_id':%s})", str(cls.col), str(key))
        return cls.db[cls.col].find_one({"_id": key})
    '''
