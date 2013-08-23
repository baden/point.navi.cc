#!/usr/bin/env python
# -*- coding: utf-8 -

# from bisect import insort
# import logging
import time
from base import DBBase
from bson import Binary
from zlib import compress
# from struct import pack, calcsize
# from struct import unpack_from

class BinGPS(DBBase):
    def __init__(self):
        super(BinGPS, self).__init__()
        self.collection.ensure_index([
            ("skey", 1), ("hour", 1)
        ])
        self.buffer = self.db[self.__class__.__name__ + "_buffer"]
        # Индекс для выборки по системе с сортировкой по мере наполнения
        # Если его работа будет неудовлетворительной, то можно добавить искуственное поле с меткой времени
        # self.buffer.ensure_index([
        #     ("skey", 1), ("_id", 1)
        # ])

        # Индекс для выборки по системе с сортировкой по мере наполнения
        # ts = long(time.time()*1e6)
        self.buffer.ensure_index([
            ("skey", 1), ("ts", 1)
        ])

    @classmethod
    def packer(cls, skey):
        bingps = cls()
        bingps.skey = skey
        bingps.packet = {}
        return bingps

    def add_point_to_packer(self, point, hour):
        if hour not in self.packet:
            self.packet[hour] = ""
        self.packet[hour] += point

    def free_buffer(self, hour, data):
        # Я искренне надеюсь что будет сохранен натуральные порядок, иначе нужно будет добавить правило сортировки
        # c = self.buffer.find({'skey': self.skey}).sort("_id", 1)
        c = self.buffer.find({'skey': self.skey}).sort("ts", 1)
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
        self.buffer.save({
            'skey': self.skey,
            'hour': hour,
            'ts': long(time.time()*1e6),
            'data': Binary(data)
        })

        # Сохраним значение последнего часа
        self.redis.set('%s.%s.lasthour' % (self.__class__.__name__, self.skey), hour)

    def save_hour(self, hour, data):
        lasthour = self.redis.get('%s.%s.lasthour' % (self.__class__.__name__, self.skey))
        if lasthour is not None:
            lasthour = int(lasthour)
            if lasthour == hour:
                # self.buffer.save({'skey': self.skey, 'hour': hour, "data": Binary(data)})
                self.buffer.save({
                    'skey': self.skey,
                    'hour': hour,
                    'ts': long(time.time()*1e6),
                    'data': Binary(data)
                })
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
