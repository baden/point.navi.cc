#!/usr/bin/env python
# -*- coding: utf-8 -

from struct import unpack_from, pack, unpack, calcsize
from datetime import datetime, timedelta, tzinfo
import time
#from db import DB
import logging
from config import USE_BACKUP
from utils import CRC16
from db.bingps import BinGPS

from route import Route
from base import BaseHandler
from db import sinform


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

PACK_F4 = '<BBBIIIHBBHHBHIBB'
#           ^ - D0: Заголовок (должен быть == 0xFF)
#            ^ - D1: Идентификатор пакета (должен быть == 0xC1)
#             ^ - D2: Длина пакета в байтах, включая HEADER, ID и LENGTH (32)
#              ^ - D3: Дата+время
#               ^ - D4: Широта 1/10000 минут
#                ^ - D5: Долгота 1/10000 минут
#                 ^ - D6: Скорость 1/100 узла
#                  ^ - D7: Направление/2 = 0..179
#                   ^ - D8: Кол-во спутников 3..12
#                    ^ - D9: Напряжение внешнего питания 1/100 B
#                     ^ - D10: Напряжение внутреннего аккумулятора 1/100 B
#                      ^ - D11: Тип точки   Причина фиксации точки
#                       ^ - D12: Флаги
#                        ^ - D13: Резерв
#                         ^ - D14: Резерв
#                          ^ - D15: Локальная CRC
assert(calcsize(PACK_F4) == 32)

PACK_F5 = '<BBBBIIIHHHBBHBBBBBB'
#           ^ - D0:B Заголовок (должен быть == 0xFF)
#            ^ - D1:B Идентификатор пакета (должен быть == 0xC2)
#             ^ - D2:B Тип точки   Причина фиксации точки (младшие 6 бит, бит 7 - фиксация без активных спутников.
#              ^ - D3:B Кол-во спутников 3..12
#               ^ - D4:I Дата+время (unixtime)
#                ^ - D5:I Широта 1/10000 минут
#                 ^ - D6:I Долгота 1/10000 минут
#                  ^ - D7:H Скорость 1/100 узла
#                   ^ - D8:H Высота над уровнем моря (-30000...30000)
#                    ^ - D9:B Направление/2 = 0..179
#                     ^ - D10:B Напряжение внешнего питания 1/10 B  (0.0-102.3) старшие 8 бит.
#                      ^ - D11:B Напряжение внутреннего аккумулятора 1/100 B   (0.00-10.23) старшие 8 бит
#                       ^ - D12:B АЦП1 (Температура?) старшие 8 бит
#                        ^ - D13:B АЦП2 (Уровень топлива) старшие 8 бит
#                         ^ - D14:B Младщие биты полей D10..D13 (4 x 2 бита) (((26)))
#                          ^ - D15:B Резерв  (АЦП3 (Вход 3))
#                           ^ - D16:B Резерв  (АЦП1..3lsb (младшие биты: 3 x 2 младших бита))
#                            ^ - D17:B Резерв
#                             ^ - D18:B Резерв
#                              ^ - D19:B Резерв
#                               ^ - D20:B Локальная CRC (сумма всех байтов пакета, младший разряд)
assert(calcsize(PACK_F5) == 32)

# -------------------------------
# Тип точки - 5 бит. Три старших бита используются для других целей. Старший бит - фиксация точки без координат.


# -------------------------------

# ZERO = timedelta(0)

# # A UTC class.

# class UTC(tzinfo):
#     """UTC"""

#     def utcoffset(self, dt):
#         return ZERO

#     def tzname(self, dt):
#         return "UTC"

#     def dst(self, dt):
#         return ZERO

# utc = UTC()

# TODO! Эта конструкция небезопасна в плане перехода на зимнее-летнее время
tzdelta = datetime.now() - datetime.utcnow()

