#!/usr/bin/env python
# -*- coding: utf-8 -

from zmq.eventloop import ioloop; ioloop.install()
from zmq.eventloop.zmqstream import ZMQStream
import zmq

import os
"""
here = os.path.dirname(os.path.abspath(__file__))
os.environ['PYTHON_EGG_CACHE'] = os.path.join(here, '..', 'misc/virtenv/lib/python2.7/site-packages')
virtualenv = os.path.join(here, '..', 'misc/virtenv/bin/activate_this.py')
execfile(virtualenv, dict(__file__=virtualenv))

# Control in head
import sys
sys.path.append("../misc/virtenv/lib/python2.7/site-packages")

print("virtualenv=", repr(virtualenv))
"""
import tornado.options
#import tornado.ioloop
from tornado.ioloop import IOLoop
import tornado.web
import platform
from datetime import datetime, timedelta
#import pymongo
from pymongo import Connection
import time
#from time import sleep
import signal
import logging
from mongolog.handlers import MongoHandler
from struct import unpack, calcsize


IMEI_BLACK_LIST = ('test-BLACK', 'test-BLACK2')
USE_BACKUP = True


context = zmq.Context()
publisher = context.socket(zmq.PUB)
publisher.bind("ipc:///tmp/ws_sub")
publish_stream = ZMQStream(publisher)


#push_socket.send_pyobj(msg)

#.to(host='mongodb://badenmongodb:1q2w3e@ds033257.mongolab.com:33257/baden_test', port=33257, db='baden_test', collection='log')

#logging.getLogger().setLevel(logging.DEBUG)

#log = logging.getLogger('tornado.general')
#log.setLevel(logging.DEBUG)

#log.addHandler(MongoHandler.to(host='mongodb://badenmongodb:1q2w3e@ds033257.mongolab.com:33257/baden_test', port=33257, db='baden_test', collection='log'))

log = logging.getLogger('demo')
log.setLevel(logging.DEBUG)
log.addHandler(MongoHandler.to(host='mongodb://badenmongodb:1q2w3e@ds033257.mongolab.com:33257/baden_test', port=33257, db='baden_test', collection='log'))


MONGO_URL = "mongodb://badenmongodb:1q2w3e@ds033257.mongolab.com:33257/baden_test"

db = Connection(MONGO_URL).baden_test
bingps = db["bingps"]
dblog = db["log"]

bingps.ensure_index([
    ("imei", 1), ("hour", 1)
])

fake = db["fake"]

inmemcounter = 0
startedat = datetime.utcnow()

PACK_F2 = '<BBBBBBBBBBBBBBBBBBBBBBHHBBHH'
#          ^ - D0: Заголовок (должен быть == 0xFF)
#           ^ - D1: Идентификатор пакета (должен быть == 0xF2)
#            ^ - D2: Длина пакета в байтах, включая HEADER, ID и LENGTH (32)
#             ^ - D3    день    День месяца = 1..31
#              ^ D4 месяц | ((год-2010) << 4)   Месяц = 1..12 год = 0..14 → 2010..2024
#               ^ D5    Часы    Часы = 0..23
#                ^ D6   Минуты  Минуты = 0..59
#                 ^ D7  Cекунды Cекунды = 0..59
#                  ^ D8 Широта (LL) Градусы широты = 0..89
#                   ^ D9    Широта (ll) Минуты целая часть = 0..59
#                    ^ D10  Широта (mm) Минуты дробная часть1 = 0..99
#                     ^ D11 Широта (nn) Минуты дробная часть2 = 0..99
#                      ^ D12    Долгота (LLL)   Градусы долготы = 0..179
#                       ^ D13   Долгота (ll)    Минуты целая часть = 0..59
#                        ^ D14  Долгота (mm)    Минуты дробная часть1 = 0..99
#                         ^ D15 Долгота (nn)    Минуты дробная часть2 = 0..99
#                          ^ D16    D16.0 = NS  D16.1 = EW  D16.2 = (Course & 1)    D16.0=0 для N   D16.0=1 для S   D16.1=0 для E   D16.1=1 для W   D16.2=0 для четных Course   D16.2=1 для нечетных Course
#                           ^ D17   Спутники    Кол-во спутников 3..12
#                            ^ D18  Скорость    Скорость в узлах 0..239
#                             ^ D19 Скорость дробная часть  Дробная часть скорости 0..99
#                              ^ D20    Направление Направление/2 = 0..179
#                               ^ D21   Направление дробная часть   Дробная часть направления 0..99
#                                ^ D22, D23 Напряжение внешнего питания Напряжение/100 = 0..2000    D22 – младшая часть D23 – старшая часть
#                                  ^ D24, D25   Напряжение внутреннего аккумулятора Напряжение/100 = 0..5000    D24 – младшая часть D25 – старшая часть
#                                    ^ D26  Зарезервировано =0
#                                     ^ D27 Тип точки   Причина фиксации точки
#                                      ^ D28, D29   Неточное смещение   Смещение относительно точного времени в секундах. Значение 0xFFFF означает превышение лимита и должно игнорироваться если это возможно.
#                                        ^ D30, D31  Зарезервировано =0 (фотодатчик)

