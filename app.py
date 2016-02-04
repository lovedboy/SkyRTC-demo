#coding:utf-8

import json
import os
import tornado.ioloop
import tornado.httpserver
import tornado.web
import uuid
from models import WSEvent, ClientWSConnection, RoomHandler

rh = RoomHandler()
ws_event = WSEvent(room_handler=rh)


def new_peer(self, msg, socket):
    print "new_peer is coming"

ws_event.new_peer = new_peer


class IndexHandler(tornado.web.RequestHandler):
    def get(self, room):
        client_id = uuid.uuid1().hex
        self.render("index.html", room=room, client_id=client_id)


if __name__ == "__main__":
    app = tornado.web.Application([
        (r"/([\w]+)/?", IndexHandler, ),
        (r"/ws/(.*)", ClientWSConnection, {'event_class': ws_event})],
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
    )
    server = tornado.httpserver.HTTPServer(app, xheaders=True)
    import sys
    try:
        port = int(sys.argv[1])
    except:
        port = 8888
    server.listen(port, '0.0.0.0')
    print 'Simple Chat Server started.'
    tornado.ioloop.IOLoop.instance().start()
