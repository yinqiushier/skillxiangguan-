---
name: xmind-to-yunxiao
description: Convert XMind test cases to Alibaba Cloud Yunxiao DevOps platform with automatic creation, update, and result synchronization
license: MIT
compatibility: opencode
metadata:
  version: "5.0"
  author: OpenCode AI Assistant
  platform: Alibaba Cloud Yunxiao
---

# XMind转云效测试用例工具

## 概述

将XMind思维导图格式的测试用例批量导入到阿里云云效测试管理平台。支持用例创建、更新、目录结构创建、测试计划关联、测试结果同步等功能。

**v5.0 特性**：
- 支持用例存在性检查（智能更新）
- 目录结构自动创建
- 测试结果同步到测试计划
- ID回写到XMind文件

## 工作目录

**工作目录**: `/mnt/c/Users/28711/xmind/`

**核心文件**:
- `upload_v2.py` - 主上传脚本
- `sync_results.py` - 测试结果同步脚本
- `xmind_parser.py` - XMind解析器
- `demo1.xmind` - 测试文件

## XMind文件格式

### 结构规范

```
根节点标题: 用例库URL-测试计划URL
├─ 目录节点 [star-red/pushpin-red]
│  └─ 子目录
│     ├─ [star-red] 需求名称
│     │  ├─ 前置条件
│     │  │  └─ 案例1 [c_symbol_pen, priority-1]  ← 测试用例
│     │  │     ├─ 步骤1
│     │  │     │  └─ 期望结果 [tag-green]  ← 测试结果
│     │  │     └─ 步骤2
│     │  │        └─ 期望结果 [tag-red]
│     │  └─ 案例2 [c_symbol_pen]
```

### 标记说明

| 标记 | 含义 |
|------|------|
| `c_symbol_pen` | 测试用例标记 |
| `star-red` | 需求关联/目录 |
| `priority-1` | P0优先级 |
| `priority-2` | P1优先级 |
| `priority-3` | P2优先级 |
| `priority-4` | P3优先级 |
| `tag-green` | PASS测试结果 |
| `tag-red` | FAILURE测试结果 |
| `tag-orange` | BLOCKED测试结果 |
| `tag-grey` | POSTPONE测试结果 |

### 配置sheet格式

在XMind中添加配置sheet：
```
根节点: 配置
├─ 测试计划: https://devops.aliyun.com/testhub/plan/PLAN_ID/case
├─ 用例库: https://devops.aliyun.com/testhub/repo/REPO_ID/case
├─ 令牌: pt-youte_access_token
└─ 组织: ORG_ID
```

## API集成

### 认证方式

**官方API (openapi-rdc.aliyuncs.com)**:
```python
headers = {
    'x-yunxiao-token': 'your_token',
    'Content-Type': 'application/json'
}
```

**内部API (devops.aliyun.com)** - 需要Cookie:
```python
headers = {
    'accept': 'application/json, text/plain, */*',
    'content-type': 'application/json',
    'cookie': 'full_cookie_string',
    'origin': 'https://devops.aliyun.com',
    'referer': 'https://devops.aliyun.com/testhub/...',
    'x-requested-with': 'XMLHttpRequest'
}
```

### 关键API端点

| 功能 | 方法 | URL |
|------|------|-----|
| 创建用例 | POST | `https://openapi-rdc.aliyuncs.com/oapi/v1/testhub/organizations/{org_id}/testRepos/{repo_id}/testcases` |
| 更新用例 | PUT | `https://openapi-rdc.aliyuncs.com/oapi/v1/testhub/organizations/{org_id}/testRepos/{repo_id}/testcases/{case_id}` |
| 更新用例详情 | PATCH | `https://devops.aliyun.com/testhub/webapi/workitem/testcase/{case_id}/info` |
| 获取目录 | GET | `https://openapi-rdc.aliyuncs.com/oapi/v1/testhub/organizations/{org_id}/testRepos/{repo_id}/directories` |
| 创建目录 | POST | `https://openapi-rdc.aliyuncs.com/oapi/v1/testhub/organizations/{org_id}/testRepos/{repo_id}/directories` |
| 添加到测试计划 | POST | `https://devops.aliyun.com/testhub/webapi/workspace/testPlan/{plan_id}/testcases` |
| 获取测试计划用例 | GET | `https://devops.aliyun.com/testhub/webapi/workspace/testPlan/{plan_id}/testcase/{case_id}` |

