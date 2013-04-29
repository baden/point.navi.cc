#!/usr/bin/env python
# -*- coding: utf-8 -

#from bisect import insort
from base import DBBase
import logging


from struct import pack, calcsize

# Условно версия №2 протокола
PACK_02 = '<HBBBBBBBBBBBBBBBBBBBBBHHBBHH'
#           ^ - D0: Заголовок (должен быть == 0xFFFF)
#            ^ - D1: Идентификатор пакета (должен быть == 0x02)
#             ^ - D2: Длина пакета в байтах, включая HEADER, ID и LENGTH (32)
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



def packPoint(point):
    pack_make('head', )
    point = {
        point['time']
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



class BinGPS(DBBase):
    def __init__(self):
        super(BinGPS, self).__init__()
        self.collection.ensure_index([
            ("skey", 1), ("hour", 1)
        ])

    @classmethod
    def packer(cls, skey):
        bingps = cls()
        bingps.skey = skey
        bingps.packet = {}
        return bingps

    def add_point_to_packer(self, point):
        hour = int(point['time'] // 3600)
        if hour not in self.packet:
            self.packet[hour] = []
        #insort(self.packet[hour].append(point)
        self.packet[hour].append(point)

    def save_packer(self):
        # TODO! Batch operations
        logging.info('BinGPS.save_packer(%s)', self.skey)
        for hour, data in self.packet.iteritems():
            for packet in data:
                logging.info('BinGPS.save_packer.update(%s, %s)', self.skey, str(packet))
                self.collection.update({'skey': self.skey, 'hour': hour}, {"$push": {"data": packet}}, True)
