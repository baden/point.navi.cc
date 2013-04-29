#!/usr/bin/env python
# -*- coding: utf-8 -

from tornado.web import RequestHandler
from config import IMEI_BLACK_LIST
import logging
from datetime import datetime

from db.system import System


class BaseHandler(RequestHandler):
    """
    Точка входа для всех трекеров
    Обязательный параметр: imei
    """
    def options(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', 'Authorization, Content-Type, X-Requested-With, Content-Length')

    def post(self, *args, **kwargs):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header("Cache-control", "no-cache")
        #self.set_header('Content-Type', 'application/octet-stream')

        self.imei = self.get_argument("imei", None)
        #print dir(self)
        if self.imei in IMEI_BLACK_LIST:
            logging.error("IMEI in black list. Denied. [%s]" % self.imei)
            self.write('ERROR: BLACK LIST\r\n')
            return

        system = System.create_or_update(self.imei, cached=True)
        self.skey = system.key
        #TODO! Добавить обновление из self.get_arguments телефона и других "редко-изменяемых" параметров
        #TODO! Добавить обработку из self.get_arguments "часто-изменяемых" параметров

        #system.create_or_update() # Создать или обновить

        #self.skey = System.skey_by_imei_or_create(self.imei)
        self.onpost(*args, **kwargs)

    def get(self, *args, **kwargs):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header("Cache-Control", "no-cache, must-revalidate")
        self.set_header("Expires", "Mon, 26 Jul 1997 05:00:00 GMT")
        now = datetime.now()
        expiration = datetime(now.year - 1, now.month, now.day)
        self.set_header("Last-Modified", expiration)
        #self.set_header('Content-Type', 'application/octet-stream')

        self.imei = self.get_argument("imei", None)
        #print dir(self.reverse_url(self))
        if self.imei in IMEI_BLACK_LIST:
            logging.error("IMEI in black list. Denied. [%s]" % self.imei)
            self.write('ERROR: BLACK LIST\r\n')
            return

        #self.skey = self.application.system.skey_by_imei_or_create(self.imei)
        system = System.create_or_update(self.imei, cached=True)
        self.skey = system.key
        self.onget(*args, **kwargs)

    def compute_etag(self):
        return None

    def onpost(self, *args, **kwargs):
        pass

    def onget(self, *args, **kwargs):
        pass

