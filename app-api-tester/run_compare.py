#!/usr/bin/env python3
import csv
import requests
import json
import uuid
import time
from datetime import datetime
import sys
import os

# 导入配置
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_manager import load_config

CONFIG = load_config()

OLD_API_URL = CONFIG["old_api_url"]
NEW_API_URL = CONFIG["new_api_url"]
TOKEN = CONFIG["token"]
HEADERS = {"authorization": TOKEN, "Content-Type": "application/json"}
WORK_DIR = CONFIG["work_dir"]

def convert_problem_time(pt):
    if not pt:
        return pt
    try:
        if 'T' in pt:
            dt = datetime.fromisoformat(pt.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        pass
    return pt

def build_attachment(ticket_number, attachment_str):
    if not attachment_str or attachment_str == '[]':
        return None
    try:
        att_list = json.loads(attachment_str.replace("'", '"'))
        if isinstance(att_list, list) and len(att_list) > 0:
            for att in att_list:
                if att.get("ticketNumber") == "":
                    att["ticketNumber"] = ticket_number
            return att_list
    except:
        pass
    return None

def run_test(api_url, row):
    case_name = row[0]
    ticket_number = f"TEST-{uuid.uuid4().hex[:12]}"
    source = row[2]
    ticket_type = row[3]
    title = row[4]
    description = row[5]
    problem_duration = row[6]
    problem_time = row[7]
    car_id = row[8]
    view_type = row[9]
    customer_name = row[10]
    customer_phone = row[11]
    phone_prefix = row[12]
    attachment_str = row[13]

    problem_time_new = convert_problem_time(problem_time)

    data = {
        "ticketNumber": ticket_number,
        "source": source,
        "title": title,
        "type": ticket_type,
        "description": description,
        "problemDuration": problem_duration,
        "problemTime": problem_time_new,
        "viewType": view_type,
        "customerName": customer_name,
        "customerPhone": customer_phone,
        "phonePrefix": phone_prefix
    }

    if car_id:
        data["carId"] = car_id

    att = build_attachment(ticket_number, attachment_str)
    if att:
        data["attachment"] = att

    try:
        resp = requests.post(api_url, headers=HEADERS, json=data, timeout=10)
        resp_data = resp.json()
        http_code = resp.status_code
        body_code = resp_data.get("statusCode", resp.status_code)
        message = resp_data.get("message", "")
        return http_code, body_code, message, json.dumps(resp_data, ensure_ascii=False), ticket_number
    except Exception as e:
        return 0, 0, str(e), str(e), ticket_number

def main():
    csv_path = os.path.join(WORK_DIR, "main.csv")
    results = []

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        for i, row in enumerate(reader):
            if not row or not row[0]:
                continue
            print(f"[{i+1}] Testing: {row[0]}...")

            old_http, old_body, old_msg, old_resp, ticket_number = run_test(OLD_API_URL, row)
            time.sleep(0.2)

            new_http, new_body, new_msg, new_resp, _ = run_test(NEW_API_URL, row)
            time.sleep(0.2)

            results.append({
                "case": row[0],
                "ticket_number": ticket_number,
                "old_http": old_http,
                "old_body": old_body,
                "old_msg": old_msg,
                "new_http": new_http,
                "new_body": new_body,
                "new_msg": new_msg,
                "old_resp": old_resp[:300],
                "new_resp": new_resp[:300]
            })
            print(f"    旧: HTTP={old_http}, Body={old_body} | 新: HTTP={new_http}, Body={new_body}")

    save_results(results)

def save_results(results):
    # compare_all
    path = os.path.join(WORK_DIR, "test_results_compare_all.csv")
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["用例名称", "旧HTTP状态码", "旧响应体状态码", "旧响应消息", "新HTTP状态码", "新响应体状态码", "新响应消息", "旧响应详情", "新响应详情"])
        for r in results:
            writer.writerow([r["case"], r["old_http"], r["old_body"], r["old_msg"], r["new_http"], r["new_body"], r["new_msg"], r["old_resp"], r["new_resp"]])

    # old_api
    path = os.path.join(WORK_DIR, "test_results_old_api.csv")
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["序号", "用例名称", "ticketNumber", "HTTP状态码", "响应体状态码", "响应消息", "期望结果", "测试结果", "完整响应"])
        for i, r in enumerate(results, 1):
            writer.writerow([i, r["case"], r.get("ticket_number", ""), r["old_http"], r["old_body"], r["old_msg"], "", "", r["old_resp"]])

    # new_api
    path = os.path.join(WORK_DIR, "test_results_new_api.csv")
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["序号", "用例名称", "ticketNumber", "HTTP状态码", "响应体状态码", "响应消息", "期望结果", "测试结果", "完整响应"])
        for i, r in enumerate(results, 1):
            writer.writerow([i, r["case"], r.get("ticket_number", ""), r["new_http"], r["new_body"], r["new_msg"], "", "", r["new_resp"]])

    print(f"\nDone! 结果保存到 test_results_*.csv")

if __name__ == "__main__":
    main()
