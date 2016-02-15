## 一个简单的SkyRTC示例

Python版本，原版本[https://github.com/LingyuCoder/SkyRTC-demo](https://github.com/LingyuCoder/SkyRTC-demo)

## demo

[https://tv.lovedboy.com/abc](https://tv.lovedboy.com/abc) URL中abc为房间号，可以将abc替换为协商好的房间号。



## 协议


### 背景知识

[http://xiaol.me/2014/08/24/webrtc-stun-turn-signaling/](http://xiaol.me/2014/08/24/webrtc-stun-turn-signaling/)

### 建立连接

通过WebSocket与服务器建立连接和交换信令数据。

#### 加入房间

通过WebSocket发送消息。消息格式：

```
  {
    "eventName": "__join__",
    "data": {
        "room": room
    },
}
```

#### 发送ice candidate 信令数据

通过WebSocket发送消息。消息格式：

```
{
    "eventName": "__ice_candidate__",
    "data": {
        "label": candidate.sdpMLineIndex,
        "candidate": candidate.candidate,
        "socketId": socket_id, //接收对象的连接实例
    }
}
```
#### 发送 offer 信令

```
{
    "eventName": "__offer__",
    "data": {
        "sdp": sdp,
        "socketId": socket_id, //接收对象的连接实例,
    },
}
```

#### 发送 anwser 信令

```
{
    "eventName": "__answer__",
    "data": {
            "socketId": socket_id, //接收对象的连接实例
            "sdp": session_desc
    }
}
```


### 客户端事件处理

#### peers

用户加入房间后触发。（发送给用户本人）

```
{
    "eventName": "_peers",
    "data": {
        "connections": ids, //房间内其他的连接实例 
        "you": socket_id //本人的连接实例
    }
}
```


#### new_peer

用户加入房间后触发。（发送给其他人）

消息格式：

```
{
    "eventName": "_new_peer",
    "data": {
        "socketId": socket_id, //新加入的客户端连接实例
    },
}
```

#### remove_peer

用户关闭连接后触发。

消息格式：

```
{
    "eventName": "_remove_peer",
    "data": {
        "socketId": socket_id //新加入的客户端连接实例
    },
}
```

#### ice_candidate

接收到ice candidate信令时触发。

消息格式：

```
{
    "eventName": "_ice_candidate",
    "data": {
        "label": candidate.sdpMLineIndex,
        "candidate": candidate.candidate,
        "socketId": socket_id //本人的连接对象实例,
    }
}
 
```

#### offer

收到offer信令时触发。

消息格式：

```
{
    "eventName": "_offer",
    "data": {
        "sdp": session_desc,
        "socketId": socket_id //本人的连接对象实例
    },
}
```

#### answer

收到answer信令时触发。

```
{
    "eventName": "_answer",
    "data": {
        "sdp": session_desc,
        "socketId": socket_id, //本人的连接对象实例
    },
}
```
