#!/usr/bin/env python
# -*- coding: utf-8 -

from route import Route
from base import BaseHandler
from time import time
import logging
import json


from db.params import Params

@Route(r"/config")
class Config(BaseHandler):
    def onpost(self):
        from shlex import split
        cmd = self.get_argument('cmd', '')
        if cmd == 'save':
            #logging.info('Save config')
            body = self.request.body
            #logging.info("== CONFIG_BODY: %s" % repr(body))

            config = {}
            for conf in body.split("\n"):
                #params = conf.strip().split()
                params = split(conf.strip())
                #logging.info("== PARAM: %s" % repr(params))
                if len(params) == 4:
                    config[params[0]] = {
                        "type": params[1],
                        "value": params[2],
                        "default": params[3]
                    }

            #logging.info("config={0}".format(repr(config)))
            document = {
                '_id': self.skey,
                'save': json.dumps(config)
            }

            Params().save(document)
            self.write("CONFIG: OK\r\n")