### 测试结果状态映射

| XMind标记 | 云效状态 |
|-----------|----------|
| `tag-green` | PASS |
| `tag-red` | FAILURE |
| `tag-orange` | BLOCKED |
| `tag-grey` | POSTPONE |
| 无标记 | TODO |

### 测试结果判断规则

**以最后一个叶子节点的结果为主**：

1. 递归收集用例下所有叶子节点的结果标记
2. 取最后一个叶子节点的结果作为测试结果
3. 如果没有结果，设置为 TODO

示例：
```
新增案例3
└─ 期望结果3
   ├─ 实际结果，测试通过 [tag-red]
   └─ 实际结果，测试通过 [tag-green]  ← 最后一个叶子节点
结果: PASS
```

## 使用方法

### 上传用例

```bash
cd /mnt/c/Users/28711/xmind

# 交互式模式
python3 upload_v2.py demo1.xmind

# 自动确认模式
python3 upload_v2.py demo1.xmind -y

# 试运行模式（不实际上传）
python3 upload_v2.py demo1.xmind --dry-run
```

### 同步测试结果

```bash
python3 sync_results.py demo1.xmind
```

### 设置Cookie（用于内部API）

```bash
export YUNXIAO_COOKIE="complete_cookie_string_from_browser"
```

## 核心代码

