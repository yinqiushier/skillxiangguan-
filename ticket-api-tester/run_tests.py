import csv
import json
import requests
import time
import os
import sys
import argparse
from datetime import datetime

# Daily environment is reachable directly from WSL. Local proxy variables can
# break TLS handshakes for support-daily.udeer.ai, so keep requests direct.
for proxy_key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
    os.environ.pop(proxy_key, None)

VIEW_TYPE_MAP = {
    0: "无", 1: "硬件问题", 2: "硬件问题", 3: "软件问题",
    4: "网络问题", 5: "配置问题", 6: "使用问题", 7: "性能问题",
    8: "安全问题", 9: "其他问题", 10: "数据问题", 11: "功能问题",
    12: "界面问题", 13: "兼容性问题", 14: "稳定性问题", 15: "可用性问题",
    16: "可用性问题(故障,无法运行)", 17: "业务问题", 18: "流程问题",
    19: "权限问题", 20: "接口问题", 21: "可用性问题(故障,无法运行)",
}

OUTPUT_DIR = "/mnt/c/Users/lenovo/Desktop/create接口/web"
INPUT_FILE = os.path.join(OUTPUT_DIR, "ticket_create_api_testcases.csv")

def parse_csv_value(val):
    if val == '': return None
    if val.lower() == 'true': return True
    if val.lower() == 'false': return False
    if val.startswith('[') and val.endswith(']'):
        try: return json.loads(val.replace('""', '"'))
        except: pass
    return val

def convert_problem_time(time_str):
    if not time_str: return None
    try:
        if 'T' in time_str: return time_str
        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    except: return time_str

def build_old_payload(row):
    payload = {}
    for k, v in [('title','title'),('description','description'),('type','type')]:
        val = row.get(v,'').strip()
        if val: payload[k] = val
    val = row.get('ticketNumber','').strip()
    if val: payload['ticketNumber'] = val
    else: payload['ticketNumber'] = f"TEST-{int(time.time()*1000)}"
    val = row.get('assignedTo','').strip()
    if val: payload['assignedTo'] = str(val)
    val = row.get('priorityId','').strip()
    if val:
        try: payload['priorityId'] = int(val)
        except: pass
    for k, v in [('customerName','customerName'),('customerPhone','customerPhone'),('carId','carId'),('problemDuration','problemDuration')]:
        val = row.get(v,'').strip()
        if val: payload[k] = val
    val = row.get('problemTime','').strip()
    if val: payload['problemTime'] = convert_problem_time(val)
    val = row.get('viewType','').strip()
    if val:
        try: payload['viewType'] = VIEW_TYPE_MAP.get(int(val), str(val))
        except: payload['viewType'] = val
    payload['statusId'] = 1
    payload['rootCause'] = "业务配置"
    return payload

def build_new_payload(row):
    payload = {}
    fields = [
        ('title','title'),('description','description'),('type','type'),
        ('carId','carId'),('problemTime','problemTime'),('problemDuration','problemDuration'),
        ('ticketNumber','ticketNumber'),('viewType','viewType'),('customerName','customerName'),
        ('customerPhone','customerPhone'),('isCustomerComplaint','isCustomerComplaint'),
        ('assignedTo','assignedTo'),('assignedRole','assignedRole'),('partner','partner'),
        ('rdAssignedList','rdAssignedList'),('source','source'),('priorityId','priorityId'),
    ]
    for csv_field, payload_field in fields:
        val = row.get(csv_field, '').strip()
        if val == '': continue
        parsed = parse_csv_value(val)
        if payload_field in ['viewType', 'priorityId', 'assignedTo']:
            try: parsed = int(parsed)
            except: pass
        payload[payload_field] = parsed
    return payload

def run_api_test(api_name, url, token, build_fn, output_file):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = ['title','期望结果','HTTP状态码','响应体code','响应message','返回工单id','测试结果']
        rows = list(reader)
    
    results = []
    total = len(rows)
    print(f"\n{'='*60}\n{api_name}\nURL: {url}\n{'='*60}")
    
    for i, row in enumerate(rows, 1):
        print(f"  [{i}/{total}] {str(row.get('title',''))[:20]:<20} - {str(row.get('期望结果',''))[:30]}")
        payload = build_fn(row)
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            try: data = resp.json()
            except: data = {'statusCode': resp.status_code, 'message': resp.text[:200]}
            
            sc = data.get('statusCode', resp.status_code)
            msg = data.get('message', '')
            tid = data.get('data', {}).get('id', '') if isinstance(data.get('data'), dict) else ''
            expected = row.get('期望结果', '')
            success = sc == 200 and ('成功' in msg or 'success' in msg.lower())
            
            if '应失败' in expected or '失败' in expected:
                result = 'PASS' if not success else 'FAIL'
            else:
                result = 'PASS' if success else 'FAIL'
            
            results.append({'title':row.get('title',''),'期望结果':expected,'HTTP状态码':resp.status_code,'响应体code':sc,'响应message':msg,'返回工单id':tid,'测试结果':result})
        except Exception as e:
            results.append({'title':row.get('title',''),'期望结果':row.get('期望结果',''),'HTTP状态码':'ERROR','响应体code':'ERROR','响应message':str(e),'返回工单id':'','测试结果':'ERROR'})
        time.sleep(0.3)
    
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    pc = sum(1 for r in results if r['测试结果'] == 'PASS')
    fc = sum(1 for r in results if r['测试结果'] == 'FAIL')
    ec = sum(1 for r in results if r['测试结果'] == 'ERROR')
    print(f"\n  总计 {total} | 通过 {pc} | 失败 {fc} | 错误 {ec}")
    print(f"  结果: {output_file}")
    if fc > 0:
        print("  失败:")
        for r in results:
            if r['测试结果'] == 'FAIL':
                print(f"    {r['title']}: 期望={r['期望结果']}, HTTP={r['HTTP状态码']} 响应体={r['响应体code']} {r['响应message']}")

