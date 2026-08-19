#!/usr/bin/env python3
import csv
import requests
import json
import time
import sys
import os

TOKEN = "qbxxca30pVfUw2t2i1bIi5ay5PrLW7sTWFz3oPPBf774b9igxhWaeY9KUSdB8SwF"
NEW_API = "https://support-daily.udeer.ai/api/v2/internal/tickets/appCreate"
OLD_API = "https://support-daily.udeer.ai/api/workItem/appCreate"
DETAIL_API = "https://support-daily.udeer.ai/api/workItem/detail"

AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjY1OSwidXNlcm5hbWUiOiJ4aWFueXVlQHVkZWVyLmFpIiwiaWF0IjoxNzc3NDQ4MTUxLCJleHAiOjE3Nzc1MzQ1NTF9.E-CGvPVu8Y4VbXyCzM0bsj9FjLmGiKG0dW2mJGabfq8"
CHECK_TOKEN = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ4aWFueXVlQHVkZWVyLmFpIiwiZXhwIjoxNzc4MDM1Njk2LCJ1c2VyIjoiZmNjZWQyMzdlMDdlZGY1ODg5ZjIwZjYwMzgzZTdjM2IiLCJjcmVhdGVkIjoxNzc3MzQ0NDk2MTQ4fQ.pl2xdXLCs6uGVRFG74KnjaFTCEl5qycJwpFtrGrjncsPnv9x3-SsAmr96VdBGD91pumCGEnzr2-PnA2nZUY1bw"

HEADERS_WITH_TOKEN = {"authorization": TOKEN, "Content-Type": "application/json"}
HEADERS_NO_TOKEN = {"Content-Type": "application/json"}
DETAIL_HEADERS = {"Accept": "application/json", "Content-Type": "application/json", "Authorization": AUTH_TOKEN}
DETAIL_COOKIES = {"UDEER_Check_Platform": CHECK_TOKEN, "UDEER_USUPPORT_Platform": AUTH_TOKEN}

BASE_DATA = {
    "source": "app",
    "type": "异常排查",
    "description": "<p>测试描述</p>",
    "problemDuration": "less_than_1_hour",
    "problemTime": "2024-09-15 08:00:00",
    "carId": "E1024A",
    "viewType": "硬件问题",
    "customerName": "张三",
    "customerPhone": "13812345678",
    "phonePrefix": "+86",
    "attachment": [{"ticketNumber": "TEST-sec", "path": "/file/test.jpg"}]
}

WORK_DIR = "C:\\Users\\lenovo\\Desktop\\create接口\\app"

def get_detail(ticket_id):
    try:
        resp = requests.get(f"{DETAIL_API}?id={ticket_id}", headers=DETAIL_HEADERS, cookies=DETAIL_COOKIES, timeout=10)
        return resp.json()
    except:
        return None