### 1. XMind解析器 (xmind_parser.py)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XMind测试用例解析工具 V5
"""

import zipfile
import json
import sys
import re
import os
from typing import List, Dict, Any, Set, Optional, Tuple

def get_title(node: Dict) -> str:
    return node.get('title', '').strip()

def get_markers(node: Dict) -> List[str]:
    markers = []
    if 'markers' in node:
        for marker in node['markers']:
            marker_id = marker.get('markerId', '')
            markers.append(marker_id)
    return markers

def has_marker(node: Dict, marker_id: str) -> bool:
    return marker_id in get_markers(node)

def get_priority(node: Dict) -> str:
    markers = get_markers(node)
    if 'priority-1' in markers: return 'P0'
    elif 'priority-2' in markers: return 'P1'
    elif 'priority-3' in markers: return 'P2'
    elif 'priority-4' in markers: return 'P3'
    return 'P2'

def get_test_results_from_markers(node: Dict) -> List[str]:
    markers = get_markers(node)
    tag_mapping = {
        'tag-green': 'PASS',
        'tag-red': 'FAILED',
        'tag-orange': 'BLOCKED',
        'tag-grey': 'POSTPONE'
    }
    results = []
    for tag, result in tag_mapping.items():
        if tag in markers:
            results.append(result)
    return results

def is_testcase_like(node: Dict) -> bool:
    markers = get_markers(node)
    title = get_title(node).lower()
    
    if 'c_symbol_pen' in markers:
        return True
    
    if 'star-red' in markers or 'symbol-pin' in markers or 'pushpin-red' in markers:
        return False
    
    prerequisite_keywords = ['前置条件', 'prerequisite', '前提', '登录', '已登录']
    if any(keyword in title for keyword in prerequisite_keywords):
        return False
    
    children = node.get('children', {}).get('attached', [])
    if children:
        return True
    
    return False

def parse_single_step(step_node: Dict, parent_path: str = "") -> List[Dict]:
    """解析单个步骤"""
    steps = []
    step_title = get_title(step_node)
    step_children = step_node.get('children', {}).get('attached', [])
    
    if parent_path:
        step_name = f"{parent_path}>{step_title}"
    else:
        step_name = step_title
    
    expected_result = ""
    nested_step_nodes = []
    step_results = []
    
    for child in step_children:
        child_title = get_title(child)
        child_markers = get_markers(child)
        
        has_priority_marker = 'priority-1' in child_markers or 'priority-2' in child_markers or 'c_symbol_pen' in child_markers
        step_keywords = ['步骤', '操作', '输入', '点击', '选择', '填写', '提交']
        is_step_keyword = any(keyword in child_title for keyword in step_keywords)
        has_result_marker = any(tag in ['tag-green', 'tag-red', 'tag-orange', 'tag-grey'] for tag in child_markers)
        
        is_step = has_priority_marker or is_step_keyword
        
        if is_step:
            nested_step_nodes.append(child)
        elif has_result_marker:
            child_results = get_test_results_from_markers(child)
            step_results.extend(child_results)
        elif not expected_result and '实际结果' not in child_title:
            expected_result = child_title
    
    steps.append({
        'step': step_name,
        'expected': expected_result,
        'result': step_results if step_results else []
    })
    
    for nested_node in nested_step_nodes:
        nested_steps = parse_single_step(nested_node, step_name)
        steps.extend(nested_steps)
    
    return steps

def parse_case_steps(node: Dict, case_title: str, has_c_symbol_pen: bool = True) -> Tuple[List[Dict], Optional[str]]:
    """解析测试用例的步骤和结果"""
    children = node.get('children', {}).get('attached', [])
    steps = []
    
    if len(children) == 1:
        # 单步骤用例
        step_content = case_title
        expected_node = children[0]
        expected_result = get_title(expected_node)
        step_results = get_test_results_from_markers(expected_node)
        
        steps.append({
            'step': step_content,
            'expected': expected_result,
            'result': step_results if step_results else []
        })
    else:
        # 多步骤用例
        for step_node in children:
            nested_steps = parse_single_step(step_node, "")
            steps.extend(nested_steps)
    
    # 计算整体测试结果
    overall_result = None
    has_failed = False
    
    for step in steps:
        results = step['result']
        if 'FAILED' in results or 'BLOCKED' in results:
            has_failed = True
    
    if has_failed:
        overall_result = "FAILED"
    else:
        for step in reversed(steps):
            if step['result']:
                overall_result = step['result'][-1]
                break
    
    return steps, overall_result

def parse_tree(node: Dict, path: List[str], current_requirement: Optional[Dict],
               prerequisites: List[str], found_star_red: bool,
               all_requirements: List[Dict], case_ids: Set[str], verbose: bool = False) -> None:
    """递归解析XMind树结构"""
    title = get_title(node)
    children = node.get('children', {}).get('attached', [])
    markers = get_markers(node)
    
    if has_marker(node, 'star-red'):
        # 需求节点
        req_name = title
        new_requirement = {
            'requirement_name': req_name,
            'requirement_url': f"https://devops.aliyun.com/projex/req/UNKNOWN# 《{title}》",
            'case_list': []
        }
        
        for child in children:
            parse_tree(child, [], new_requirement, [], True, all_requirements, case_ids, verbose)
        
        if new_requirement['case_list']:
            all_requirements.append(new_requirement)
        return
    
    if is_testcase_like(node):
        # 测试用例
        if current_requirement is None:
            return
        
        labels = node.get('labels', [])
        case_id = None
        for label in labels:
            if isinstance(label, str) and len(label) > 15:
                case_id = label
                break
        
        has_c_symbol_pen = 'c_symbol_pen' in markers
        steps, overall_result = parse_case_steps(node, title, has_c_symbol_pen)
        
        case = {
            'id': case_id,
            'title': title,
            'path': ' > '.join(path) if path else '',
            'prerequisites': '>'.join(prerequisites) if prerequisites else '',
            'priority': get_priority(node),
            'steps': steps,
            'test_result': overall_result
        }
        
        current_requirement['case_list'].append(case)
        
        if case_id:
            case_ids.add(case_id)
        return
    
    # 递归处理子节点
    for child in children:
        parse_tree(child, path, current_requirement, prerequisites, found_star_red, all_requirements, case_ids, verbose)

def parse_xmind_to_dict(filename: str, verbose: bool = False) -> Dict[str, Any]:
    """解析XMind文件"""
    with zipfile.ZipFile(filename, 'r') as z:
        content_json = z.read('content.json').decode('utf-8')
    
    xmind_data = json.loads(content_json)
    
    config = {"plan": "", "repo": "", "token": "", "organization_id": ""}
    all_requirements = []
    case_ids = set()
    
    def parse_config_xmind(root_topic: Dict) -> Dict[str, str]:
        """解析配置sheet"""
        cfg = {"plan": "", "repo": "", "token": "", "organization_id": ""}
        children = root_topic.get('children', {}).get('attached', [])
        
        for child in children:
            title = get_title(child).strip()
            child_children = child.get('children', {}).get('attached', [])
            if not child_children:
                continue
            value = get_title(child_children[0]).strip()
            
            if '测试计划' in title or 'plan' in title.lower():
                cfg['plan'] = value
            elif '用例库' in title or 'repo' in title.lower() or '库' in title:
                cfg['repo'] = value
            elif '令牌' in title or 'token' in title.lower():
                cfg['token'] = value
            elif '组织' in title or 'organization' in title.lower():
                cfg['organization_id'] = value
        
        return cfg
    
    def is_config_sheet(root_topic: Dict) -> bool:
        title = get_title(root_topic)
        if '配置' in title or 'config' in title.lower():
            return True
        children = root_topic.get('children', {}).get('attached', [])
        config_keywords = ['测试计划', '用例库', '令牌', 'token', '组织', 'organization']
        for child in children:
            child_title = get_title(child).lower()
            if any(keyword.lower() in child_title for keyword in config_keywords):
                return True
        return False
    
    for sheet in xmind_data:
        root_topic = sheet['rootTopic']
        root_title = get_title(root_topic)
        
        if is_config_sheet(root_topic):
            sheet_config = parse_config_xmind(root_topic)
            for key, value in sheet_config.items():
                if value:
                    config[key] = value
        else:
            children = root_topic.get('children', {}).get('attached', [])
            for child in children:
                parse_tree(child, [], None, [], False, all_requirements, case_ids, verbose)
    
    return {"config": config, "cases": all_requirements}
```

### 2. 上传脚本 (upload_v2.py)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XMind用例上传到云效平台 V2
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

def add_cases_to_testplan(plan_id: str, case_ids: List[str], token: str) -> Tuple[bool, str]:
    """添加用例到测试计划"""
    cookie = os.environ.get('YUNXIAO_COOKIE', '')
    if not cookie:
        return False, "未设置YUNXIAO_COOKIE环境变量，跳过"
    
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
        if result.get('code') == 200 and result.get('result') == True:
            return True, f"成功添加 {len(case_ids)} 个用例到测试计划"
        else:
            return False, result.get('errorMsg') or result.get('msg') or str(result)[:100]
    except requests.Timeout:
        return False, "请求超时，可能是cookie已过期"
    except Exception as e:
        return False, str(e)

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
    """构建目录映射"""
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
    """创建目录结构"""
    path_to_id = {}
    if root_id:
        path_to_id[""] = root_id
    
    for path_parts in dir_paths:
        current_parent = root_id
        current_path = ""
        
        for part in path_parts:
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

def check_case_exists(session: requests.Session, headers: Dict, org_id: str, repo_id: str, case_id: str) -> bool:
    """检查用例是否存在"""
    url = f"{BASE_URL}/organizations/{org_id}/testRepos/{repo_id}/testcases/{case_id}"
    try:
        response = session.get(url, headers=headers, timeout=30, verify=False)
        result = response.json()
        return result.get('code') == 200 or result.get('success') or result.get('id')
    except:
        return False

def update_testcase_internal(case_id: str, case: Dict, cookie: str) -> bool:
    """使用内部API更新测试用例详情"""
    steps = case.get('steps', [])
    step_content = []
    for step in steps:
        step_content.append({
            "step": step.get('step', ''),
            "expected": step.get('expected', '')
        })
    
    precondition = case.get('prerequisites', '')
    
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
    
    url = f"https://devops.aliyun.com/testhub/webapi/workitem/testcase/{case_id}/info"
    internal_headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'cookie': cookie,
        'origin': 'https://devops.aliyun.com',
        'referer': 'https://devops.aliyun.com/testhub/repo/REPO_ID/case',
        'x-requested-with': 'XMLHttpRequest'
    }
    
    try:
        response = requests.patch(url, headers=internal_headers, json=payload, timeout=10, verify=False)
        result = response.json()
        return result.get('code') == 200 and result.get('result') == True
    except:
        return False

def update_testcase(session: requests.Session, headers: Dict, org_id: str, repo_id: str, 
                    case_id: str, case: Dict, directory_id: str = None, assigned_to: str = None) -> Optional[str]:
    """更新测试用例"""
    cookie = os.environ.get('YUNXIAO_COOKIE', '')
    if cookie:
        result = update_testcase_internal(case_id, case, cookie)
        if result:
            return case_id
    
    # 降级：使用官方API仅更新标题
    url = f"{BASE_URL}/organizations/{org_id}/testRepos/{repo_id}/testcases/{case_id}"
    payload = {"subject": case['title']}
    
    try:
        response = session.put(url, headers=headers, json=payload, timeout=30, verify=False)
        if response.status_code in [200, 201, 204]:
            return case_id
        try:
            result = response.json()
            if result.get('code') == 200 or result.get('success') or result.get('id'):
                return case_id
        except:
            pass
        return None
    except Exception as e:
        return None

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

def write_case_ids_to_xmind(xmind_file: str, cases: list) -> None:
    """将创建的用例ID回写到XMind文件"""
    try:
        with zipfile.ZipFile(xmind_file, 'r') as z:
            content = z.read('content.json').decode('utf-8')
            other_files = {name: z.read(name) for name in z.namelist() if name != 'content.json'}
        
        data = json.loads(content)
        
        case_title_to_id = {}
        for title, cid in cases:
            case_title_to_id[title.strip()] = cid
        
        updated_count = 0
        matched_count = 0
        print(f"    待回写用例: {list(case_title_to_id.keys())}")
        
        def update_labels(obj):
            nonlocal updated_count, matched_count
            if isinstance(obj, dict):
                title = obj.get('title', '').strip()
                
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
    
    print(f"\n配置信息:")
    print(f"  organization_id: {org_id}")
    print(f"  repo_id: {repo_id}")
    print(f"  test_plan_id: {plan_id}")
    print(f"  token: {token[:20]}...")
    
    requirements = data.get('cases', [])
    total_cases = sum(len(req['case_list']) for req in requirements)
    
    print(f"\n✓ 需求数: {len(requirements)}")
    print(f"✓ 用例数: {total_cases}")
    
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
    all_processed_ids = []
    
    print("\n" + "="*80)
    print("开始上传到云效...")
    print("="*80)
    
    for req in requirements:
        print(f"\n需求: {req['requirement_name'][:50]}...")
        
        for case in req['case_list']:
            case_id = case.get('id')
            path = case.get('path', '')
            
            dir_id = root_id
            if path:
                parts = [p.strip() for p in path.split('>')]
                full_path = ' > '.join(parts)
                dir_id = path_to_id.get(full_path, root_id)
            
            clean_title = case['title']
            clean_title = re.sub(r'\s*\[ID:[^\]]+\]', '', clean_title)
            
            print(f"\n  处理: {clean_title}")
            print(f"    目录ID: {dir_id}")
            
            if case_id:
                print(f"    检测到ID: {case_id[:8]}...")
                exists = check_case_exists(session, headers, org_id, repo_id, case_id)
                
                if exists:
                    print(f"    → 用例已存在，执行更新...")
                    update_case = case.copy()
                    update_case['title'] = clean_title
                    if update_testcase(session, headers, org_id, repo_id, case_id, update_case, dir_id, None):
                        print(f"    → 更新成功! ID: {case_id}")
                        stats["updated"] += 1
                        all_processed_ids.append(case_id)
                    else:
                        stats["failed"] += 1
                    continue
                else:
                    print(f"    → 云效中不存在该ID，执行新建...")
            
            create_case = case.copy()
            create_case['title'] = clean_title
            new_id = create_testcase(session, headers, org_id, repo_id, create_case, dir_id, None)
            if new_id:
                print(f"    → 创建成功! ID: {new_id}")
                stats["created"] += 1
                created_cases.append((clean_title, new_id))
                all_processed_ids.append(new_id)
            else:
                stats["failed"] += 1
    
    if created_cases:
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
    
    if plan_id and all_processed_ids:
        print("\n" + "="*80)
        print("尝试添加用例到测试计划...")
        print("="*80)
        
        success, msg = add_cases_to_testplan(plan_id, all_processed_ids, token)
        
        if success:
            print(f"  → 添加到测试计划成功!")
        else:
            print(f"  → 添加失败: {msg}")
    
    return stats

def main():
    if len(sys.argv) < 2:
        print("XMind用例上传到云效平台 V2")
        print("用法: python3 upload_v2.py <xmind文件> [-y] [--dry-run]")
        sys.exit(1)
    
    xmind_file = sys.argv[1]
    auto_confirm = '-y' in sys.argv
    dry_run = '--dry-run' in sys.argv
    
    if not os.path.exists(xmind_file):
        print(f"错误: 文件不存在 {xmind_file}")
        sys.exit(1)
    
    upload_cases(xmind_file, auto_confirm, dry_run)

if __name__ == '__main__':
    main()
```

### 3. 测试结果同步 (sync_results.py)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步测试结果 - 从XMind读取测试结果标记，同步到云效
"""

