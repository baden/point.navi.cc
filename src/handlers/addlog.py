#!/usr/bin/env python
# -*- coding: utf-8 -

from route import Route
from base import BaseHandler
from time import time
import logging
from db.logs import Logs
import re

restartlog = re.compile(r'SWID:<b>([\dA-F]+)</b>')

@Route(r"/addlog")
class AddLogHandler(BaseHandler):
    def onpost(self, *args, **kwargs):
        self.postget(*args, **kwargs)

    def onget(self, *args, **kwargs):
        self.postget(*args, **kwargs)

    def postget(self):
        #logging.error('/addlog')
        slat = self.get_argument('lat', '0000.0000E')
        slon = self.get_argument('lon', '00000.0000N')

        lat = float(slat[:2]) + float(slat[2:9]) / 60.0
        lon = float(slon[:3]) + float(slon[3:10]) / 60.0

        if slat[-1] == 'S':
            lat = -lat

        if slon[-1] == 'W':
            lon = -lon

        text = self.get_argument('text', None)
        try:
            swid = restartlog.findall(text)[0]
            logging.info("parced SWID: %s" % repr(swid))
            self.system.update({"$set": {"swid": swid}})

        except:
            logging.info("skip parce")
            pass

        log = {
            'imei': self.imei,
            'skey': self.skey,
            'akey': self.get_argument('akey', None),
            'text': text,
            'label': int(self.get_argument('label', '0'), 10),
            'mtype': self.get_argument('mtype', None),
            'lat': lat,
            'lon': lon,
            'fid': int(self.get_argument('fid', '0'), 10),
            'ceng': self.get_argument('ceng', ''),
            'dt': int(time())
        }
        Logs().add(log)
        del log["_id"]
        msg = {
            "message": "add_log",
            "skey": self.skey,
            "log": log
        }
        self.application.publisher.send(msg)

        self.write("ADDLOG: OK\r\n")
