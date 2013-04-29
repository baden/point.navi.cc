#!/usr/bin/env python
# -*- coding: utf-8 -

from struct import unpack, calcsize
from datetime import datetime, timedelta
import time
#from db import DB
import logging
from config import USE_BACKUP
from utils import CRC16
from db.bingps import BinGPS

from route import Route
from base import BaseHandler


print ":handlers:bingps"

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
        logging.error("GPS_PARSE_ERROR: error datetime (%s): [%s]" % (strerror, data.encode('hex')))
        return None     # LENGTH

    if datestamp > datetime.now() + timedelta(days=1):
        logging.error("GPS_PARSE_ERROR: error datetime: future point [%s]" % data.encode('hex'))
        return None

    #latitude = float(p_lat1) + (float(p_lat2) + float(p_lat3 * 100 + p_lat4) / 10000.0) / 60.0
    latitude = (p_lat1 * 60 + p_lat2) * 10000 + p_lat3 * 100 + p_lat4
    #longitude = float(p_lon1) + (float(p_lon2) + float(p_lon3 * 100 + p_lon4) / 10000.0) / 60.0
    longitude = (p_lon1 * 60 + p_lon2) * 10000 + p_lon3 * 100 + p_lon4
    if p_nsew & 1:
        latitude = -latitude
    if p_nsew & 2:
        longitude = -longitude

    #speed = (float(p_speed) + float(p_speed2) / 100.0) * 1.852  # Переведем в км/ч
    speed = p_speed * 100 + p_speed2
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
        logging.error("Corrupt latitude or longitude %f, %f, [%s]" % (latitude, longitude, data.encode('hex')))
        return None

    if sats < 3:
        logging.error("No sats. [%s]" % data.encode('hex'))
        return None

    vout /= 100
    vin /= 10

    if toffset != 0:
        if toffset == 0xFFFF:
            logging.error("Toffset is 0xFFFF")
        else:
            logging.warning("Used toffset (%d seconds)" % toffset)
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


@Route(r"/bingps")
class BinGps(BaseHandler):
    def onpost(self):
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
        _log += "\n IMEI=%s" % self.imei
        _log += "\n skey=%s" % self.skey

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
            logging.error('Data packet is too small or miss.')
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

            self.write('BINGPS: CRCERROR\r\n')
            return
        else:
            _log += '\n CRC OK %04X' % crc

        logging.info(_log)

        plen = len(pdata)
        #packer = Packer()
        packer = BinGPS.packer(self.skey)
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
                    packer.add_point_to_packer(point)
                    lastpoint = point
                    logging.info('=== Point=%s' % repr(point))

        packer.save_packer()

        if lastpoint is not None:
            msg = {
                "id": 0,
                "message": "last_update",
                "skey": self.skey,
                "point": lastpoint
            }
            self.application.publisher.send(msg)

        self.write("BINGPS: OK\r\n")

    def get(self):
        self.write("BINGPS: NOFUNC\r\n")
