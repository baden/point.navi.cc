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
    def get(cls, skey):
        value = cls.find_by_key(skey)
        if value is None:
            return None
        return json.loads(value["save"])

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