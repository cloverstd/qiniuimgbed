#!/usr/bin/env python
# encoding: utf-8

import tornado.ioloop
import tornado.httpserver
import tornado.web
from tornado.util import ObjectDict
from tornado.options import options, define, parse_command_line
from tornado.gen import coroutine
import os
import json
import tornado.httpclient

define('debug', default=True, type=bool)
define('port', default=8888, type=int)
define('host', default='127.0.0.1', type=str)

class IndexHandler(tornado.web.RequestHandler):

    def get(self):
        self.render('index.html')

    def post(self):
        print self.request.arguments
        self.write('hi')

class MyFileHandler(tornado.web.RequestHandler):

    def get(self):
        self.render('myfile.html')

class ManageHandler(tornado.web.RequestHandler):

    def write(self, chunk):
        if isinstance(chunk, dict):
            value = json.dumps(chunk)
        else:
            value = chunk
        self.set_header('Content-Type', 'application/json; charset:utf-8')
        self.set_status(200)
        super(ManageHandler, self).write(value)

    def success(self, data):
        response = {
                'meta': {
                    'code': 0,
                    'msg': 'success!'
                },
                'data': data
            }
        self.write(response)

    def fail(self, code, msg):
        response = {
                'meta': {
                    'code': code,
                    'msg': msg
                },
                'data': None
            }
        self.write(response)

class ListRemoteFileHandler(ManageHandler):

    @coroutine
    def post(self):
        at = self.get_argument('at')
        path = self.get_argument('path')

        http_client = tornado.httpclient.AsyncHTTPClient()
        host = 'rsf.qbox.me'

        headers = {
                'Host': host,
                # 'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': 'QBox {}'.format(at)
            }
        url = 'http://{host}{path}'.format(host=host,
                path=path)

        try:
            response = yield http_client.fetch(url,
                                            method='GET',
                                            headers=headers)
        except tornado.httpclient.HTTPError as e:
            self.fail(e.code, str(e))
        else:
            self.success(json.loads(response.body))

class DeleteRemoteFileHandler(ManageHandler):

    @coroutine
    def post(self):
        at = self.get_argument('at')
        path = self.get_argument('path')

        http_client = tornado.httpclient.AsyncHTTPClient()
        host = 'rs.qbox.me'

        headers = {
                'Host': host,
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': 'QBox {}'.format(at)
            }
        url = 'http://{host}{path}'.format(host=host,
                path=path)

        try:
            response = yield http_client.fetch(url,
                                            method='POST',
                                            headers=headers,
                                            body='')
        except tornado.httpclient.HTTPError as e:
            print e.response.body
            self.fail(e.code, str(e))
        else:
            self.success('')

class Application(tornado.web.Application):

    def __init__(self):
        settings = ObjectDict()
        settings.debug = options.debug
        settings.autoescape = None
        self.base_dir = os.path.abspath(os.path.dirname(__file__))
        settings.template_path = os.path.join(self.base_dir, 'templates')
        settings.static_path = os.path.join(self.base_dir, 'static')

        handlers = [
                (r'/', IndexHandler),
                (r'/upload', IndexHandler),
                (r'/myfile', MyFileHandler),
                (r'/myfile/list', ListRemoteFileHandler),
                (r'/myfile/delete', DeleteRemoteFileHandler),
            ]

        super(Application, self).__init__(handlers, **settings)

if __name__ == '__main__':
    parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    print 'Server is running on http://{host}:{port}'.format(
                host=options.host,
                port=options.port
            )
    tornado.ioloop.IOLoop.instance().start()