assert(calcsize(PACK_F2) == 32)


CRC16_CCITT_table = (
        0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7, 0x8108, 0x9129, 0xa14a, 0xb16b,
        0xc18c, 0xd1ad, 0xe1ce, 0xf1ef, 0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
        0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de, 0x2462, 0x3443, 0x0420, 0x1401,
        0x64e6, 0x74c7, 0x44a4, 0x5485, 0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
        0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4, 0xb75b, 0xa77a, 0x9719, 0x8738,
        0xf7df, 0xe7fe, 0xd79d, 0xc7bc, 0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
        0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b, 0x5af5, 0x4ad4, 0x7ab7, 0x6a96,
        0x1a71, 0x0a50, 0x3a33, 0x2a12, 0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
        0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41, 0xedae, 0xfd8f, 0xcdec, 0xddcd,
        0xad2a, 0xbd0b, 0x8d68, 0x9d49, 0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
        0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78, 0x9188, 0x81a9, 0xb1ca, 0xa1eb,
        0xd10c, 0xc12d, 0xf14e, 0xe16f, 0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
        0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e, 0x02b1, 0x1290, 0x22f3, 0x32d2,
        0x4235, 0x5214, 0x6277, 0x7256, 0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
        0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405, 0xa7db, 0xb7fa, 0x8799, 0x97b8,
        0xe75f, 0xf77e, 0xc71d, 0xd73c, 0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
        0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab, 0x5844, 0x4865, 0x7806, 0x6827,
        0x18c0, 0x08e1, 0x3882, 0x28a3, 0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
        0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92, 0xfd2e, 0xed0f, 0xdd6c, 0xcd4d,
        0xbdaa, 0xad8b, 0x9de8, 0x8dc9, 0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
        0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8, 0x6e17, 0x7e36, 0x4e55, 0x5e74,
        0x2e93, 0x3eb2, 0x0ed1, 0x1ef0
        )


def CRC16(crc, data):
    """ Compute correct enough :grin: CRC16 CCITT for using in BF2142 auth token """
    return (((crc << 8) & 0xff00) ^ CRC16_CCITT_table[((crc >> 8) ^ (0xff & data))])


