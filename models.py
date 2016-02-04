#coding:utf-8

import os
import uuid
import json
import tornado.web
import logging
import time
from tornado import websocket
import hashlib
logging.basicConfig(level=logging.DEBUG)


class RoomHandler(object):
    """Store data about connections, rooms, which users are in which rooms, etc."""

    def __init__(self):
        self.room = dict()
        self.client_name = dict()
        self.sockets = dict()

    def create_room(self, room_id):
        # 创建房间
        if room_id in self.room:
            return
        self.room[room_id] = {}

    def enter_room(self, ws_conn, client_name):
        # 进入房间
        self.client_name[ws_conn.client_id] = client_name
        self.sockets[ws_conn.client_id] = ws_conn
        if ws_conn.room_id not in self.room:
            self.create_room(ws_conn.room_id)
        if ws_conn.client_id in self.room[ws_conn.room_id]:
            raise
        self.room[ws_conn.room_id][ws_conn.client_id] = ws_conn

    def get_all_ws_conn(self, client_id, room_id):
        # 获取房间的所有连接
        try:
            for key, value in self.room[room_id].items():
                if key == client_id:
                    continue
                yield value
        except KeyError:
            logging.error("get_all_ws_conn index error")
            pass

    def leave_room(self, socket):
        # 离开房间
        room_id = socket.room_id
        client_id = socket.client_id
        try:
            del self.room[room_id][client_id]
        except KeyError:
            pass
        try:
            del self.sockets[client_id]
        except KeyError:
            pass
        try:
            del self.client_name[client_id]
        except KeyError:
            pass
        # 如果房间数量连接人数为0,删除房间
        try:
            root_member = len(self.room[room_id])
            logging.debug("root_id:{} member num is {}".format(room_id, root_member))
            if root_member == 0:
                del self.room[room_id]
        except KeyError:
            pass


class WSEvent(object):

    def __init__(self, room_handler):
        self._room = room_handler
        self.__default = 'default_room'

    def emit(self, event_name, msg, socket):
        func = getattr(self, event_name, None)
        if func is None:
            logging.debug("WSEvent don't implement {} method".format(event_name))
        else:
            logging.debug("WSEvent will run {} method".format(event_name))
            try:
                func(self, msg, socket)
            except TypeError:
                func(msg, socket)

    def __join__(self, msg, socket):
        logging.debug("socketID:{} join".format(socket.client_id))
        room_id = msg.get("room", None) or self.__default
        socket.room_id = room_id
        self._room.enter_room(socket, '')
        ws_conns = self._room.get_all_ws_conn(socket.client_id, room_id=room_id)
        ids = []
        for conn in ws_conns:
            conn.write_message(json.dumps({
                "eventName": "_new_peer",
                "data": {
                    "socketId": socket.client_id, },
            }))
            ids.append(conn.client_id)

        socket.write_message(json.dumps({
            "eventName": "_peers",
            "data": {
                "connections": ids,
                "you": socket.client_id,
            }
        }))

        self.emit('new_peer', msg, socket)

    def __ice_candidate__(self, msg, socket):

        soc = self._room.sockets.get(msg['socketId'], None)
        if soc is None:
            logging.error("socket_id:{} not found".format(msg['socketId']))
            return
        soc.write_message(json.dumps({
            "eventName": "_ice_candidate",
            "data": {
                "label": msg['label'],
                "candidate": msg['candidate'],
                "socketId": socket.client_id,
            }
        }))

        self.emit('ice_candidate', msg, socket)

    def __offer__(self, msg, socket):
        soc = self._room.sockets.get(msg['socketId'], None)
        if soc is None:
            logging.error("socket_id:{} not found".format(msg['socketId']))
            return
        soc.write_message(json.dumps({
            "eventName": "_offer",
            "data": {
                "sdp": msg['sdp'],
                "socketId": socket.client_id, },
        }))
        self.emit('offer', msg, socket)

    def __answer__(self, msg, socket):

        soc = self._room.sockets.get(msg['socketId'], None)
        if soc is None:
            logging.error("socket_id:{} not found".format(msg['socketId']))
            return
        soc.write_message(json.dumps({
            "eventName": "_answer",
            "data": {
                "sdp": msg['sdp'],
                "socketId": socket.client_id, },
        }))
        self.emit('answer', msg, socket)

    def __remove_peer__(self, msg, socket):
        ws_conns = self._room.get_all_ws_conn(socket.client_id, room_id=socket.room_id)
        for conn in ws_conns:
            conn.write_message(json.dumps({
                "eventName": "_remove_peer",
                "data": {
                    "socketId": socket.client_id, },
            }))
        self._room.leave_room(socket)
        self.emit('remove_peer', msg, socket)

    def socket_message(self, msg, socket):
        ws_conns = self._room.get_all_ws_conn(socket.client_id, room_id=socket.room_id)
        for conn in ws_conns:
            conn.write_message(json.dumps(msg))

    def new_connect(self, msg, socket):
        pass

    def new_peer(self, msg, socket):
        pass

    def remove_peer(self, msg, socket):
        pass

    def ice_candidate(self, msg, socket):
        pass

    def offer(self, msg, socket):
        pass

    def answer(self, msg, socket):
        pass

    def remove_peer(self, msg, socket):
        pass


class ClientWSConnection(websocket.WebSocketHandler):

    def initialize(self, event_class):
        """Store a reference to the "external" RoomHandler instance"""
        self.event_class = event_class

    def open(self, client_id):
        # self.client_id = uuid.uuid1().hex
        self.client_id = client_id
        self.room_id = None
        self.event_class.emit('new_connect', None, self)
        logging.debug("WebSocket opened. ClientID = %s, ROOMID = %s" % (self.client_id, self.room_id))

    def on_message(self, message):
        msg = json.loads(message)
        logging.debug("room_id: {} client_id:{} send message:{}".format(self.room_id, self.client_id, msg))
        event_name = msg.get("eventName", None)
        if event_name is not None:
            logging.debug("eventName:{}".format(event_name))
            self.event_class.emit(event_name, msg['data'], self)
        else:
            self.event_class.emit("socket_message", msg['data'], self)

    def on_close(self):
        logging.debug("client_id:{} leave room_id={}".format(self.client_id, self.room_id))
        self.event_class.emit("__remove_peer__", None, self)


