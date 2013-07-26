#!/usr/bin/env python
# -*- coding: utf-8 -

from route import Route
from base import BaseHandler
from time import time
import logging
import json
from db import sinform


from db.params import Params

@Route(r"/config")
class Config(BaseHandler):
    def onpost(self):
        from shlex import split
        cmd = self.get_argument('cmd', '')
        if cmd == 'save':
            body = self.request.body

            config = {}
            for conf in body.split("\n"):
                params = split(conf.strip())
                if len(params) == 4:
                    config[params[0]] = {
                        "type": params[1],
                        "value": params[2],
                        "default": params[3]
                    }

            Params().saveconfig(self.skey, config)

            # В оригинале: inform(skey, 'cfgupd', {'skey': str(skey)})
            msg = {
                "message": "cfg_upd",
                "skey": self.skey
            }
            self.application.publisher.send(msg)

            self.write("CONFIG: OK\r\n")

# /params?imei=013226000198214&cmd=params
@Route(r"/params")
class Config(BaseHandler):
    def onget(self):

        cmd = self.get_argument('cmd', '')

        if cmd == "params":
            empty = True
            params = Params.get(self.skey).all()
            for (k, v) in params.iteritems():
                if v.has_key("queue"):
                    self.write("PARAM %s %s\r\n" % (k, v["queue"]))
                    empty = False

            self.write("FINISH\r\n")
            if empty:
                sinform.sinform_unset(self.skey, "CONFIGUP")

        elif cmd == 'cancel':
            Params.del_queueall(self.skey)
            sinform.sinform_unset(self.skey, "CONFIGUP")
            self.write("DELETED\r\n")

            msg = {
                "message": "cfg_upd",
                "skey": self.skey
            }
            self.application.publisher.send(msg)

        elif cmd == 'confirm':
            Params.confirm_queueall(self.skey)
            sinform.sinform_unset(self.skey, "CONFIGUP")
            self.write("CONFIRM")

            msg = {
                "message": "cfg_upd",
                "skey": self.skey
            }
            self.application.publisher.send(msg)

        elif cmd == 'check':
            empty = True
            params = Params.get(self.skey).all()
            for (k, v) in params.iteritems():
                if v.has_key("queue"):
                    empty = False

            if empty:
                sinform.sinform_unset(self.skey, "CONFIGUP")
                self.write('NODATA\r\n')
            else:
                sinform.sinform_set(self.skey, "CONFIGUP")
                self.write("CONFIGUP\r\n")
