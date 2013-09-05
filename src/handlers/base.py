#!/usr/bin/env python
# -*- coding: utf-8 -

from tornado.web import RequestHandler
from config import IMEI_BLACK_LIST
import logging
from datetime import datetime
from time import time

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

        #logging.info()

        self.msgs = []
        self.dynamic = {}

        self.imei = self.get_argument("imei", None)
        #print dir(self)
        if self.imei in IMEI_BLACK_LIST:
            logging.error("IMEI in black list. Denied. [%s]" % self.imei)
            self.write('ERROR: BLACK LIST\r\n')
            return

        phone = self.get_argument("phone", None)

        system = System.create_or_update(self.imei, cached=True, phone=phone)
        self.system = system
        self.skey = system.key

        # Динамические данные: csq, vout, vin
        self.dynamic["lastping"] = int(time())
        csq = self.get_argument("csq", None)
        if csq is not None:
            self.dynamic["csq"] = csq
        vout = self.get_argument("vout", None)
        if vout is not None:
            self.dynamic["vout"] = int(vout) / 1000.0
        vin = self.get_argument("vin", None)
        if vin is not None:
            self.dynamic["vin"] = int(vin) / 1000.0

        #TODO! Добавить обновление из self.get_arguments телефона и других "редко-изменяемых" параметров
        #TODO! Добавить обработку из self.get_arguments "часто-изменяемых" параметров

        #system.create_or_update() # Создать или обновить

        #self.skey = System.skey_by_imei_or_create(self.imei)
        self.onpost(*args, **kwargs)

        system.update_dynamic(**self.dynamic)
        msg = {
            "id": 0,
            "message": "update_dynamic",
            "skey": self.skey,
            "dynamic": self.dynamic
        }
        self.application.publisher.send(msg)

    def get(self, *args, **kwargs):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header("Cache-Control", "no-cache, must-revalidate")
        self.set_header("Expires", "Mon, 26 Jul 1997 05:00:00 GMT")
        now = datetime.now()
        expiration = datetime(now.year - 1, now.month, now.day)
        self.set_header("Last-Modified", expiration)
        #self.set_header('Content-Type', 'application/octet-stream')

        self.imei = self.get_argument("imei", None)
        phone = self.get_argument("phone", None)
        #print dir(self.reverse_url(self))
        if self.imei in IMEI_BLACK_LIST:
            logging.error("IMEI in black list. Denied. [%s]" % self.imei)
            self.write('ERROR: BLACK LIST\r\n')
            return

        #self.skey = self.application.system.skey_by_imei_or_create(self.imei)
        system = System.create_or_update(self.imei, cached=True, phone=phone)
        self.system = system
        self.skey = system.key

        self.dynamic = {}

        # Динамические данные: csq, vout, vin
        self.dynamic["lastping"] = int(time())
        csq = self.get_argument("csq", None)
        if csq is not None:
            self.dynamic["csq"] = csq
        vout = self.get_argument("vout", None)
        if vout is not None:
            self.dynamic["vout"] = int(vout) / 1000.0
        vin = self.get_argument("vin", None)
        if vin is not None:
            self.dynamic["vin"] = int(vin) / 1000.0

        self.onget(*args, **kwargs)

        system.update_dynamic(**self.dynamic)
        msg = {
            "id": 0,
            "message": "update_dynamic",
            "skey": self.skey,
            "dynamic": self.dynamic
        }
        self.application.publisher.send(msg)

    def compute_etag(self):
        return None

    def onpost(self, *args, **kwargs):
        pass

    def onget(self, *args, **kwargs):
        pass

