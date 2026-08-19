#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步测试结果 - 从XMind读取测试结果标记，同步到云效测试计划
"""

import json
import sys
import os
import requests
import zipfile
from typing import Dict, List, Optional

requests.packages.urllib3.disable_warnings()

# 测试结果映射
RESULT_MAP = {
    'tag-green': 'PASS',
    'tag-red': 'FAILURE',
    'tag-orange': 'BLOCKED',
    'tag-grey': 'POSTPONE'
}


def find_result_in_node(node):
    '''递归查找节点及其子节点中的"实际结果"标记'''
    # 检查当前节点是否是"实际结果"类型
    title = node.get('title', '').lower()
    markers = [m.get('markerId', '') for m in node.get('markers', [])]
    
    if '实际' in node.get('title', '') or 'actual' in title:
        if markers:
            return markers
    
    # 递归查找子节点
    children = node.get('children', {})
    for child in children.get('attached', []):
        result = find_result_in_node(child)
        if result:
            return result
    return []


def find_all_markers(node):
    '''递归查找节点及其所有子节点的标记'''
    markers = [m.get('markerId', '') for m in node.get('markers', [])]
    children = node.get('children', {})
    for child in children.get('attached', []):
        markers.extend(find_all_markers(child))
    return markers


def read_xmind_results(xmind_file: str) -> List[Dict]:
    """从XMind文件读取测试结果
    
    规则:
    1. 检查用例的所有步骤
    2. 如果存在 tag-red，结果为 FAILURE
    3. 否则获取最后一个有标记步骤的标记作为结果
    4. 如果所有步骤都没有标记，结果为 TODO
    """
    results = []
    
    with zipfile.ZipFile(xmind_file, 'r') as z:
        content = json.loads(z.read('content.json'))
    
    def find_cases(node):
        cases = []
        children = node.get('children', {}).get('attached', [])
        for child in children:
            markers = [m.get('markerId', '') for m in child.get('markers', [])]
            
            # 检查是否有用例标记
            is_case = any(m in ['c_symbol_pen', 'priority-1', 'priority-2', 'priority-3', 'priority-4'] for m in markers)
            if not is_case:
                cases.extend(find_cases(child))
                continue
            
            # 遍历所有子节点（步骤）
            step_results = []
            steps = child.get('children', {}).get('attached', [])
            
            for step in steps:
                step_title = step.get('title', '')
                
                # 获取该步骤的直接标记
                step_markers = [m.get('markerId', '') for m in step.get('markers', [])]
                
                # 如果步骤本身没有标记，递归查找子节点中的"实际结果"标记
                if not step_markers:
                    step_markers = find_result_in_node(step)
                
                if step_markers:
                    step_results.append(step_markers)
            
            # 判断结果
            test_result = None
            
            # 1. 检查是否有失败的步骤
            for markers_list in step_results:
                if 'tag-red' in markers_list:
                    test_result = 'FAILURE'
                    break
            
            # 2. 如果没有失败，获取最后一个有标记的步骤结果
            if test_result is None and step_results:
                last_markers = step_results[-1]
                for marker in last_markers:
                    if marker in RESULT_MAP:
                        test_result = RESULT_MAP[marker]
                        break
            
            # 3. 如果没有结果，设置为 TODO
            if test_result is None:
                test_result = 'TODO'
            
            # 获取用例ID
            labels = child.get('labels', [])
            case_id = None
            for label in labels:
                if isinstance(label, str) and len(label) > 15:
                    case_id = label
                    break
                elif isinstance(label, dict) and 'id' in label:
                    case_id = label['id']
                    break
            
            # 获取标题
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
    
    # 读取XMind中的测试结果
    cases = read_xmind_results(xmind_file)
    
    if not cases:
        print("未找到测试结果标记")
        return
    
    print(f"\n找到 {len(cases)} 个用例")
    
    # 统计结果
    stats = {'PASS': 0, 'FAILURE': 0, 'BLOCKED': 0, 'POSTPONE': 0, 'TODO': 0}
    for case in cases:
        status = case.get('status') or '未标记'
        if status == '未标记':
            stats['TODO'] += 1
        else:
            stats[status] += 1
    
    print("\n结果统计:")
    for k, v in stats.items():
        if v > 0:
            print(f"  {k}: {v}")
    
    # 显示有结果标记的用例
    print("\n有结果标记的用例:")
    for case in cases:
        if case.get('status'):
            print(f"  - {case['title'][:40]}: {case['status']} ({case['id'][:16]}...)")
    
    # 同步结果
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
    
    # 从XMind配置读取参数
    with zipfile.ZipFile(xmind_file, 'r') as z:
        content = json.loads(z.read('content.json'))
        
        # 查找配置sheet
        config = {}
        for sheet in content:
            sheet_name = sheet.get('title', '')
            if '配置' in sheet_name or 'Config' in sheet_name:
                root = sheet.get('rootTopic', {})
                children = root.get('children', {}).get('attached', [])
                for child in children:
                    title = child.get('title', '')
                    if '组织' in title or 'token' in title.lower():
                        notes = child.get('notes', {})
                        plain_text = notes.get('plaintext', '')
                        if plain_text:
                            if 'org' in title.lower():
                                config['org_id'] = plain_text
                            elif 'token' in title.lower():
                                config['token'] = plain_text
                            elif 'user' in title.lower() or '用户' in title:
                                config['user_id'] = plain_text
                
                # 也从children中提取
                for child in children:
                    children2 = child.get('children', {}).get('attached', [])
                    for child2 in children2:
                        title = child2.get('title', '')
                        notes = child2.get('notes', {})
                        plain_text = notes.get('plaintext', '')
                        if plain_text:
                            if 'token' in title.lower():
                                config['token'] = plain_text
    
    # 如果配置中没有，从环境变量或硬编码值
    org_id = config.get('org_id', os.environ.get('YUNXIAO_ORG_ID', '64db414e9538a17091157f29'))
    token = config.get('token', os.environ.get('YUNXIAO_TOKEN', 'pt-ytejPEd5vDj7WwRqD6Uxs95m_0a5c8d47-37bd-4561-a3e9-c3a0bc97571a'))
    user_id = config.get('user_id', os.environ.get('YUNXIAO_USER_ID', '669f49c45e4ded97ce902e11'))
    
    # 从plan URL提取plan_id
    plan_id = None
    for sheet in content:
        root = sheet.get('rootTopic', {})
        children = root.get('children', {}).get('attached', [])
        for child in children:
            title = child.get('title', '')
            if '计划' in title or 'plan' in title.lower():
                notes = child.get('notes', {})
                plain_text = notes.get('plaintext', '')
                if plain_text:
                    import re
                    match = re.search(r'/plan/([a-zA-Z0-9]+)', plain_text)
                    if match:
                        plan_id = match.group(1)
    
    if not plan_id:
        plan_id = os.environ.get('YUNXIAO_PLAN_ID', '41726a11f16f5e93cea600f656')
    
    sync_results(xmind_file, org_id, plan_id, token, user_id)


if __name__ == '__main__':
    main()
