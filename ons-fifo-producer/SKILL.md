---
name: ons-fifo-producer
description: ONS RocketMQ FIFO消息生产者 - 发送工单消息到阿里云ONS
license: MIT
compatibility: opencode
metadata:
  version: "1.0"
  author: ann
  platform: Alibaba Cloud ONS
---

# ONS FIFO消息生产者

## 概述

向阿里云ONS RocketMQ发送FIFO队列消息，用于工单系统测试。支持多种消息类型：车辆缠绕(Entangle)、模块重启(module reboot)、车辆卡停(Stuck)、AEB触发过多等。

## 使用方法

1. 修改脚本中的消息内容（SN、NAME、msg等）
2. 运行脚本发送消息

## 消息类型

### 车辆缠绕 (Entangle)
```python
车辆缠绕待定={
  "sn": SN,
  "name": NAME,
  "type": "Entangle",
  "time": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
  "msg": "车辆发生缠绕:右刷盘缠绕",
  "callLevel": 2
}
```

### 模块重启 (module reboot)
```python
module_reboot_RTC={
    "sn": SN,
    "type": "module",
    "reason": "RTC故障",
    "module": "URTC",
    "alarms": ["[11015]URTC_BACK_ERROR"],
    "time": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    "userId": 545,
    "userName": "禹华楠"
}
```

### 车辆卡停 (Stuck)
```python
SATUCK_nodriver_nomute = {
    "sn": SN,
    "name": NAME,
    "type": "Stuck",
    "time": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    "mute": False,
    "msg": "车辆作业期间异常卡停过久",
    "callLevel": 0,
    "idleAndRoamDrivers": [
        {"driverId": "driver_743", "driverName": "程凯韬", "deviceName": "", "deviceSN": "", "deviceDomain": "", "mode": "", "otherWork": ""},
    ]
}
```

## 配置

- ENDPOINT: ONS服务地址
- ACCESS_KEY: 阿里云AccessKey
- ACCESS_SECRET: 阿里云AccessSecret
- TOPIC: 消息主题
- GROUP: 消费者组

## 文件位置

- 桌面：`C:\Users\lenovo\Desktop\ons-fifo-producer\fifo_producer_example1.py`
- 桌面定时脚本：`C:\Users\lenovo\Desktop\ons-fifo-producer\run_entangle_10m.py`
- opencode：`/home/yinqiushier/.opencode/skills/ons-fifo-producer/src/fifo_producer_example1.py`
- opencode定时脚本：`/home/yinqiushier/.opencode/skills/ons-fifo-producer/src/run_entangle_10m.py`