def test_security():
    results = []
    print("=" * 60)
    print("安全专项测试 - 新接口")
    print("=" * 60)

    print("\n[1] 测试重放攻击 - 重复ticketNumber")
    data = BASE_DATA.copy()
    data["ticketNumber"] = "TEST-replay-001"
    data["title"] = "重放攻击测试"
    data["attachment"][0]["ticketNumber"] = "TEST-replay-001"
    resp1 = requests.post(NEW_API, headers=HEADERS_WITH_TOKEN, json=data, timeout=10)
    r1_http, r1_body = resp1.status_code, resp1.json().get("statusCode", "")
    time.sleep(0.3)
    resp2 = requests.post(NEW_API, headers=HEADERS_WITH_TOKEN, json=data, timeout=10)
    r2_http, r2_body = resp2.status_code, resp2.json().get("statusCode", "")
    print(f"    第一次: HTTP={r1_http}, Body={r1_body}")
    print(f"    第二次: HTTP={r2_http}, Body={r2_body}")
    new_pass = "✅ 通过" if r2_body == 400 else "❌ 失败"
    print(f"    防护: {new_pass}")
    results.append({"case": "重放攻击-重复ticketNumber", "api": "新", "http": r2_http, "body": r2_body, "pass": new_pass})

    print("\n[2] 测试未授权访问 - 无token")
    data = BASE_DATA.copy()
    data["ticketNumber"] = "TEST-notoken-001"
    data["title"] = "未授权测试"
    resp = requests.post(NEW_API, headers=HEADERS_NO_TOKEN, json=data, timeout=10)
    print(f"    HTTP={resp.status_code}")
    new_pass = "✅ 通过" if resp.status_code in (401, 403) else "❌ 失败"
    print(f"    防护: {new_pass}")
    results.append({"case": "未授权访问-无token", "api": "新", "http": resp.status_code, "body": resp.json().get("statusCode", ""), "pass": new_pass})

    print("\n[3] 测试XSS - 查看详情是否转义")
    xss_payload = "<script>alert('XSS')</script>"
    data = BASE_DATA.copy()
    data["ticketNumber"] = "TEST-xss-001"
    data["title"] = xss_payload
    data["description"] = f"<p>{xss_payload}</p>"
    resp = requests.post(NEW_API, headers=HEADERS_WITH_TOKEN, json=data, timeout=10)
    if resp.status_code == 201:
        ticket_id = resp.json().get("data", "")
        detail = get_detail(ticket_id)
        detail_str = json.dumps(detail, ensure_ascii=False) if detail else ""
        is_escaped = xss_payload not in detail_str or "&lt;script&gt;" in detail_str
        new_pass = "✅ 通过" if is_escaped else "❌ 失败"
        print(f"    创建成功, ID={ticket_id}")
        print(f"    XSS转义: {new_pass}")
        results.append({"case": "XSS-script标签", "api": "新", "http": 201, "body": 200, "pass": new_pass})
    else:
        print(f"    创建失败: {resp.status_code}")
        results.append({"case": "XSS-script标签", "api": "新", "http": resp.status_code, "body": resp.json().get("statusCode", ""), "pass": "❌ 失败"})

    print("\n" + "=" * 60)
    print("安全专项测试 - 老接口")
    print("=" * 60)

    print("\n[1] 测试重放攻击 - 重复ticketNumber")
    data = BASE_DATA.copy()
    data["ticketNumber"] = "TEST-replay-old-001"
    data["title"] = "重放攻击测试"
    data["attachment"][0]["ticketNumber"] = "TEST-replay-old-001"
    data["problemTime"] = "2024-09-15T08:00:00Z"
    resp1 = requests.post(OLD_API, headers=HEADERS_WITH_TOKEN, json=data, timeout=10)
    r1_http, r1_body = resp1.status_code, resp1.json().get("statusCode", "")
    time.sleep(0.3)
    resp2 = requests.post(OLD_API, headers=HEADERS_WITH_TOKEN, json=data, timeout=10)
    r2_http, r2_body = resp2.status_code, resp2.json().get("statusCode", "")
    print(f"    第一次: HTTP={r1_http}, Body={r1_body}")
    print(f"    第二次: HTTP={r2_http}, Body={r2_body}")
    old_pass = "✅ 通过" if r2_body == 400 else "❌ 失败"
    print(f"    防护: {old_pass}")
    results.append({"case": "重放攻击-重复ticketNumber", "api": "旧", "http": r2_http, "body": r2_body, "pass": old_pass})

    print("\n[2] 测试未授权访问 - 无token")
    data = BASE_DATA.copy()
    data["ticketNumber"] = "TEST-notoken-old-001"
    data["title"] = "未授权测试"
    data["problemTime"] = "2024-09-15T08:00:00Z"
    resp = requests.post(OLD_API, headers=HEADERS_NO_TOKEN, json=data, timeout=10)
    print(f"    HTTP={resp.status_code}")
    old_pass = "✅ 通过" if resp.status_code in (401, 403) else "❌ 失败"
    print(f"    防护: {old_pass}")
    results.append({"case": "未授权访问-无token", "api": "旧", "http": resp.status_code, "body": resp.json().get("statusCode", ""), "pass": old_pass})

    print("\n[3] 测试XSS - 查看详情是否转义")
    data = BASE_DATA.copy()
    data["ticketNumber"] = "TEST-xss-old-001"
    data["title"] = xss_payload
    data["description"] = f"<p>{xss_payload}</p>"
    data["problemTime"] = "2024-09-15T08:00:00Z"
    resp = requests.post(OLD_API, headers=HEADERS_WITH_TOKEN, json=data, timeout=10)
    if resp.status_code == 201:
        ticket_id = resp.json().get("data", "")
        detail = get_detail(ticket_id)
        detail_str = json.dumps(detail, ensure_ascii=False) if detail else ""
        is_escaped = xss_payload not in detail_str or "&lt;script&gt;" in detail_str
        old_pass = "✅ 通过" if is_escaped else "❌ 失败"
        print(f"    创建成功, ID={ticket_id}")
        print(f"    XSS转义: {old_pass}")
        results.append({"case": "XSS-script标签", "api": "旧", "http": 201, "body": 200, "pass": old_pass})
    else:
        print(f"    创建失败: {resp.status_code}")
        results.append({"case": "XSS-script标签", "api": "旧", "http": resp.status_code, "body": resp.json().get("statusCode", ""), "pass": "❌ 失败"})

    save_results(results)
    print("\n" + "=" * 60)
    print("测试完成，结果已保存到 test_security_results.csv")
    print("=" * 60)

def save_results(results):
    path = os.path.join(WORK_DIR, "test_security_results.csv")
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["用例名称", "接口", "HTTP状态码", "响应体状态码", "测试结果"])
        for r in results:
            writer.writerow([r["case"], r["api"], r["http"], r["body"], r["pass"]])

if __name__ == "__main__":
    test_security()