import json
import sys
import os
import requests
import zipfile
from typing import Dict, List, Optional

requests.packages.urllib3.disable_warnings()

RESULT_MAP = {
    'tag-green': 'PASS',
    'tag-red': 'FAILURE',
    'tag-orange': 'BLOCKED',
    'tag-grey': 'POSTPONE'
}

def find_result_in_node(node):
    """递归查找节点及其子节点中的'实际结果'标记"""
    title = node.get('title', '').lower()
    markers = [m.get('markerId', '') for m in node.get('markers', [])]
    
    if '实际' in node.get('title', '') or 'actual' in title:
        if markers:
            return markers
    
    children = node.get('children', {})
    for child in children.get('attached', []):
        result = find_result_in_node(child)
        if result:
            return result
    return []

def find_all_markers(node):
    """递归查找节点及其所有子节点的标记"""
    markers = [m.get('markerId', '') for m in node.get('markers', [])]
    children = node.get('children', {})
    for child in children.get('attached', []):
        markers.extend(find_all_markers(child))
    return markers

def read_xmind_results(xmind_file: str) -> List[Dict]:
    """从XMind文件读取测试结果"""
    results = []
    
    with zipfile.ZipFile(xmind_file, 'r') as z:
        content = json.loads(z.read('content.json'))
    
    def find_cases(node):
        cases = []
        children = node.get('children', {}).get('attached', [])
        for child in children:
            markers = [m.get('markerId', '') for m in child.get('markers', [])]
            
            is_case = any(m in ['c_symbol_pen', 'priority-1', 'priority-2', 'priority-3', 'priority-4'] for m in markers)
            if not is_case:
                cases.extend(find_cases(child))
                continue
            
            step_results = []
            steps = child.get('children', {}).get('attached', [])
            
            for step in steps:
                step_title = step.get('title', '')
                step_markers = [m.get('markerId', '') for m in step.get('markers', [])]
                
                if not step_markers:
                    step_markers = find_result_in_node(step)
                
                if step_markers:
                    step_results.append(step_markers)
            
            test_result = None
            
            for markers_list in step_results:
                if 'tag-red' in markers_list:
                    test_result = 'FAILURE'
                    break
            
            if test_result is None and step_results:
                last_markers = step_results[-1]
                for marker in last_markers:
                    if marker in RESULT_MAP:
                        test_result = RESULT_MAP[marker]
                        break
            
            if test_result is None:
                test_result = 'TODO'
            
            labels = child.get('labels', [])
            case_id = None
            for label in labels:
                if isinstance(label, str) and len(label) > 15:
                    case_id = label
                    break
            
            title = child.get('title', '未知')
            
            if case_id:
                results.append({
                    'title': title,
                    'id': case_id,
                    'status': test_result
                })
            
            cases.extend(find_cases(child))
        return cases
    
    for sheet in content:
        root = sheet.get('rootTopic', {})
        find_cases(root)
    
    return results

