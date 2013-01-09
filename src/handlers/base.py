#!/usr/bin/env python
# -*- coding: utf-8 -

from tornado.web import RequestHandler
from config import IMEI_BLACK_LIST
import logging


class BaseHandler(RequestHandler):
    """
    Точка входа для всех трекеров
    Обязательный параметр: imei
    """
    def options(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type, X-Requested-With, Content-Length')

    def post(self, *args, **kwargs):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header("Cache-control", "no-cache")
        #self.set_header('Content-Type', 'application/octet-stream')

        self.imei = self.get_argument("imei", None)
        print dir(self)
        if self.imei in IMEI_BLACK_LIST:
            logging.error("IMEI in black list. Denied. [%s]" % self.imei)
            self.write('ERROR: BLACK LIST\r\n')
            return

        self.skey = self.application.system.skey_by_imei_or_create(self.imei)
        self.onpost(*args, **kwargs)

    def get(self, *args, **kwargs):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header("Cache-control", "no-cache")
        #self.set_header('Content-Type', 'application/octet-stream')

        self.imei = self.get_argument("imei", None)
        #print dir(self.reverse_url(self))
        if self.imei in IMEI_BLACK_LIST:
            logging.error("IMEI in black list. Denied. [%s]" % self.imei)
            self.write('ERROR: BLACK LIST\r\n')
            return

        self.skey = self.application.system.skey_by_imei_or_create(self.imei)
        self.onget(*args, **kwargs)

    def onpost(self, *args, **kwargs):
        pass

    def onget(self, *args, **kwargs):
        pass

