# -*- coding: utf-8 -*-
import logging

#import config
from config import MONGO_URL
from base import DBBase
import json


class Params(DBBase):
    col = 'params'

    # @classmethod
    # def save(cls, skey, object):
    #     #logging.info('Params.save(%s, %s)', str(imei), str(object))
    #     #logging.info('=== config=%s', str(MONGO_URL))
    #     #logging.info('=== db=%s', cls.db)
    #     super(Params, cls).save({'_id': skey, 'save': json.dumps(object)})

    @classmethod
    def get(cls, key):
        return cls(key)      # На данный момент есть различия в реализации и это получает данные
        # value = cls.find_by_key(skey)
        # if value is None:
        #     return None
        # return json.loads(value["save"])

    def all(self):
        result = {}
        if self.document is not None:
            for (k,v) in self.document.iteritems():
                if k not in ["_id", "__cache__"]:
                    result[DBBase.fromkey(k)] = v
        return result

    @classmethod
    def del_queueall(cls, skey):
        self = cls.get(skey)
        result = {}
        for (k, v) in self.document.iteritems():
            if k not in ["_id", "__cache__"]:
                if v.has_key("queue"):
                    result[k + ".queue"] = ""
        self.reset_cache()
        self.collection.update({"_id": self.key}, {"$unset": result})

    @classmethod
    def confirm_queueall(cls, skey):
        self = cls.get(skey)
        _set = {}
        unset = {}
        for (k, v) in self.document.iteritems():
            if k not in ["_id", "__cache__"]:
                if v.has_key("queue"):
                    _set[k + ".value"] = v["queue"]
                    unset[k + ".queue"] = ""
        self.reset_cache()
        self.collection.update({"_id": self.key}, {"$set": _set, "$unset": unset})

    def saveconfig(self, skey, config):
        # logging.info('saveconfig (%s, %s)' % (repr(skey), repr(config)))
        prepare = {}
        # for (k, v) in config.iteritems():
        #     prepare[DBBase.tokey(k)] = v
        for (k, v) in config.iteritems():
            prepare[DBBase.tokey(k) + ".type"] = v["type"]
            prepare[DBBase.tokey(k) + ".value"] = v["value"]
            prepare[DBBase.tokey(k) + ".default"] = v["default"]
        # logging.info('saveconfig prepare (%s)' % repr(prepare))
        self.collection.update({"_id": skey}, {"$set": prepare}, True)
        pass