def sync_results(xmind_file: str, org_id: str, plan_id: str, token: str, user_id: str):
    """同步测试结果到云效"""
    print("=" * 80)
    print("同步测试结果到云效")
    print("=" * 80)
    
    cases = read_xmind_results(xmind_file)
    
    if not cases:
        print("未找到测试结果标记")
        return
    
    print(f"\n找到 {len(cases)} 个用例")
    
    stats = {'PASS': 0, 'FAILURE': 0, 'BLOCKED': 0, 'POSTPONE': 0, 'TODO': 0}
    for case in cases:
        status = case.get('status') or 'TODO'
        stats[status] = stats.get(status, 0) + 1
    
    print("\n结果统计:")
    for k, v in stats.items():
        if v > 0:
            print(f"  {k}: {v}")
    
    print("\n有结果标记的用例:")
    for case in cases:
        if case.get('status'):
            print(f"  - {case['title'][:40]}: {case['status']} ({case['id'][:16]}...)")
    
    headers = {
        'x-yunxiao-token': token,
        'Content-Type': 'application/json'
    }
    
    print("\n" + "=" * 80)
    print("开始同步...")
    print("=" * 80)
    
    success_count = 0
    for case in cases:
        if not case.get('status'):
            continue
        
        case_id = case['id']
        status = case['status']
        
        url = f"https://openapi-rdc.aliyuncs.com/oapi/v1/testhub/organizations/{org_id}/testPlans/{plan_id}/testcases/{case_id}"
        payload = {'executor': user_id, 'status': status}
        
        try:
            response = requests.put(url, headers=headers, json=payload, timeout=10, verify=False)
            if response.status_code in [200, 201, 204]:
                success_count += 1
                print(f"  ✓ {case['title'][:30]}: {status}")
            else:
                print(f"  ✗ {case['title'][:30]}: {status} (失败)")
        except Exception as e:
            print(f"  ✗ {case['title'][:30]}: {status} (异常: {e})")
    
    print("\n" + "=" * 80)
    print(f"同步完成: 成功 {success_count} 个")
    print("=" * 80)

