#!/usr/bin/env python
# -*- coding: utf-8 -


import redis
r = redis.StrictRedis(host='localhost', port=6379, db=0)
r.set('foo', 'bar')
r.get('foo')
