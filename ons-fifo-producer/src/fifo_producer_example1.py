#!/usr/bin/env python3
"""
RocketMQ FIFO Producer - 调度版
"""

import json
import time
import uuid
from datetime import datetime, timezone
from rocketmq.client import Producer, Message, SendStatus # type: ignore

SN = "0241205120011"    
NAME = "U1117A"

default_tag='default'
SATUCK_tag='Stuck'
reboot_tag='reboot'
coredump_tag='coredump'
stop_tag='stop'
accident_tag='accident'
AebTooMuch_tag = 'AebTooMuch'
entangle_tag='Entangle'

AebTooMuch={
  "sn": SN,
  "name": NAME,
  "driver": None,
  "type": "1",
  "time":datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
  "msg": "AEB触发过多 一天生成一个工单 还是一小时生成一条工单",
  "callLevel": 0,
  "reason": "emergency_brake"
}

车辆缠绕待定={
  "sn": SN,
  "name": NAME,
  "type": "Entangle",
  "time": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
  "msg": "车辆发生缠绕:右刷盘缠绕",
  "callLevel": 2
}

SATUCK_mute = {
    "sn": SN,
    "name": NAME,
    "type": "Stuck",
    "time": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    "mute": True,
    "msg": "车辆作业期间异常卡停过久-测试数据 mute=True 生成低level工单-五分钟内不重复生成",
    "callLevel": 0,
    "idleAndRoamDrivers": [
        {"driverId": "driver_743", "driverName": "安广宇test", "deviceName": "", "deviceSN": "", "deviceDomain": "", "mode": "", "otherWork": ""},
        {"driverId": "driver_1000027", "driverName": "金事博", "deviceName": "U1443A", "deviceSN": "0250314120001", "deviceDomain": "prod", "mode": "roam", "otherWork": ""},
        {"driverId": "driver_678", "driverName": "淳进亮", "deviceName": "U1351A", "deviceSN": "0250312120029", "deviceDomain": "prod", "mode": "roam", "otherWork": ""},
    ]
}

SATUCK_has_driver = {
    "sn": SN,
    "name": NAME,
    "type": "Stuck",
    "time": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    "mute": False,
    "msg": "车辆作业期间异常卡停过久-有driver不生成",
    "callLevel": 0,
    "driver": "driver_743",
    "idleAndRoamDrivers": [
        {"driverId": "driver_743", "driverName": "程凯韬", "deviceName": "", "deviceSN": "", "deviceDomain": "", "mode": "", "otherWork": ""},
        {"driverId": "driver_1000027", "driverName": "金事博", "deviceName": "U1443A", "deviceSN": "0250314120001", "deviceDomain": "prod", "mode": "roam", "otherWork": ""},
        {"driverId": "driver_678", "driverName": "淳进亮", "deviceName": "U1351A", "deviceSN": "0250312120029", "deviceDomain": "prod", "mode": "roam", "otherWork": ""},
    ]
}

SATUCK_nodriver_nomute = {
    "sn": SN,
    "name": NAME,
    "type": "Stuck",
    "time": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    "mute": False,
    "msg": "车辆作业期间异常卡停过久-测试数据 mute=False 生成紧急level工单-五分钟内不重复生成 ，先低后高要测试下 或者先高后低",
    "callLevel": 0,
    "idleAndRoamDrivers": [
        {"driverId": "driver_743", "driverName": "程凯韬", "deviceName": "", "deviceSN": "", "deviceDomain": "", "mode": "", "otherWork": ""},
        {"driverId": "driver_1000027", "driverName": "金事博", "deviceName": "U1443A", "deviceSN": "0250314120001", "deviceDomain": "prod", "mode": "roam", "otherWork": ""},
        {"driverId": "driver_678", "driverName": "淳进亮", "deviceName": "U1351A", "deviceSN": "0250312120029", "deviceDomain": "prod", "mode": "roam", "otherWork": ""},
    ]
}

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