def main():
    if len(sys.argv) < 2:
        print("测试结果同步工具")
        print("用法: python sync_results.py <xmind文件>")
        sys.exit(1)
    
    xmind_file = sys.argv[1]
    
    if not os.path.exists(xmind_file):
        print(f"文件不存在: {xmind_file}")
        sys.exit(1)
    
    # 默认配置
    org_id = os.environ.get('YUNXIAO_ORG_ID', '64db414e9538a17091157f29')
    token = os.environ.get('YUNXIAO_TOKEN', 'pt-ytejPEd5vDj7WwRqD6Uxs95m_0a5c8d47-37bd-4561-a3e9-c3a0bc97571a')
    user_id = os.environ.get('YUNXIAO_USER_ID', '669f49c45e4ded97ce902e11')
    plan_id = os.environ.get('YUNXIAO_PLAN_ID', '41726a11f16f5e93cea600f656')
    
    sync_results(xmind_file, org_id, plan_id, token, user_id)

if __name__ == '__main__':
    main()
```

## 测试结果同步（手动模式）

### 同步测试计划执行结果（正确API）:

```python
import requests

token = "your_access_token"
org_id = "organization_id"
plan_id = "test_plan_id"
case_id = "case_id"

url = f"https://openapi-rdc.aliyuncs.com/oapi/v1/testhub/organizations/{org_id}/testPlans/{plan_id}/testcases/{case_id}"
headers = {"x-yunxiao-token": token}

