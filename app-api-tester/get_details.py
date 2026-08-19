#!/usr/bin/env python3
import csv
import requests
import json
import sys
import os

WORK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "..", "..", "Desktop", "create接口", "app")
if not os.path.exists(WORK_DIR):
    WORK_DIR = "."

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
else:
    CONFIG = {"token": "", "detail_url": "https://support-daily.udeer.ai/api/workItem/detail", "detail_cookies": {}}

AUTH_TOKEN = CONFIG.get("token", "")
DETAIL_URL = CONFIG.get("detail_url", "https://support-daily.udeer.ai/api/workItem/detail")
CHECK_TOKEN = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ4aWFueXVlQHVkZWVyLmFpIiwiZXhwIjoxNzc4MDM1Njk2LCJ1c2VyIjoiZmNjZWQyMzdlMDdlZGY1ODg5ZjIwZjYwMzgzZTdjM2IiLCJjcmVhdGVkIjoxNzc3MzQ0NDk2MTQ4fQ.pl2xdXLCs6uGVRFG74KnjaFTCEl5qycJwpFtrGrjncsPnv9x3-SsAmr96VdBGD91pumCGEnzr2-PnA2nZUY1bw"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": AUTH_TOKEN
}

COOKIES = {
    "UDEER_Check_Platform": CHECK_TOKEN,
    "UDEER_USUPPORT_Platform": AUTH_TOKEN
}

IGNORE_KEYS = {'id', 'ticketNumber', 'createdAt', 'updatedAt', 'dueDate', 'dueTimeSta', 'dueStatus', 'sort', 'dupNum', 'firstAcceptTime', 'acceptTime', 'transferTime', 'finishTime', 'examineTime', 'examineNum', 'examineNewTime'}

def extract_ticket_id(full_response, http_status, body_status):
    if http_status not in ("200", "201") or body_status != "200":
        return ""
    try:
        data = json.loads(full_response)
        return str(data.get("data", ""))
    except:
        return ""

def main():
    old_path = os.path.join(WORK_DIR, "test_results_old_api.csv")
    new_path = os.path.join(WORK_DIR, "test_results_new_api.csv")

    old_results = []
    with open(old_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            old_results.append(row)

    new_results = []
    with open(new_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            new_results.append(row)

    old_success_ids = []
    for row in old_results:
        if len(row) > 8:
            tid = extract_ticket_id(row[8], row[3] if len(row) > 3 else "", row[4] if len(row) > 4 else "")
            old_success_ids.append(tid)

    new_success_ids = []
    for row in new_results:
        if len(row) > 8:
            tid = extract_ticket_id(row[8], row[3] if len(row) > 3 else "", row[4] if len(row) > 4 else "")
            new_success_ids.append(tid)

    print(f"旧接口成功: {len([x for x in old_success_ids if x])}")
    print(f"新接口成功: {len([x for x in new_success_ids if x])}")

    old_details = []
    for i, row in enumerate(old_results):
        full_resp = row[8] if len(row) > 8 else ""
        http_status = row[3] if len(row) > 3 else ""
        body_status = row[4] if len(row) > 4 else ""
        ticket_id = extract_ticket_id(full_resp, http_status, body_status)
        if ticket_id:
            try:
                resp = requests.get(f"{DETAIL_URL}?id={ticket_id}", headers=HEADERS, cookies=COOKIES, timeout=10)
                data = resp.json()
                old_details.append(data)
                print(f"  旧 {i+1}: {ticket_id}")
            except Exception as e:
                old_details.append({"error": str(e)})
        else:
            old_details.append({"statusCode": http_status, "message": row[4] if len(row) > 4 else ""})

    new_details = []
    for i, row in enumerate(new_results):
        full_resp = row[8] if len(row) > 8 else ""
        http_status = row[3] if len(row) > 3 else ""
        body_status = row[4] if len(row) > 4 else ""
        ticket_id = extract_ticket_id(full_resp, http_status, body_status)
        if ticket_id:
            try:
                resp = requests.get(f"{DETAIL_URL}?id={ticket_id}", headers=HEADERS, cookies=COOKIES, timeout=10)
                data = resp.json()
                new_details.append(data)
                print(f"  新 {i+1}: {ticket_id}")
            except Exception as e:
                new_details.append({"error": str(e)})
        else:
            new_details.append({"statusCode": http_status, "message": row[4] if len(row) > 4 else ""})

    detail_path = os.path.join(WORK_DIR, "test_details_compare.csv")
    with open(detail_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["序号", "用例名称", "旧工单ID", "旧HTTP", "旧详情", "新工单ID", "新HTTP", "新详情", "差异"])
        for i in range(max(len(old_results), len(new_results))):
            old_row = old_results[i] if i < len(old_results) else []
            new_row = new_results[i] if i < len(new_results) else []
            old_detail = old_details[i] if i < len(old_details) else {}
            new_detail = new_details[i] if i < len(new_details) else {}
            old_id = old_success_ids[i] if i < len(old_success_ids) else ""
            new_id = new_success_ids[i] if i < len(new_success_ids) else ""
            old_http = old_row[3] if len(old_row) > 3 else ""
            new_http = new_row[3] if len(new_row) > 3 else ""
            old_str = json.dumps(old_detail, ensure_ascii=False) if old_detail else ""
            new_str = json.dumps(new_detail, ensure_ascii=False) if new_detail else ""
            diff = ""
            if old_detail and new_detail and "data" in old_detail and "data" in new_detail:
                old_t = old_detail.get("data", {}).get("ticket", {})
                new_t = new_detail.get("data", {}).get("ticket", {})
                if isinstance(old_t, dict) and isinstance(new_t, dict):
                    diffs = []
                    for key in old_t:
                        if key in IGNORE_KEYS:
                            continue
                        old_val = old_t.get(key)
                        new_val = new_t.get(key)
                        if old_val != new_val:
                            diffs.append(f"{key}: 旧{old_val}→新{new_val}")
                    for key in new_t:
                        if key in IGNORE_KEYS or key in old_t:
                            continue
                        diffs.append(f"{key}: 新增")
                    if diffs:
                        diff = "; ".join(diffs[:5])
            writer.writerow([i+1, old_row[1] if len(old_row) > 1 else "", old_id, old_http, old_str, new_id, new_http, new_str, diff])

    print(f"\nDone! 详情保存到 {detail_path}")

if __name__ == "__main__":
    main()