def UpdatePoint(buffer, offset):
    # Обновляет пакет со старого формата F2 на новый F4
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
    ) = unpack_from(PACK_F2, buffer, offset)

    month = p_my & 0x0F
    year = (p_my & 0xF0) / 16 + 2010
    try:
        # datestamp = datetime(year, month, day, hours, minutes, seconds, 0, utc)
        datestamp = datetime(year, month, day, hours, minutes, seconds) + tzdelta
    except ValueError, strerror:
        logging.error("GPS_PARSE_ERROR: error datetime (%s): [%s]" % (strerror, data.encode('hex')))
        return None     # LENGTH

    # if datestamp > datetime.now(utc) + tzdelta + timedelta(days=1):
    if datestamp > datetime.now() + tzdelta + timedelta(days=1):
        logging.error("GPS_PARSE_ERROR: error datetime: future point [%s]" % repr(datestamp))
        return None

    latitude = (p_lat1 * 60 + p_lat2) * 10000 + p_lat3 * 100 + p_lat4
    # latitude = float(p_lat1) + (float(p_lat2) + float(p_lat3 * 100 + p_lat4) / 10000.0) / 60.0

    # longitude = float(p_lon1) + (float(p_lon2) + float(p_lon3*100 + p_lon4)/10000.0)/60.0
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

    # if latitude > 90.0:
    if latitude > 90 * 60 * 10000:
        error = True
    # if latitude < -90.0:
    if latitude < -90 * 60 * 10000:
        error = True
    # if longitude > 180.0:
    if longitude > 180 * 60 * 10000:
        error = True
    # if longitude < -180.0:
    if longitude < -180 * 60 * 10000:
        error = True

    if error:
        logging.error("Corrupt latitude or longitude %f, %f, [%s]" % (latitude, longitude, data.encode('hex')))
        return None

    # if sats < 3:
    #     logging.error("No sats. [%s]" % data.encode('hex'))
    #     return None

    #vout /= 100
    #vin /= 10

    if toffset != 0:
        if toffset == 0xFFFF:
            logging.error("Toffset is 0xFFFF")
        else:
            logging.warning("Used toffset (%d seconds)" % toffset)
            datestamp += timedelta(seconds=toffset)

    # point = {
    #     'time': time.mktime(datestamp.timetuple()),
    #     'lat': latitude,
    #     'lon': longitude,
    #     'sats': sats,
    #     'speed': speed,
    #     'course': course,
    #     'vout': vout,
    #     'vin': vin,
    #     'fsource': fsource,
    #     'photo': photo
    # }

    dt = time.mktime(datestamp.timetuple())

    point = pack(
        PACK_F4,
        0xFF,                   # D0: Заголовок (должен быть == 0xFF)
        0xF4,                   # D1: Идентификатор пакета (должен быть == 0xF4)
        32,                     # D2: Длина пакета в байтах, включая HEADER, ID и LENGTH (32)
        dt,                     # D3: Дата+время
        latitude,               # D4: Широта 1/10000 минут
        longitude,              # D5: Долгота 1/10000 минут
        speed,                  # D6: Скорость 1/100 узла
        int(round(course/2)),   # D7: Направление/2 = 0..179
        sats,                   # D8: Кол-во спутников 3..12
        vout,                   # D9: Напряжение внешнего питания 1/100 B
        vin,                    # D10: Напряжение внутреннего аккумулятора 1/100 B
        fsource,                # D11: Тип точки   Причина фиксации точки
        0,                      # D12: Флаги
        photo,                  # D13: Резерв
        0,                      # D14: Резерв
        0                       # D15: Локальная CRC (пока не используется)
    )
    # point = {
    #     'time': time.mktime(datestamp.timetuple()),
    #     'bin': binpack,
    # }
    return point

