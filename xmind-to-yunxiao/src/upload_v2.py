#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XMind用例上传到云效平台 V2 - 使用 openapi-rdc API
支持目录结构创建
"""

import json
import sys
import os
import re
import requests
import zipfile
from typing import Dict, Any, Optional, List, Tuple

requests.packages.urllib3.disable_warnings()

PARSE_XMIND_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PARSE_XMIND_PATH)
from xmind_parser import parse_xmind_to_dict

BASE_URL = "https://openapi-rdc.aliyuncs.com/oapi/v1/testhub"
OLD_API_BASE = "https://devops.aliyun.com/testhub/webapi/workspace"


YUNXIAO_DEFAULT_COOKIE = 'cna=zJjsIZoDtDgCAX156W+d85oW; account_info_switch=close; login_current_pk=1854754881094956; currentRegionId=cn-hangzhou; isg=BEJCISq9n9nxuoMxjemFeIvOk0ikE0Yt5xFzVoxbR7Vi3-JZdKvsPcQUi9ujib7F; aliyun_lang=zh; aliyun_enable_passkey=1; AONE_SESSION=fafbc77a-6c72-4ae2-95fc-ad9ed093332e; partitioned_cookie_flag=doubleRemove; ak_user_locale=zh_CN; login_aliyunid="nick251021****"; login_aliyunid_ticket=CmV8s*MT5tJl3_1$$wKZWfDrz9Pd77TU51MbAFOTewieDMgsK1A_X9q1FEJYf_sNpoU_BOTwChTBoNM1ZJeedfK9zxYnbN5hossqIZCr6t7SGxRigm2Cb4fGaCdBZWIzmgdHq6sXXZQg4KFWufyvpe0*0; login_aliyunid_csrf=_csrf_tk_1105775541739092; login_aliyunid_pk=1854754881094956; login_aliyunid_pks="BG+rk6pnG/FVqNJdOCZ1Nm9vLulebBgkZzaa0Gry+KZC/0="; hssid=5728cfed-1d97-45f2-a740-3214d787cc4b; hsite=6; aliyun_country=CN; aliyun_site=CN; tfstk=gfinmLgF52zCGmfwm_rBWjhmyRYtdkZ7nbI8wuFy75P_wpNL9YloExzydb3p4glg6DFKpkWuqxcuypZKegci1fGKpYEeEbcqtzUr27nldccc2MdBRYSu2uRvMnKxdvE74IQTLNhTO8MaadUeeJlVtuRvMhKxdvZ74vIfIfHZQ5wuU97EalPa18Qz4WzP_Ny4_7rraWPwbJe3UJyUzAJgF5Pz4ulrQd2u_7rz4bkZTmBa9blIbIk6_PpEyQnaKyVqL5kKpcyhMSkUsgSztJ4HSvPG4goizA-93W8fB7ZLOYenNnsQYz0rvloe_3rqlfmuuoYJdknILqzr0Q_rikcuuDzGULDKL2rgQmJRl5ng9bo37KI0yloYuku95BU8x-crAXXl4jktHDasqIfaN2ebb8mW3aVuzg717Zy5xgwwecb5Pyy_ISLYxUcBxD416dvGuqaUCJ-vIdb5Pyy_ISpMIZRb8RweD; LOGIN_ALIYUN_PK_FOR_TB=1854754881094956; TEAMBITION_SESSIONID=eyJ1aWQiOiI2ODk5NWM0ODc5Nzg0MzUwZWM4NDMxMDgiLCJhdXRoVXBkYXRlZCI6MTc3NTU0MTcwNzUwNywidXNlciI6eyJfaWQiOiI2ODk5NWM0ODc5Nzg0MzUwZWM4NDMxMDgiLCJuYW1lIjoibmljazI1MTAyMTI2MDUiLCJlbWFpbCI6ImFjY291bnRzXzY4OTk1YzQ4Nzk3ODQzNTBlYzg0MzBmY0BtYWlsLnRlYW1iaXRpb24uY29tIiwiYXZhdGFyVXJsIjoiaHR0cHM6Ly90Y3MtZGV2b3BzLmFsaXl1bmNzLmNvbS90aHVtYm5haWwvMTEzbDI5MWYwNGRhMWM4ZWFjNDc3NmMyOWMyNTY3NjlkZTg0L3cvMTAwL2gvMTAwIiwicmVnaW9uIjoiIiwibGFuZyI6InpoX0NOIiwibGFuZ3VhZ2UiOiJ6aF9DTiIsImlzUm9ib3QiOmZhbHNlLCJvcGVuSWQiOiIiLCJwaG9uZUZvckxvZ2luIjoiIiwiY3JlYXRlZCI6IjIwMjUtMDgtMTFUMDI6NTg6MTYuNDY1WiJ9LCJsb2dpbkZyb20iOiIifQ==; TEAMBITION_SESSIONID.sig=c0sZroyPWQRRcEat5I0B76UNMQY; teambition_lang=zh_CN'

def add_cases_to_testplan(plan_id: str, case_ids: List[str], token: str) -> Tuple[bool, str]:
    """添加用例到测试计划"""
    
    cookie = os.environ.get('YUNXIAO_COOKIE', '') or YUNXIAO_DEFAULT_COOKIE
    
    url = f"{OLD_API_BASE}/testPlan/{plan_id}/testcases"
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'cookie': cookie,
        'origin': 'https://devops.aliyun.com',
        'referer': f'https://devops.aliyun.com/testhub/plan/{plan_id}/case',
        'x-requested-with': 'XMLHttpRequest'
    }
    
    payload = {"testcaseIdentifierList": case_ids}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10, verify=False)
        result = response.json()
        
        # 检查成功: code=200 且 result=true
        if result.get('code') == 200 and result.get('result') == True:
            return True, f"成功添加 {len(case_ids)} 个用例到测试计划"
        else:
            return False, result.get('errorMsg') or result.get('msg') or str(result)[:100]
    except requests.Timeout:
        return False, "请求超时，可能是cookie已过期"
    except Exception as e:
        return False, str(e)


def update_test_result(session: requests.Session, headers: Dict, org_id: str, plan_id: str, 
                      case_id: str, status: str, executor: str = None) -> bool:
    """更新测试计划中的测试结果"""
    url = f"{BASE_URL}/organizations/{org_id}/testPlans/{plan_id}/testcases/{case_id}"
    
    payload = {"status": status}
    if executor:
        payload["executor"] = executor
    
    try:
        response = session.put(url, headers=headers, json=payload, timeout=10, verify=False)
        
        # 成功返回204 No Content
        if response.status_code in [200, 201, 204]:
            return True
        
        # 尝试解析响应
        try:
            result = response.json()
            if result.get('code') == 200:
                return True
            print(f"      更新结果失败: {result.get('errorMessage', '')}")
        except:
            pass
        
        return False
    except Exception as e:
        print(f"      更新结果异常: {str(e)[:100]}")
        return False


def extract_id_from_url(url: str) -> Optional[str]:
    """从URL中提取ID"""
    if not url:
        return None
    match = re.search(r'/(repo|plan)/([a-zA-Z0-9]+)', url)
    if match:
        return match.group(2)
    match = re.search(r'/([a-zA-Z0-9]{20,})/', url)
    if match:
        return match.group(1)
    return None


def get_user_info(token: str) -> Optional[Dict]:
    """获取当前用户信息"""
    headers = {'x-yunxiao-token': token}
    try:
        response = requests.get('https://openapi-rdc.aliyuncs.com/oapi/v1/platform/user', 
                               headers=headers, timeout=30, verify=False)
        result = response.json()
        if result.get('id'):
            return result
    except:
        pass
    return None


def get_directories(session: requests.Session, headers: Dict, org_id: str, repo_id: str) -> List[Dict]:
    """获取测试库所有目录"""
    url = f"{BASE_URL}/organizations/{org_id}/testRepos/{repo_id}/directories"
    try:
        response = session.get(url, headers=headers, timeout=30, verify=False)
        result = response.json()
        if isinstance(result, list):
            return result
    except:
        pass
    return []


def create_directory(session: requests.Session, headers: Dict, org_id: str, repo_id: str, 
                    name: str, parent_id: str = None) -> Optional[str]:
    """创建测试库目录"""
    url = f"{BASE_URL}/organizations/{org_id}/testRepos/{repo_id}/directories"
    payload = {"name": name}
    if parent_id:
        payload["parentIdentifier"] = parent_id
    try:
        response = session.post(url, headers=headers, json=payload, timeout=30, verify=False)
        result = response.json()
        if result.get('id'):
            print(f"      创建目录: {name} -> {result['id']}")
            return result['id']
        elif result.get('code') == 200:
            return result.get('id')
        else:
            print(f"      创建目录失败: {result}")
            return None
    except Exception as e:
        print(f"      创建目录异常: {str(e)[:50]}")
        return None


def build_directory_map(session: requests.Session, headers: Dict, org_id: str, repo_id: str) -> Tuple[str, Dict[str, str]]:
    """构建目录映射，返回(根目录ID, {路径:目录ID})"""
    directories = get_directories(session, headers, org_id, repo_id)
    
    root_id = None
    path_to_id = {}
    
    for dir_info in directories:
        dir_id = dir_info.get('id')
        dir_name = dir_info.get('name', '')
        parent_id = dir_info.get('parentId') or dir_info.get('parentIdentifier')
        
        if not parent_id:
            root_id = dir_id
        
        if dir_id:
            path_to_id[dir_name] = dir_id
    
    return root_id, path_to_id


def create_directory_structure(session: requests.Session, headers: Dict, org_id: str, repo_id: str,
                              root_id: str, dir_paths: List[List[str]]) -> Dict[str, str]:
    """创建目录结构，返回 {路径: 目录ID}"""
    path_to_id = {}
    
    if root_id:
        path_to_id[""] = root_id
    
    for path_parts in dir_paths:
        current_parent = root_id
        current_path = ""
        
        for i, part in enumerate(path_parts):
            if current_path:
                full_path = current_path + " > " + part
            else:
                full_path = part
            
            if full_path in path_to_id:
                current_parent = path_to_id[full_path]
                current_path = full_path
            else:
                new_id = create_directory(session, headers, org_id, repo_id, part, current_parent)
                if new_id:
                    path_to_id[full_path] = new_id
                    current_parent = new_id
                    current_path = full_path
    
    return path_to_id


def extract_id_from_title(title: str) -> Optional[str]:
    """从title中提取用例ID"""
    import re
    # 匹配 [ID:xxx...] 格式
    match = re.search(r'\[ID:([a-zA-Z0-9]+)\.\.\.\]', title)
    if match:
        return match.group(1)
    
    # 匹配完整ID格式（labels中的完整ID）
    match = re.search(r'\[ID:([a-zA-Z0-9]+)\]', title)
    if match:
        return match.group(1)
    
    return None


def check_case_exists(session: requests.Session, headers: Dict, org_id: str, repo_id: str, case_id: str) -> bool:
    """检查用例是否存在"""
    url = f"{BASE_URL}/organizations/{org_id}/testRepos/{repo_id}/testcases/{case_id}"
    try:
        response = session.get(url, headers=headers, timeout=30, verify=False)
        result = response.json()
        return result.get('code') == 200 or result.get('success') or result.get('id')
    except:
        return False


def delete_testcase(session: requests.Session, headers: Dict, org_id: str, repo_id: str, case_id: str) -> bool:
    """删除测试用例"""
    url = f"{BASE_URL}/organizations/{org_id}/testRepos/{repo_id}/testcases/{case_id}"
    
    try:
        response = session.delete(url, headers=headers, timeout=30, verify=False)
        if response.status_code in [200, 201, 204]:
            return True
        try:
            result = response.json()
            if result.get('code') == 200 or result.get('success'):
                return True
            return False
        except:
            return response.status_code in [200, 201, 204]
    except:
        return False


def update_testcase(session: requests.Session, headers: Dict, org_id: str, repo_id: str, 
                    case_id: str, case: Dict, directory_id: str = None, assigned_to: str = None) -> Optional[str]:
    """更新测试用例 - 尝试内部API，失败则用官方API仅更新标题"""
    
    # 尝试使用内部API更新（支持更新前置条件和测试步骤）
    cookie = os.environ.get('YUNXIAO_COOKIE', '')
    if cookie:
        result = update_testcase_internal(case_id, case, cookie)
        if result:
            return case_id
    
    # 降级：使用官方API仅更新标题
    url = f"{BASE_URL}/organizations/{org_id}/testRepos/{repo_id}/testcases/{case_id}"
    
    payload = {
        "subject": case['title']
    }
    
    try:
        response = session.put(url, headers=headers, json=payload, timeout=30, verify=False)
        
        if response.status_code in [200, 201, 204]:
            return case_id  # 返回原始ID表示更新成功
        
        try:
            result = response.json()
            if result.get('code') == 200 or result.get('success') or result.get('id'):
                return case_id
            else:
                print(f"      更新失败: {result.get('errorMessage') or result.get('message')}")
                return None
        except:
            print(f"      更新失败: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"      请求异常: {str(e)[:100]}")
        return None


def update_testcase_internal(case_id: str, case: Dict, cookie: str) -> bool:
    """使用内部API更新测试用例详情（前置条件、测试步骤等）"""
    
    # 构建测试步骤
    steps = case.get('steps', [])
    step_content = []
    for step in steps:
        step_content.append({
            "step": step.get('step', ''),
            "expected": step.get('expected', '')
        })
    
    # 构建前置条件
    precondition = case.get('prerequisites', '')
    
    # 构建请求体
    payload = {
        "stepType": "TABLE",
        "stepContent": json.dumps(step_content, ensure_ascii=False),
        "stepContentFormat": "TEST_TABLE",
        "precondition": precondition,
        "preconditionFormat": "RICHTEXT",
        "expectedResult": "",
        "expectedResultFormat": "RICHTEXT",
        "testcaseIdentifier": case_id
    }
    
    # 使用内部API (PATCH方法)
    url = f"https://devops.aliyun.com/testhub/webapi/workitem/testcase/{case_id}/info"
    
    internal_headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'cookie': cookie,
        'origin': 'https://devops.aliyun.com',
        'referer': 'https://devops.aliyun.com/testhub/repo/2836810f9e15ed3c679364ef42/case',
        'x-requested-with': 'XMLHttpRequest'
    }
    
    try:
        response = requests.patch(url, headers=internal_headers, json=payload, timeout=10, verify=False)
        result = response.json()
        
        if result.get('code') == 200 and result.get('result') == True:
            return True
        
        return False
    except:
        return False


def create_testcase(session: requests.Session, headers: Dict, org_id: str, repo_id: str, 
                    case: Dict, directory_id: str = None, assigned_to: str = None) -> Optional[str]:
    """创建测试用例"""
    url = f"{BASE_URL}/organizations/{org_id}/testRepos/{repo_id}/testcases"
    
    payload = {
        "subject": case['title'],
        "preCondition": case.get('prerequisites', ''),
        "directoryId": directory_id,
        "testSteps": {
            "content": [{"step": s['step'], "expected": s.get('expected', '')} for s in case.get('steps', [])],
            "contentType": "TABLE"
        }
    }
    
    if assigned_to:
        payload["assignedTo"] = assigned_to
    
    try:
        response = session.post(url, headers=headers, json=payload, timeout=30, verify=False)
        result = response.json()
        
        case_id = result.get('id') or result.get('data', {}).get('id')
        if case_id:
            return case_id
        elif result.get('code') == 200 or result.get('success'):
            return result.get('data', {}).get('id') or result.get('id')
        else:
            print(f"      创建失败: {result.get('error') or result.get('message') or str(result)[:100]}")
            return None
    except Exception as e:
        print(f"      请求异常: {str(e)[:100]}")
        return None


def is_testcase_node(node: Dict) -> bool:
    """判断节点是否为测试用例节点"""
    markers = [m.get('markerId', '') for m in node.get('markers', [])]
    if 'c_symbol_pen' in markers or 'priority-1' in markers or 'priority-2' in markers:
        return True
    if 'star-red' in markers or 'symbol-pin' in markers:
        return False
    children = node.get('children', {}).get('attached', [])
    if children and len(children) > 0:
        return True
    return False


def normalize_title(title: str) -> str:
    """标准化标题用于匹配"""
    return title.strip()


def write_case_ids_to_xmind(xmind_file: str, cases: list) -> None:
    """将创建的用例ID回写到XMind文件的labels中"""
    try:
        with zipfile.ZipFile(xmind_file, 'r') as z:
            content = z.read('content.json').decode('utf-8')
            other_files = {name: z.read(name) for name in z.namelist() if name != 'content.json'}
        
        data = json.loads(content)
        
        case_title_to_id = {}
        for title, cid in cases:
            case_title_to_id[normalize_title(title)] = cid
        
        updated_count = 0
        matched_count = 0
        print(f"    待回写用例: {list(case_title_to_id.keys())}")
        
        def update_labels(obj):
            nonlocal updated_count, matched_count
            if isinstance(obj, dict):
                title = normalize_title(obj.get('title', ''))
                
                if title in case_title_to_id:
                    matched_count += 1
                    existing_labels = obj.get('labels', [])
                    new_id = case_title_to_id[title]
                    if new_id not in existing_labels:
                        obj['labels'] = existing_labels + [new_id]
                        print(f"    回写ID: {title[:30]} -> {new_id}")
                        updated_count += 1
                
                if 'children' in obj:
                    for child in obj['children'].get('attached', []):
                        update_labels(child)
        
        if isinstance(data, list):
            for sheet in data:
                update_labels(sheet)
        else:
            update_labels(data)
        
        print(f"    匹配到 {matched_count} 个节点，更新 {updated_count} 个标签")
        
        with zipfile.ZipFile(xmind_file + '.tmp', 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('content.json', json.dumps(data, ensure_ascii=False))
            for name, content in other_files.items():
                z.writestr(name, content)
        
        os.replace(xmind_file + '.tmp', xmind_file)
        print(f"  ✓ 已回写 {updated_count} 个用例ID")
    except Exception as e:
        print(f"  ✗ 回写失败: {str(e)[:100]}")


def upload_cases(xmind_file: str, auto_confirm: bool = False, dry_run: bool = False) -> Dict[str, int]:
    """上传XMind用例到云效"""
    
    print("\n" + "="*80)
    print("开始解析XMind文件...")
    print("="*80)
    
    data = parse_xmind_to_dict(xmind_file)
    config = data.get('config', {})
    
    org_id = config.get('organization_id', '')
    token = config.get('token', '')
    repo_url = config.get('repo', '')
    plan_url = config.get('plan', '')
    
    repo_id = extract_id_from_url(repo_url)
    plan_id = extract_id_from_url(plan_url)
    
    if not token:
        print("错误: 未找到token配置")
        return {"created": 0, "updated": 0, "failed": 0}
    
    if not org_id or not repo_id:
        print("错误: 未找到ORG_ID或REPO_ID配置")
        return {"created": 0, "updated": 0, "failed": 0}
    
    print(f"\n配置信息:")
    print(f"  organization_id: {org_id}")
    print(f"  repo_id: {repo_id}")
    print(f"  test_plan_id: {plan_id}")
    print(f"  token: {token[:20]}...")
    
    user_info = get_user_info(token)
    assigned_to = user_info.get('id') if user_info else None
    if assigned_to:
        print(f"  用户ID: {assigned_to}")
    
    requirements = data.get('cases', [])
    total_cases = sum(len(req['case_list']) for req in requirements)
    
    print(f"\n✓ 需求数: {len(requirements)}")
    print(f"✓ 用例数: {total_cases}")
    
    if not requirements:
        print("\n没有找到测试用例")
        return {"created": 0, "updated": 0, "failed": 0}
    
    print("\n" + "="*80)
    print("用例预览:")
    print("="*80)
    
    dir_paths = []
    for req in requirements:
        print(f"\n需求: {req['requirement_name']}")
        for i, case in enumerate(req['case_list'], 1):
            result = case.get('test_result') or '未执行'
            path = case.get('path', '')
            print(f"  {i}. {case['title']} [{case['priority']}] 结果:{result}")
            print(f"     路径: {path if path else '(根目录)'}")
            if path:
                parts = [p.strip() for p in path.split('>')]
                if parts not in dir_paths:
                    dir_paths.append(parts)
    
    if not auto_confirm and not dry_run:
        confirm = input("\n确认上传到云效? (y/n): ")
        if confirm.lower() != 'y':
            print("已取消")
            return {"created": 0, "updated": 0, "failed": 0}
    
    if dry_run:
        print("\n[DRY RUN] 试运行模式")
        return {"created": total_cases, "updated": 0, "failed": 0}
    
    headers = {
        'x-yunxiao-token': token,
        'Content-Type': 'application/json'
    }
    session = requests.Session()
    
    print("\n" + "="*80)
    print("获取/创建目录结构...")
    print("="*80)
    
    root_id, existing_dirs = build_directory_map(session, headers, org_id, repo_id)
    print(f"  根目录ID: {root_id}")
    print(f"  已有目录: {list(existing_dirs.keys())}")
    
    path_to_id = create_directory_structure(session, headers, org_id, repo_id, root_id, dir_paths)
    
    stats = {"created": 0, "updated": 0, "failed": 0}
    created_cases = []
    
    print("\n" + "="*80)
    print("开始上传到云效...")
    print("="*80)
    
    all_processed_ids = []  # 收集所有处理过的用例ID
    
    for req in requirements:
        print(f"\n需求: {req['requirement_name'][:50]}...")
        
        for case in req['case_list']:
            # 尝试从多个来源获取用例ID
            case_id = case.get('id')  # 从labels中获取
            if not case_id:
                # 从title中提取ID
                case_id = extract_id_from_title(case['title'])
            
            path = case.get('path', '')
            
            dir_id = root_id
            if path:
                parts = [p.strip() for p in path.split('>')]
                full_path = ' > '.join(parts)
                dir_id = path_to_id.get(full_path, root_id)
            
            # 清理title中的ID标记（用于显示）
            clean_title = case['title']
            import re
            clean_title = re.sub(r'\s*\[ID:[^\]]+\]', '', clean_title)
            
            print(f"\n  处理: {clean_title}")
            print(f"    目录ID: {dir_id}")
            
            # 检查用例是否存在
            if case_id:
                print(f"    检测到ID: {case_id[:8]}...")
                exists = check_case_exists(session, headers, org_id, repo_id, case_id)
                
                if exists:
                    # 更新用例
                    print(f"    → 用例已存在，执行更新...")
                    # 创建临时case副本，使用清理后的title
                    update_case = case.copy()
                    update_case['title'] = clean_title
                    if update_testcase(session, headers, org_id, repo_id, case_id, update_case, dir_id, assigned_to):
                        print(f"    → 更新成功! ID: {case_id}")
                        stats["updated"] += 1
                        all_processed_ids.append(case_id)  # 收集ID用于添加到测试计划
                    else:
                        stats["failed"] += 1
                    continue
                else:
                    print(f"    → 云效中不存在该ID，执行新建...")
            
            # 创建新用例
            create_case = case.copy()
            create_case['title'] = clean_title
            new_id = create_testcase(session, headers, org_id, repo_id, create_case, dir_id, assigned_to)
            if new_id:
                print(f"    → 创建成功! ID: {new_id}")
                stats["created"] += 1
                created_cases.append((clean_title, new_id))
                all_processed_ids.append(new_id)  # 收集ID用于添加到测试计划
            else:
                stats["failed"] += 1
    
    if created_cases and not dry_run:
        print("\n" + "="*80)
        print("正在回写用例ID到XMind文件...")
        print("="*80)
        write_case_ids_to_xmind(xmind_file, created_cases)
    
    print("\n" + "="*80)
    print("导入完成!")
    print("="*80)
    print(f"  新建: {stats['created']}")
    print(f"  更新: {stats['updated']}")
    print(f"  失败: {stats['failed']}")
    print(f"  创建目录: {len(path_to_id)}")
    
    # 尝试添加用例到测试计划
    if plan_id and all_processed_ids and not dry_run:
        print("\n" + "="*80)
        print("尝试添加用例到测试计划...")
        print("="*80)
        
        success, msg = add_cases_to_testplan(plan_id, all_processed_ids, token)
        
        if success:
            print(f"  → 添加到测试计划成功!")
        else:
            print(f"  → 添加失败: {msg}")
            print("  → 请手动添加用例到测试计划，或更新cookie后重试")
    
    return stats


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("XMind用例上传到云效平台 V2")
        print("用法: python3 upload_v2.py <xmind文件> [-y] [--dry-run]")
        sys.exit(1)
    
    xmind_file = sys.argv[1]
    auto_confirm = '-y' in sys.argv
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    
    if not os.path.exists(xmind_file):
        print(f"错误: 文件不存在 {xmind_file}")
        sys.exit(1)
    
    upload_cases(xmind_file, auto_confirm, dry_run)


if __name__ == '__main__':
    main()
