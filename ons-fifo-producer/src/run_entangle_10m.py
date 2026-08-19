#!/usr/bin/env python3
import json
import time
from datetime import datetime, timezone
from rocketmq.client import Producer, Message, SendStatus

SN = "0241205120011"    
NAME = "U1117A"
ENTANGLE_TAG = "Entangle"

ENDPOINT = "ep-bp1iecc62ca636d4bb66.epsrv-bp1g2k84c7kid2igyiun.cn-hangzhou.privatelink.aliyuncs.com:8080"
ACCESS_KEY = "cR81a766NDsDnkTb"
ACCESS_SECRET = "9OlVp9PF7ARmIFDH"
TOPIC = "test_fms_support_ticket"
GROUP = "ann_test"

车辆缠绕待定 = {
    "type": "Entangle",
    "sn": SN,
    "name": NAME,
    "time": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    "msg": "车辆发生缠绕:右刷盘缠绕"
}

def send_message(producer, topic, tags, body):
    msg = Message(topic)
    msg.set_tags(tags)
    msg.set_keys('ann_test_keys')
    msg.set_body(json.dumps(body, ensure_ascii=False))
    result = producer.send_sync(msg)
    if result.status == SendStatus.OK:
        print(f"[{datetime.now()}] 发送成功, MessageID: {result.msg_id}")
    else:
        print(f"[{datetime.now()}] 发送失败, Status: {result.status}")

def main():
    producer = Producer(GROUP)
    producer.set_namesrv_addr(ENDPOINT)
    producer.set_session_credentials(ACCESS_KEY, ACCESS_SECRET, "")
    producer.start()
    print("生产者启动成功")
    
    while True:
        send_message(producer, TOPIC, ENTANGLE_TAG, 车辆缠绕待定)
        time.sleep(600)

if __name__ == "__main__":
    main()