def DecodePoint(data):
    (
        p_head,     # D0: Заголовок (должен быть == 0xFF)
        p_id,       # D1: Идентификатор пакета (должен быть == 0xF2)
        p_len,      # D2: Длина пакета в байтах, включая HEADER, ID и LENGTH (32)
        day,        # D3    день    День месяца = 1..31
        p_my,       # D4 месяц | ((год-2010) << 4)   Месяц = 1..12 год = 0..14 → 2010..2024
        hours,      # D5    Часы    Часы = 0..23
        minutes,    # D6   Минуты  Минуты = 0..59
        seconds,    # D7  Cекунды Cекунды = 0..59
        p_lat1,     # D8 Широта (LL) Градусы широты = 0..89
        p_lat2,     # D9    Широта (ll) Минуты целая часть = 0..59
        p_lat3,     # D10  Широта (mm) Минуты дробная часть1 = 0..99
        p_lat4,     # D11 Широта (nn) Минуты дробная часть2 = 0..99
        p_lon1,     # D12    Долгота (LLL)   Градусы долготы = 0..179
        p_lon2,     # D13   Долгота (ll)    Минуты целая часть = 0..59
        p_lon3,     # D14  Долгота (mm)    Минуты дробная часть1 = 0..99
        p_lon4,     # D15 Долгота (nn)    Минуты дробная часть2 = 0..99
        p_nsew,     # D16    D16.0 = NS  D16.1 = EW  D16.2 = (Course & 1)    D16.0=0 для N   D16.0=1 для S   D16.1=0 для E   D16.1=1 для W   D16.2=0 для четных Course   D16.2=1 для нечетных Course
        sats,       # D17   Спутники    Кол-во спутников 3..12
        p_speed,    # D18  Скорость    Скорость в узлах 0..239
        p_speed2,   # D19 Скорость дробная часть  Дробная часть скорости 0..99
        p_course,   # D20    Направление Направление/2 = 0..179
        p_course2,  # D21   Направление дробная часть   Дробная часть направления 0..99
        vout,       # D22, D23 Напряжение внешнего питания Напряжение/100 = 0..2000    D22 – младшая часть D23 – старшая часть
        vin,        # D24, D25   Напряжение внутреннего аккумулятора Напряжение/100 = 0..5000    D24 – младшая часть D25 – старшая часть
        p_res1,     # D26  Зарезервировано =0
        fsource,    # D27 Тип точки   Причина фиксации точки
        toffset,    # D28, D29   Неточное смещение   Смещение относительно точного времени в секундах. Значение 0xFFFF означает превышение лимита и должно игнорироваться если это возможно.
        photo       # D30, D31  Зарезервировано (используется для данных с фотодатчика)
    ) = unpack(PACK_F2, data)

    month = p_my & 0x0F
    year = (p_my & 0xF0) / 16 + 2010
    try:
        datestamp = datetime(year, month, day, hours, minutes, seconds)
    except ValueError, strerror:
        log.error("GPS_PARSE_ERROR: error datetime (%s): [%s]" % (strerror, data.encode('hex')))
        return None     # LENGTH

    if datestamp > datetime.now() + timedelta(days=1):
        log.error("GPS_PARSE_ERROR: error datetime: future point [%s]" % data.encode('hex'))
        return None

    latitude = float(p_lat1) + (float(p_lat2) + float(p_lat3 * 100 + p_lat4) / 10000.0) / 60.0
    longitude = float(p_lon1) + (float(p_lon2) + float(p_lon3 * 100 + p_lon4) / 10000.0) / 60.0
    if p_nsew & 1:
        latitude = -latitude
    if p_nsew & 2:
        longitude = -longitude

    speed = (float(p_speed) + float(p_speed2) / 100.0) * 1.852  # Переведем в км/ч
    if p_nsew & 4:
        course = float(p_course * 2 + 1) + float(p_course2) / 100.0
    else:
        course = float(p_course * 2) + float(p_course2) / 100.0

    #altitude = 0.0

    error = False

    if latitude > 90.0:
        error = True
    if latitude < -90.0:
        error = True
    if longitude > 180.0:
        error = True
    if longitude < -180.0:
        error = True

    if error:
        log.error("Corrupt latitude or longitude %f, %f, [%s]" % (latitude, longitude, data.encode('hex')))
        return None

    if sats < 3:
        log.error("No sats. [%s]" % data.encode('hex'))
        return None

    vout /= 100
    vin /= 10

    if toffset != 0:
        if toffset == 0xFFFF:
            log.error("Toffset is 0xFFFF")
        else:
            log.warning("Used toffset (%d seconds)" % toffset)
            datestamp += timedelta(seconds=toffset)

    point = {
        'time': time.mktime(datestamp.timetuple()),
        'lat': latitude,
        'lon': longitude,
        'sats': sats,
        'speed': speed,
        'course': course,
        'vout': vout,
        'vin': vin,
        'fsource': fsource,
        'photo': photo
    }
    return point


