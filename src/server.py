#!/usr/bin/env python

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
import tornado.ioloop
import tornado.web
import platform
from datetime import datetime, timedelta
#import pymongo
from pymongo import Connection
from time import sleep

MONGO_URL = "mongodb://badenmongodb:1q2w3e@ds033257.mongolab.com:33257/baden_test"

db = Connection(MONGO_URL).baden_test
fake = db["fake"]

inmemcounter = 0
startedat = datetime.utcnow()


#tornado.web import Application, RequestHandler, asynchronous
class LongPollHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        lines = ['line 1\n', 'line 2\n']

        def send():
            try:
                self.write(lines.pop(0))
                self.write("pid:[%s]" % str(os.getpid()))
                self.flush()
                if len(lines) == 0:
                    self.finish()
                    return
            except:
                self.finish()
            else:
                tornado.ioloop.IOLoop.instance().add_timeout(timedelta(0, 20), send)
        send()


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
        sleep(1)

application = tornado.web.Application([
    (r"/", MainHandler), (r"/longpoll", LongPollHandler)
], debug=True)

if __name__ == "__main__":
    address = os.environ.get('OPENSHIFT_INTERNAL_IP', '0.0.0.0')
    application.listen(8181, address=address)
    tornado.ioloop.IOLoop.instance().start()
