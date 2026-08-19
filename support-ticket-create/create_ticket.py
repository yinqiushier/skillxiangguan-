#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
import uuid


DEFAULT_BASE_URL = "https://support-daily.udeer.ai"
DEFAULT_PAYLOAD = {
    "title": "自动化测试",
    "description": "<p>自动化测试</p>",
    "type": "异常排查",
    "carId": "E1024A",
    "problemDuration": "less_than_3_minutes",
    "viewType": "1",
    "assignedTo": "0",
    "priorityId": 1,
    "moduleTags": [],
    "isCustomerComplaint": False,
    "customerName": "test",
    "statusId": 11,
    "assignedRole": "PAE",
}


def normalize_token(token):
    if not token:
        return None
    token = token.strip()
    if token.lower().startswith("bearer "):
        return token
    return f"Bearer {token}"


def now_text():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def build_payload(args):
    payload = dict(DEFAULT_PAYLOAD)
    payload.update(
        {
            "ticketNumber": args.ticket_number or str(uuid.uuid1()),
            "problemTime": args.problem_time or now_text(),
        }
    )

    overrides = {
        "title": args.title,
        "description": args.description,
        "type": args.type,
        "carId": args.car_id,
        "problemDuration": args.problem_duration,
        "viewType": args.view_type,
        "assignedTo": args.assigned_to,
        "assignedRole": args.assigned_role,
        "customerName": args.customer_name,
    }
    payload.update({key: value for key, value in overrides.items() if value is not None})

    if args.priority_id is not None:
        payload["priorityId"] = args.priority_id
    if args.status_id is not None:
        payload["statusId"] = args.status_id
    if args.customer_complaint is not None:
        payload["isCustomerComplaint"] = args.customer_complaint

    return payload


def parse_json_response(body):
    if not body:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def is_success(status, data):
    if status < 200 or status >= 300:
        return False
    if not isinstance(data, dict):
        return True
    code = data.get("code")
    message = str(data.get("message") or data.get("msg") or "")
    return code in (0, 200, "0", "200") or "成功" in message or "success" in message.lower()


def request_create(base_url, token, payload, timeout):
    url = base_url.rstrip("/") + "/api/v2/tickets/create"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Content-Type": "application/json",
        "Origin": base_url.rstrip("/"),
        "Referer": base_url.rstrip("/") + "/workspace/issueManagement?current=1&isHideCheck=true&isNotProblem=true&pageSize=10",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    }
    if token:
        headers["authorization"] = token
        headers["Cookie"] = "authorizationV2=" + token.replace(" ", "%20")

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            return resp.status, text, parse_json_response(text)
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        return exc.code, text, parse_json_response(text)


def print_result(status, text, data):
    code = data.get("code") if isinstance(data, dict) else None
    message = None
    ticket_id = None
    if isinstance(data, dict):
        message = data.get("message") or data.get("msg")
        result_data = data.get("data")
        if isinstance(result_data, dict):
            ticket_id = result_data.get("id") or result_data.get("ticketId") or result_data.get("ticketNo")

    print(f"HTTP状态码: {status}")
    if code is not None:
        print(f"响应体code: {code}")
    if message:
        print(f"响应message: {message}")
    if ticket_id:
        print(f"返回工单id: {ticket_id}")

    if is_success(status, data):
        print("测试结果: PASS")
        return 0

    if status in (401, 403):
        print("测试结果: FAIL - token 可能失效，请向用户索要新的 authorization token")
    else:
        print("测试结果: FAIL")
    if text:
        print("响应体摘要:")
        print(text[:2000])
    return 1


def parse_args():
    parser = argparse.ArgumentParser(description="Create one Udeer Support ticket via /api/v2/tickets/create")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--token", default=os.getenv("UDEER_SUPPORT_TOKEN"))
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--dry-run", action="store_true")

    parser.add_argument("--title")
    parser.add_argument("--description")
    parser.add_argument("--type")
    parser.add_argument("--car-id")
    parser.add_argument("--problem-time")
    parser.add_argument("--problem-duration")
    parser.add_argument("--ticket-number")
    parser.add_argument("--view-type")
    parser.add_argument("--assigned-to")
    parser.add_argument("--assigned-role")
    parser.add_argument("--customer-name")
    parser.add_argument("--priority-id", type=int)
    parser.add_argument("--status-id", type=int)
    parser.add_argument("--customer-complaint", action=argparse.BooleanOptionalAction)
    return parser.parse_args()


def main():
    args = parse_args()
    token = normalize_token(args.token)
    payload = build_payload(args)

    if args.dry_run:
        print("POST " + args.base_url.rstrip("/") + "/api/v2/tickets/create")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if not token:
        print("缺少 token：请传 --token 或设置 UDEER_SUPPORT_TOKEN", file=sys.stderr)
        return 2

    status, text, data = request_create(args.base_url, token, payload, args.timeout)
    return print_result(status, text, data)


if __name__ == "__main__":
    raise SystemExit(main())
