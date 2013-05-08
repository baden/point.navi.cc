#!/usr/bin/env python
# -*- coding: utf-8 -

#from bisect import insort
from base import DBBase
import logging

from bson import Binary
from zlib import compress
# from struct import pack, calcsize
from struct import unpack_from

# Условно версия №2 протокола
# PACK_02 = '<HBBBBBBBBBBBBBBBBBBBBBHHBBHH'
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


# def packPoint(point):
#     pack_make('head', )
#     point = {
#         point['time']
#         'lat': latitude,
#         'lon': longitude,
#         'sats': sats,
#         'speed': speed,
#         'course': course,
#         'vout': vout,
#         'vin': vin,
#         'fsource': fsource,
#         'photo': photo
#     }

class BinGPS(DBBase):
    def __init__(self):
        super(BinGPS, self).__init__()
        self.collection.ensure_index([
            ("skey", 1), ("hour", 1)
        ])
        self.buffer = self.db[self.__class__.__name__ + "_buffer"]
        # Индекс для выборки по системе с сортировкой по мере наполнения
        # Если его работа будет неудовлетворительной, то можно добавить искуственное поле с меткой времени
        self.buffer.ensure_index([
            ("skey", 1), ("_id", 1)
        ])

    @classmethod
    def packer(cls, skey):
        bingps = cls()
        bingps.skey = skey
        bingps.packet = {}
        return bingps

    def add_point_to_packer(self, point):
        hour = unpack_from("<I", point, 3)[0] // 3600  # TODO! Не самое элегантное решение
        if hour not in self.packet:
            self.packet[hour] = ""
        self.packet[hour] += point

    def free_buffer(self, hour, data):
        # Я искренне надеюсь что будет сохранен натуральные порядок, иначе нужно будет добавить правило сортировки
        c = self.buffer.find({'skey': self.skey}).sort("_id", 1)
        # Предполагаем что в буффере могут быть данные и за другие часы
        datas = {}
        removeids = []
        for r in c:
            removeids.append(r["_id"])
            if r['hour'] not in datas:
                datas[r['hour']] = r['data']
            else:
                datas[r['hour']] += r['data']

        # Добавим только что полученные данные
        # if hour not in datas:
        #     datas[hour] = data
        # else:
        #     datas[hour] += data

        # Сохраним все пакеты из буффера
        for (h, d) in datas.iteritems():
            # Тут возможны варианты: или добавлять в существующую запись (mongo производит копирование документа)
            # Или добавлять запись
            # В первом варианте необходима периодическая процедура db.repairDatabase()
            # Во втором варианте получение записей может занимать больше времени
            self.collection.update({'skey': self.skey, 'hour': h}, {"$push": {"data": Binary(compress(d))}}, True)

            # self.collection.save({'skey': self.skey, 'hour': h}, {"data": Binary(d)})

        # Удалим пакеты из буффера
        self.buffer.remove({"_id": {"$in": removeids}})

        # Сохраним полученный пакет
        self.buffer.save({'skey': self.skey, 'hour': hour, "data": Binary(data)})

        # Сохраним значение последнего часа
        self.redis.set('%s.%s.lasthour' % (self.__class__.__name__, self.skey), hour)

    def save_hour(self, hour, data):
        lasthour = self.redis.get('%s.%s.lasthour' % (self.__class__.__name__, self.skey))
        if lasthour is not None:
            lasthour = int(lasthour)
            if lasthour == hour:
                self.buffer.save({'skey': self.skey, 'hour': hour, "data": Binary(data)})
            else:
                self.free_buffer(hour, data)
        else:
            self.free_buffer(hour, data)

    def save_packer(self):
        # TODO! Batch operations
        for hour, data in self.packet.iteritems():
            self.save_hour(hour, data)
            # self.collection.update({'skey': self.skey, 'hour': hour}, {"$push": {"data": Binary(data)}}, True)
            # self.collection.save({'skey': self.skey, 'hour': hour, "data": Binary(data)})