# TODO!!! Переделать на 0xF5
def point_to_dict(point):
    (
        head,                   # D0: Заголовок (должен быть == 0xFF)
        id,                     # D1: Идентификатор пакета (должен быть == 0xF4)
        len,                    # D2: Длина пакета в байтах, включая HEADER, ID и LENGTH (только 32)
        dt,                     # D3: Дата+время (unixtime)
        latitude,               # D4: Широта 1/10000 минут
        longitude,              # D5: Долгота 1/10000 минут
        speed,                  # D6: Скорость 1/100 узла
        course,                 # D7: Направление/2 = 0..179
        sats,                   # D8: Кол-во спутников 3..12
        vout,                   # D9: Напряжение внешнего питания 1/100 B
        vin,                    # D10: Напряжение внутреннего аккумулятора 1/100 B
        fsource,                # D11: Тип точки   Причина фиксации точки
        flags,                  # D12: Флаги
        res1,                   # D13: Резерв
        res2,                   # D14: Резерв
        crc                     # D15: Локальная CRC (пока не используется)
    ) = unpack(PACK_F4, point)
    latitude = latitude / 600000.0
    longitude = longitude / 600000.0
    speed = speed * 1.852 / 100.0
    course = course * 2
    vout = vout / 100.0
    vin = vin / 100.0
    return {
        'dt': dt,
        'latitude': latitude,
        'longitude': longitude,
        'speed': speed,
        'course': course,
        'sats': sats,
        'vout': vout,
        'vin': vin,
        'fsource': fsource,
        'fuel': int(res1 / 2),
        'flags': flags
    }
#tornado.web import Application, RequestHandler, asynchronous

@Route(r"/bingps")
class BinGps(BaseHandler):
    def onpost(self):
        dataid = int(self.get_argument('dataid', '0'), 16)

        pdata = self.request.body

        _log = '\n\n====\nLOGS:'
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

        if USE_BACKUP:
            _log += '\n Saving to backup (TBD)'
            _log += '\n Data (HEX):'
            for data in pdata:
                _log += ' %02X' % ord(data)
            pass

        if len(pdata) < 3:
            logging.error('Data packet is too small or miss.')
            self.write("BINGPS: CRCERROR\r\n")
            return

        crc = ord(pdata[-1]) * 256 + ord(pdata[-2])
        pdata = pdata[:-2]

        crc2 = 0
        for byte in pdata:
            crc2 = CRC16(crc2, ord(byte))

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
        lastdt = 0
        lastpoint = None
        while offset < plen:
            if pdata[offset] != '\xFF':
                offset += 1
                continue

            if pdata[offset + 1] == '\xF2':
                point = UpdatePoint(pdata, offset)
                offset += 32
                if point is not None:
                    dt = unpack_from("<I", point, 3)[0] # TODO! Не самое элегантное решение
                    logging.info("packet F2 datetime = %d" % dt)
                    packer.add_point_to_packer(point, dt // 3600)
                    lastpoint = point
                    lastdt = dt
                    # logging.info('=== Point=%s' % repr(point))

            elif pdata[offset + 1] == '\xF4':
                point = pdata[offset:offset+32]
                dt = unpack_from("<I", pdata, offset + 3)[0]   # TODO! Не самое элегантное решение
                logging.info("packet F4 datetime = %d" % dt)
                packer.add_point_to_packer(point, dt // 3600)
                offset += 32
                lastpoint = point
                lastdt = dt

            elif pdata[offset + 1] == '\xF5':
                point = pdata[offset:offset+32]
                dt = unpack_from("<I", pdata, offset + 4)[0]  # TODO! Не самое элегантное решение
                logging.info("packet F5 datetime = %d" % dt)
                if lastdt >= dt:
                    logging.error("Datetime must be grow (%d -> %d) at %d offset" % (lastdt, dt, offset))
                packer.add_point_to_packer(point, dt // 3600)
                offset += 32
                lastpoint = point
                lastdt = dt
            else:
                logging.error("Wrong packet at %d offset" % offset)

        packer.save_packer()

        if lastpoint is not None:
            asdict = point_to_dict(lastpoint)
            #system.update_dynamic(lastlat = asdict['latitude'], lastlon = asdict['longitude'], sats = asdict['sats'])
            self.system.update_dynamic(**asdict)
            msg = {
                "id": 0,
                "message": "update_dynamic",
                "skey": self.skey,
                "dynamic": asdict
            }
            self.application.publisher.send(msg)

            msg = {
                "id": 0,
                "message": "last_update",
                "skey": self.skey,
                "point": asdict
            }
            self.application.publisher.send(msg)

        for l in sinform.sinform_getall(self.skey):
            self.write("%s\r\n" % str(l))
        self.write("ADDLOG: OK\r\n")

        self.write("BINGPS: OK\r\n")

    def get(self):
        self.write("BINGPS: NOFUNC\r\n")