#tornado.web import Application, RequestHandler, asynchronous
class BinGps(tornado.web.RequestHandler):
    def initialize(self, bingps):
        self.bingps = bingps

    def options(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type, X-Requested-With, Content-Length')

    def post(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        imei = self.get_argument("imei", None)

        if imei in IMEI_BLACK_LIST:
            log.error("IMEI in black list. Denied. [%s]" % imei)
            self.write('BINGPS: DENIED\r\n')
            return

        dataid = int(self.get_argument('dataid', '0'), 16)

        pdata = self.request.body

        _log = 'LOGS:'
        _log += "\n pdata len=%s" % len(pdata)
        _log += "\n data id=%s" % dataid
        #_log += "\n os.environ: %s" % repr(os.environ)
        _log += "\n headers: %s" % repr(self.request.headers)
        _log += "\n arguments: %s" % self.request.arguments
        #_log += "\n body: %s" % len(self.request.body)
        _log += "\n pbody: %s" % len(pdata)
        _log += "\n Remote IP: %s" % str(self.request.remote_ip)
        #_log += "Request info: %s\n" % str(self.request.content_type)
        #_log += "\n self=%s" % dir(self)
        _log += "\n IMEI=%s" % imei

        #skey = DBSystem.key_by_imei(imei)

        '''
        if 'Content-Type' in self.request.headers:
            if "application/x-www-form-urlencoded" in self.request.headers['Content-Type']:
                #pdata = unquote_plus(self.request.body.replace('=',''))
                pdata = unquote_plus(pdata.replace('=&', '&'))

                _log += "\n headers: %s" % repr(self.request.headers)
                _log += '\n pdata len = %d  content-length = %d (%s) ' % (len(pdata), int(self.request.headers['Content_Length']), self.request.headers['Content_Length'])

                if (len(pdata) == (int(self.request.headers['Content_Length']) + 1)) and (pdata[-1] == '='):
                    pdata = pdata[:-1]
                _log += '\n data reencoded'
            else:
                #pdata = self.request.body
                _log += '\n raw data'
        '''

        if len(pdata) < 3:
            log.error('Data packet is too small or miss.')
            self.response.write('BINGPS: CRCERROR\r\n')
            return

        crc = ord(pdata[-1]) * 256 + ord(pdata[-2])
        pdata = pdata[:-2]

        crc2 = 0
        for byte in pdata:
            crc2 = CRC16(crc2, ord(byte))

        if USE_BACKUP:
            _log += '\n Saving to backup'
            pass

        if crc != crc2:
            _log += '\n Warning! Calculated CRC: 0x%04X but system say CRC: 0x%04X. (Now error ignored.)' % (crc2, crc)
            _log += '\n Original data (HEX):'
            odata = self.request.body
            for data in odata:
                _log += ' %02X' % ord(data)
            logging.info(_log)

            _log = '\n Encoded data (HEX):'
            for data in pdata:
                _log += ' %02X' % ord(data)
            logging.info(_log)

            self.response.write('BINGPS: CRCERROR\r\n')
            return
        else:
            _log += '\n CRC OK %04X' % crc

        log.info(_log)

        plen = len(pdata)
        offset = 0
        lastpoint = None
        while offset < plen:
            if pdata[offset] != '\xFF':
                offset += 1
                continue

            if pdata[offset + 1] == '\xF2':
                point = DecodePoint(pdata[offset:offset + 32])
                offset += 32
                if point is not None:
                    lastpoint = point
                    log.info('=== Point=%s' % repr(point))

        if lastpoint is not None:
            msg = {
                "id": 0,
                "message": "last_update",
                "point": lastpoint
            }
            log.info('=== Inform=%s' % repr(msg))
            #push_socket.send_pyobj(msg)
            publish_stream.send_pyobj(msg)

        self.write("BINGPS: NOFUNC\r\n")

    def get(self):
        self.write("BINGPS: NOFUNC\r\n")


class Logs(tornado.web.RequestHandler):
    def initialize(self, dblog):
        self.dblog = dblog

    def get(self):
        logs = dblog.find().sort("time", -1).limit(100)
        self.write("""
            <!doctype html>
            <html>
            <head>
            <link href="//netdna.bootstrapcdn.com/twitter-bootstrap/2.2.2/css/bootstrap-combined.min.css" rel="stylesheet">
            </head>
            <body>
            <table class="table table-bordered table-striped table-hover" style="word-wrap: break-word;">
            <thead>
                <tr><th style="width:50px">Level</th><th>module</th><th>Message</th><th>File:line</th><th>Time</th></tr>
            </thead>
            <tbody>
        """)
        for l in logs:
            code = '<div style="max-width: 400px;">'
            for r in l["message"].split('\n'):
                code += '<p>%s</p>' % r
            code += '</div>'
            self.write('<tr>')
            self.write("<td>%s</td>" % l["levelname"])
            self.write("<td>%s</td>" % l["module"])
            self.write("<td>%s</td>" % code)
            self.write("<td>%s:%s</td>" % (l["filename"], l["lineno"]))
            self.write("<td>%s</td>" % str(l["time"]))
            #self.write("<td>%s</td>" % repr(l))
            self.write("</tr>")
        self.write("""
            </tbody>
            </table>
            </body>
            </html>
        """)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        global inmemcounter, startedat
        inmemcounter += 1
        self.set_header("Cache-control", "no-cache")
        self.write("""
            <h2>Its five REworked!</h2>
            <p>Point server2</p>
            <p><b>DB:</b> %s</p>
            <p><b>COL:</b> %s</p>
            <p><b>Started at:</b> %s</p>
            <p><b>Global counter:</b> %d</p>
            """ % (repr(db), repr(fake), str(startedat), inmemcounter))

        fall = fake.find_one({"_id": "counter"})
        if fall is None:
            fall = {"_id": "counter", "value": 0}
        else:
            fall["value"] += 1
        self.write("<p><b>Mongo counter:</b> %s</p>" % repr(fall["value"]))
        fake.save(fall)

        self.write("<h2>Platform information</h2>")
        self.write("<p><b>System:</b> %s</p>" % platform.system())
        self.write("<p><b>Process ID:</b> %s</p>" % str(os.getpid()))
        self.write("<p><b>Release:</b> %s</p>" % platform.release())
        self.write("<p><b>Version:</b> %s</p>" % platform.version())
        self.write("<p><b>Machine:</b> %s</p>" % platform.machine())
        self.write("<p><b>Processor:</b> %s</p>" % platform.processor())
        self.write("<p><b>Node:</b> %s</p>" % platform.node())
        self.write("<p><b>Python:</b> %s</p>" % platform.python_version())
        self.write("<p><b>Port:</b> %s</p>" % os.environ.get('PORT', 5000))

        self.write("<h2>Memory information</h2>")
        for m in open('/proc/meminfo'):
            self.write("<p>%s</p>" % m)


class MyApplication(tornado.web.Application):
    def log_request(self, handler):

        if handler.get_status() < 400:
            log_method = log.info
        elif handler.get_status() < 500:
            log_method = log.warn
        else:
            log_method = log.error

        request_time = 1000.0 * handler.request.request_time()
        log_message = '%d %s %.2fms' % (handler.get_status(), handler._request_summary(), request_time)
        log_method(log_message)
        #print ' LOG:%s' % log_message


#application = tornado.web.Application([
application = MyApplication([
    (r"/", MainHandler),
    (r"/bingps", BinGps, dict(bingps=bingps)),
    (r"/logs", Logs, dict(dblog=dblog)),
], debug=True)

#tornado.web.Application.log_request = MongoHandler

#print repr(application.log_request)
#application.log_request = MongoHandler.to(host='mongodb://badenmongodb:1q2w3e@ds033257.mongolab.com:33257/baden_test', port=33257, db='baden_test', collection='log')
#application.log_request = MongoHandler
#.to(host='mongodb://badenmongodb:1q2w3e@ds033257.mongolab.com:33257/baden_test', port=33257, db='baden_test', collection='log')


#log.debug('Start point.navi.cc server.')
#tornado.options.parse_command_line()
'''
    log.debug("1 - debug message")
    log.info("2 - info message")
    log.warn("3 - warn message")
    log.error("4 - error message")
    log.critical("5 - critical message")
'''


def sig_handler(sig, frame):
    """Catch signal and init callback.

    More information about signal processing for graceful stoping
    Tornado server you can find here:
    http://codemehanika.org/blog/2011-10-28-graceful-stop-tornado.html
    """
    logging.warning('Caught signal: %s', sig)
    IOLoop.instance().add_callback(shutdown)


def shutdown():
    """Stop server and add callback to stop i/o loop"""
    io_loop = IOLoop.instance()

    #logging.info('Stopping server')
    #io_loop.stop()
    # Can add some stop tasks here.

    logging.info('Will shutdown in 1 seconds ...')
    io_loop.add_timeout(time.time() + 1, io_loop.stop)


def main():
    log.info("starting torando web server")

    #signal.signal(signal.SIGTERM, sig_handler)
    #signal.signal(signal.SIGINT, sig_handler)

    address = os.environ.get('INTERNAL_IP', '0.0.0.0')
    port = int(os.environ.get('INTERNAL_POINT_PORT', '8181'))
    application.listen(port, address=address)
    try:
        IOLoop.instance().start()
    except KeyboardInterrupt:
        IOLoop.instance().stop()
        #io_loop.stop()
        logging.info('Exit application')
    publish_stream.close()


if __name__ == '__main__':
    tornado.options.parse_command_line()
    main()
