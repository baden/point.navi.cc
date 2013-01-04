#!/usr/bin/env python
# -*- coding: utf-8 -

from tornado.web import RequestHandler
from route import Route


@Route(r"/logs")
class Logs(RequestHandler):
    def get(self):
        self.set_header("Cache-control", "no-cache")
        level = self.get_argument("level", None)
        if level is not None:
            logs = self.application.dblog.find({"levelname": level}).sort("time", -1).limit(100)
        else:
            logs = self.application.dblog.find().sort("time", -1).limit(100)
        self.write("""
            <!doctype html>
            <html>
            <head>
            <link rel="icon" type="image/gif" href="data:image/gif;base64,R0lGODlhEAAQAIAAAAAAAAAAACH5BAkAAAEALAAAAAAQABAAAAIgjI+py+0PEQiT1lkNpppnz4HfdoEH2W1nCJRfBMfyfBQAOw==" />
            <link href="//netdna.bootstrapcdn.com/twitter-bootstrap/2.2.2/css/bootstrap-combined.min.css" rel="stylesheet">
            <style>
                a { padding: 18px;}
                pre {padding: 0;}
                .INFO {color: blacl;}
                .WARNING {color: green; }
                .ERROR {color: red; }
                .DEBUG {color: grey; }
            </style>
            </head>
            <body>
            <a href="/logs">All</a>
            <a href="/logs?level=INFO">INFO</a>
            <a href="/logs?level=WARNING">WARNING</a>
            <a href="/logs?level=ERROR">ERROR</a>
            <ul>
        """)
        #self.write("<li>:Logs: %s</li>" % dir(self.application))
        for l in logs:
            self.write('<li><span class="%s"><b>%s</b> %s %s %s %s</span>' % (l["levelname"], str(l["time"]), l["levelname"], l["module"], l["filename"], l["lineno"]))
            #self.write("<td>%s</td>" % repr(l))
            self.write("<pre>%s</pre>" % l["message"])
            if l["exc_info"] is not None:
                self.write("<pre>%s</pre>" % l["exc_info"])
            self.write("</li>")
        self.write("""
            </ul>
            </body>
            </html>
        """)


class Logs2(RequestHandler):
    def initialize(self, dblog):
        self.dblog = dblog

    def get(self):
        logs = self.dblog.find().sort("time", -1).limit(100)
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