module_reboot_主激光异常={
    "sn": SN,
    "type": "module",
    "reason": "主激光异常",
    "module": "LOCATION",
    "alarms": [
        "[5120]name(udeer::perception::PclPoseCU) Data 1775203266670540 Pose 1775203266439999 has large diff timestamp 230541",
        "[5120]name(udeer::perception::PclPoseCU) Data 1775203266722845 Pose 1775203266439999 has large diff timestamp 282846",
        "[5004]PERCEPTION_GLOBAL_ODOM_TIMEOUT",
        "[5100]name(udeer::perception::PclPoseCU) Data 1775203266700062 Pose 1775203266439999 has large diff timestamp 260063",
        "[5120]name(udeer::perception::PclPoseCU) Data 1775203266771779 Pose 1775203266439999 has large diff timestamp 331780",
        "[5102]name(udeer::perception::PclPoseCU) Data 1775203266700062 Pose 1775203266439999 has large diff timestamp 260063",
        "[5120]name(udeer::perception::PclPoseCU) Data 1775203266821820 Pose 1775203266439999 has large diff timestamp 381821"
    ],
    "time": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    "userId": 662,
    "msg":"30天内同车同模块重启计数预警",
    "userName":"王先跃"
}

module_reboot_配置变更重启={
    "sn": SN,
    "type": "module",
    "reason": "配置变更重启",
    "module": "PLANNING",
    "alarms": [],
    "time": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    "msg": "配置变更重启",
    "userId": 662,
    "userName": "王先跃"
}

module_reboot_other={
    "sn": SN,
    "type": "module",
    "reason": "其他原因",
    "module": "CONTROL",
    "alarms": [],
    "time": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    "userId": 662,
    "userName": "王先跃"
}

power_reboot={
    "sn": SN,
    "type": "power-reboot",
    "reason": "RTC故障",
    "module": None,
    "alarms": [],
    "time": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    "userId": 662,
    "userName": "王先跃"
}

accident={
  "sn": SN,
  "deviceName": NAME,
  "reason": "碰撞障碍物——anntest",
  "time": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
  "userId": 662,
  "userName": "王先跃"
}

safe_name={
  "code": SN,
  "caller": "safety_system",
  "canceller": "system",
  "sn": "DEVICE001",
  "devId": "DEV001",
  "name": "巡逻任务001",
  "devName": NAME,
  "projectNo": "PRJ001",
  "id": 10002,
  "no": "TASK002",
  "process": 80,
  "status": "stopped",
  "startTime": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
  "stopTime": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
  "taskFile": "/tasks/task002.xml",
  "errorMsg": "安全响应超时",
  "miles": 30.0,
  "returnRemainDis": 5.0,
  "subProcess": 0,
  "pauseStartTime": 0
}

corpdump={
  "sn": SN,
  "name": NAME,
  "projectName": "测试项目",
  "time": int(time.time() * 1000),
  "recentCoreDumps": [
    {
      "module": "navigation",
      "createTime": int(time.time() * 1000),
      "message": "Segmentation fault"
    },
    {
      "module": "sensor",
      "createTime": int(time.time() * 1000),
      "message": "Null pointer exception"
    }
  ]
}

def get_Date():
    print(datetime.now(timezone.utc).isoformat())

def send_message(producer, topic, tags, body):
    msg = Message(topic)
    msg.set_tags(tags)
    msg.set_keys('ann_test_keys')
    print(f"设置的keys: ann_test_keys")
    msg.set_body(json.dumps(body, ensure_ascii=False))
    result = producer.send_sync(msg)
    if result.status == SendStatus.OK:
        print(f"发送成功, MessageID: {result.msg_id}, keys: ann_test_keys")
    else:
        print(f"发送失败, Status: {result.status}")
    time.sleep(1)

def main():
    ENDPOINT = "ep-bp1iecc62ca636d4bb66.epsrv-bp1g2k84c7kid2igyiun.cn-hangzhou.privatelink.aliyuncs.com:8080"
    ACCESS_KEY = "cR81a766NDsDnkTb"
    ACCESS_SECRET = "9OlVp9PF7ARmIFDH"
    TOPIC = "test_fms_support_ticket"
    GROUP = "ann_test"
    producer = Producer(GROUP)
    producer.set_namesrv_addr(ENDPOINT)
    producer.set_session_credentials(ACCESS_KEY, ACCESS_SECRET, "")
    producer.start()
    print("生产者启动成功\n")
    
    send_message(producer, TOPIC, entangle_tag, 车辆缠绕待定)

    producer.shutdown()
    print("\n生产者已关闭")

if __name__ == "__main__":
    main()