def load_template_row(template_title=None, template_index=1):
    with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"模板文件为空: {INPUT_FILE}")
    if template_title:
        for row in rows:
            if row.get('title', '').strip() == template_title:
                return row
        raise ValueError(f"未找到模板标题: {template_title}")
    if template_index < 1 or template_index > len(rows):
        raise ValueError(f"模板行号超出范围: {template_index}, 总行数: {len(rows)}")
    return rows[template_index - 1]

def create_from_template(base_url, token, title, description, template_title=None, template_index=1, output_file=None):
    row = load_template_row(template_title=template_title, template_index=template_index)
    row = dict(row)
    row['title'] = title
    row['description'] = description
    payload = build_new_payload(row)
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    url = f"{base_url}/api/v2/tickets/create"

    print(f"\n{'='*60}\n按模板创建工单\nURL: {url}\n模板: {template_title or f'第{template_index}行'}\n{'='*60}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    try:
        data = resp.json()
    except Exception:
        data = {'statusCode': resp.status_code, 'message': resp.text[:500]}

    print(f"\nHTTP状态码: {resp.status_code}")
    print(json.dumps(data, ensure_ascii=False, indent=2)[:5000])

    ticket_id = data.get('data', {}).get('id', '') if isinstance(data.get('data'), dict) else ''
    result = {
        'title': title,
        'HTTP状态码': resp.status_code,
        '响应体code': data.get('statusCode', resp.status_code),
        '响应message': data.get('message', ''),
        '返回工单id': ticket_id,
    }

    if output_file:
        fieldnames = ['title', 'HTTP状态码', '响应体code', '响应message', '返回工单id']
        exists = os.path.exists(output_file)
        with open(output_file, 'a', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not exists:
                writer.writeheader()
            writer.writerow(result)
        print(f"\n创建结果已追加: {output_file}")

    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='工单创建接口测试')
    parser.add_argument('--new-token', required=True, help='新接口 /api/v2/tickets/create 的token')
    parser.add_argument('--old-token', help='老接口 /api/workItem/create 的token')
    parser.add_argument('--base-url', default='https://support-test.udeer.ai', help='接口基础URL')
    parser.add_argument('--only-new', action='store_true', help='仅测试新接口')
    parser.add_argument('--only-old', action='store_true', help='仅测试老接口')
    parser.add_argument('--create-from-template', action='store_true', help='按CSV模板创建单个新接口工单，只覆盖title和description')
    parser.add_argument('--title', help='按模板创建时覆盖的工单标题')
    parser.add_argument('--description', help='按模板创建时覆盖的工单描述')
    parser.add_argument('--template-title', help='按CSV中title匹配模板行；不传则使用--template-index')
    parser.add_argument('--template-index', type=int, default=1, help='按CSV行号选择模板，默认第1行')
    parser.add_argument('--template-output', default=os.path.join(OUTPUT_DIR, 'template_create_results.csv'), help='按模板创建结果输出CSV')
    args = parser.parse_args()

    if args.create_from_template:
        if not args.title or not args.description:
            parser.error('--create-from-template 需要同时传 --title 和 --description')
        create_from_template(
            args.base_url,
            args.new_token,
            args.title,
            args.description,
            template_title=args.template_title,
            template_index=args.template_index,
            output_file=args.template_output,
        )
        print(f"\n所有测试完成！")
        sys.exit(0)
    
    if not args.only_old:
        run_api_test(
            "新接口 /api/v2/tickets/create",
            f"{args.base_url}/api/v2/tickets/create",
            args.new_token,
            build_new_payload,
            os.path.join(OUTPUT_DIR, "new_api_test_results.csv")
        )
    
    if not args.only_new:
        if not args.old_token:
            print("\n[提示] 未提供 --old-token，跳过老接口测试")
        else:
            run_api_test(
                "老接口 /api/workItem/create",
                f"{args.base_url}/api/workItem/create",
                args.old_token,
                build_old_payload,
                os.path.join(OUTPUT_DIR, "old_api_test_results.csv")
            )
    
    print(f"\n所有测试完成！")