# status: PASS, FAILURE, BLOCKED, POSTPONE
response = requests.put(url, headers=headers, json={"status": "PASS"})
print(response.status_code)  # 204 = 成功
```

### 同步用例详情（使用Cookie）:

```python
import requests

cookie = "your_full_cookie_from_browser"

headers = {
    'content-type': 'application/json',
    'cookie': cookie,
    'origin': 'https://devops.aliyun.com',
    'x-requested-with': 'XMLHttpRequest'
}

case_id = 'case_id_here'
url = f'https://devops.aliyun.com/testhub/webapi/workitem/testcase/{case_id}/info'
payload = {'testResult': 'PASS'}  # PASS, FAILURE, BLOCKED, POSTPONE, TODO

resp = requests.patch(url, headers=headers, json=payload, timeout=10, verify=False)
print(resp.json())

# 添加用例到测试计划
plan_id = 'plan_id_here'
url = f'https://devops.aliyun.com/testhub/webapi/workspace/testPlan/{plan_id}/testcases'
payload = {"testcaseIdentifierList": ["case_id_1", "case_id_2"]}

resp = requests.post(url, headers=headers, json=payload, timeout=10, verify=False)
print(resp.json())
```

## 获取Cookie

1. 浏览器访问 `https://devops.aliyun.com`
2. 登录后按 F12 打开开发者工具
3. 切换到 Network 标签
4. 访问任意测试相关页面
5. 找到任意请求，复制完整的 Cookie 头

## 已知问题

1. ~~**测试计划结果同步**~~ - 已解决：使用 openapi-rdc API
2. **ID回写**：依赖XMind文件格式支持，部分XMind文件可能不支持labels字段
3. **Cookie过期**：Cookie会过期，需要定期更新

## 配置文件

可以在XMind中添加配置sheet，或使用环境变量：

```bash
export YUNXIAO_TOKEN="your_token"
export YUNXIAO_ORG_ID="org_id"
export YUNXIAO_PLAN_ID="plan_id"
export YUNXIAO_USER_ID="user_id"
export YUNXIAO_COOKIE="full_cookie_string"
```
