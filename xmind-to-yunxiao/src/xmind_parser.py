#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XMind测试用例解析工具 V5
将XMind文件解析为标准JSON格式

使用方法:
    命令行: python3 xmind_parser.py <xmind文件1> [xmind文件2...]
    模块: from xmind_parser import parse_xmind; data = parse_xmind('file.xmind')
"""

import zipfile
import json
import sys
import re
import os
from typing import List, Dict, Any, Set, Optional, Tuple


def get_title(node: Dict) -> str:
    """获取节点标题"""
    return node.get('title', '').strip()


def get_markers(node: Dict) -> List[str]:
    """获取节点的markers"""
    markers = []
    if 'markers' in node:
        for marker in node['markers']:
            marker_id = marker.get('markerId', '')
            markers.append(marker_id)
    return markers


def get_labels(node: Dict) -> List[str]:
    """获取节点的labels"""
    return node.get('labels', [])


def has_marker(node: Dict, marker_id: str) -> bool:
    """检查节点是否有指定的marker"""
    return marker_id in get_markers(node)


def get_priority(node: Dict) -> str:
    """从markers中提取优先级"""
    markers = get_markers(node)
    if 'priority-1' in markers:
        return 'P0'
    elif 'priority-2' in markers:
        return 'P1'
    elif 'priority-3' in markers:
        return 'P2'
    elif 'priority-4' in markers:
        return 'P3'
    return 'P2'


def get_test_results_from_markers(node: Dict) -> List[str]:
    """从标签类markers获取测试结果"""
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


def collect_all_test_results(node: Dict) -> List[str]:
    """递归收集节点及其所有子节点的测试结果"""
    results = []
    node_results = get_test_results_from_markers(node)
    results.extend(node_results)
    children = node.get('children', {}).get('attached', [])
    for child in children:
        child_results = collect_all_test_results(child)
        results.extend(child_results)
    return results


def get_case_id_from_labels(node: Dict) -> Optional[str]:
    """从labels中提取用例ID"""
    labels = get_labels(node)
    for label in labels:
        if not label.startswith('http'):
            return label
    return None


def is_testcase_like(node: Dict) -> bool:
    """判断节点是否看起来像测试用例"""
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
    """解析单个步骤及其嵌套子步骤"""
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
        is_generate_keyword = any(keyword in child_title for keyword in ['生成', '创建'])
        has_result_marker = any(tag in ['tag-green', 'tag-red', 'tag-orange', 'tag-grey'] for tag in child_markers)
        
        is_step = has_priority_marker or is_step_keyword or (is_generate_keyword and has_priority_marker)
        
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
    
    # 单步骤用例：只有1个子节点，title作为步骤
    if len(children) == 1:
        step_content = case_title
        expected_node = children[0]
        expected_result = get_title(expected_node)
        
        step_results = []
        expected_results = get_test_results_from_markers(expected_node)
        if expected_results:
            step_results.extend(expected_results)
        
        result_nodes = expected_node.get('children', {}).get('attached', [])
        for result_node in result_nodes:
            node_results = collect_all_test_results(result_node)
            step_results.extend(node_results)
        
        steps.append({
            'step': step_content,
            'expected': expected_result,
            'result': step_results if step_results else []
        })
    elif len(children) >= 2 and not has_c_symbol_pen:
        # 没有c_symbol_pen且有2+子节点
        case_step1_node = children[-1]
        case_step1_title = get_title(case_step1_node)
        
        step1_results = []
        step1_expected_results = get_test_results_from_markers(case_step1_node)
        if step1_expected_results:
            step1_results.extend(step1_expected_results)
        result_nodes = case_step1_node.get('children', {}).get('attached', [])
        for result_node in result_nodes:
            node_results = collect_all_test_results(result_node)
            step1_results.extend(node_results)
        
        steps.append({
            'step': "case步骤1",
            'expected': case_step1_title,
            'result': step1_results if step1_results else []
        })
        
        for step_node in children[:-1]:
            nested_steps = parse_single_step(step_node, "")
            steps.extend(nested_steps)
    else:
        # 多步骤用例
        first_child = children[0]
        first_child_title = get_title(first_child)
        first_child_markers = get_markers(first_child)
        
        has_priority = 'priority-1' in first_child_markers or 'priority-2' in first_child_markers or 'c_symbol_pen' in first_child_markers
        step_keywords = ['步骤', '操作', '输入', '点击', '选择', '填写', '提交']
        is_step_keyword = any(keyword in first_child_title for keyword in step_keywords)
        is_generate_keyword = any(keyword in first_child_title for keyword in ['生成', '创建'])
        
        is_first_step = has_priority or is_step_keyword or (is_generate_keyword and has_priority)
        
        if not is_first_step:
            step_content = case_title
            expected_node = first_child
            expected_result = get_title(expected_node)
            
            first_step_results = []
            expected_results = get_test_results_from_markers(expected_node)
            if expected_results:
                first_step_results.extend(expected_results)
            
            result_nodes = expected_node.get('children', {}).get('attached', [])
            for result_node in result_nodes:
                node_results = collect_all_test_results(result_node)
                first_step_results.extend(node_results)
            
            steps.append({
                'step': step_content,
                'expected': expected_result,
                'result': first_step_results if first_step_results else []
            })
            
            for step_node in children[1:]:
                nested_steps = parse_single_step(step_node, "")
                steps.extend(nested_steps)
        else:
            for step_node in children:
                nested_steps = parse_single_step(step_node, "")
                steps.extend(nested_steps)
    
    # 计算整体测试结果
    overall_result = None
    has_failed = False
    has_empty_result = False
    
    for step in steps:
        results = step['result']
        if 'FAILED' in results or 'BLOCKED' in results:
            has_failed = True
        if not results:
            has_empty_result = True
    
    if has_failed:
        overall_result = "FAILED"
    elif has_empty_result:
        overall_result = None
    else:
        for step in reversed(steps):
            if step['result']:
                overall_result = step['result'][-1]
                break
    
    return steps, overall_result


def extract_requirement_info(node: Dict, title: str) -> Tuple[str, str, str]:
    """从需求节点中提取需求ID、名称和URL"""
    labels = get_labels(node)
    req_url = None
    req_id = ""
    
    for label in labels:
        if label.startswith('http'):
            req_url = label
            req_id_match = re.search(r'/req/([A-Z]+-\d+)', label)
            if req_id_match:
                req_id = req_id_match.group(1)
            break
    
    if not req_url:
        req_id_match = re.search(r'([A-Z]+-\d+)', title)
        req_id = req_id_match.group(1) if req_id_match else ""
        
        if req_id:
            req_url = f"https://devops.aliyun.com/projex/req/{req_id}# 《{title}》"
        else:
            req_url = f"https://devops.aliyun.com/projex/req/UNKNOWN# 《{title}》"
    
    req_name = title
    return req_id, req_name, req_url


def parse_tree(node: Dict, path: List[str], current_requirement: Optional[Dict],
               prerequisites: List[str], found_star_red: bool,
               all_requirements: List[Dict], case_ids: Set[str], verbose: bool = False) -> None:
    """递归解析XMind树结构"""
    title = get_title(node)
    children = node.get('children', {}).get('attached', [])
    markers = get_markers(node)
    
    if has_marker(node, 'star-red'):
        req_id, req_name, req_url = extract_requirement_info(node, title)
        new_requirement = {
            'requirement_name': req_name,
            'requirement_url': req_url,
            'case_list': []
        }
        
        for child in children:
            parse_tree(child, [], new_requirement, [], True, all_requirements, case_ids, verbose)
        
        if new_requirement['case_list']:
            all_requirements.append(new_requirement)
        
        return
    
    if is_testcase_like(node):
        if current_requirement is None:
            if verbose:
                print(f"  ⚠ 警告: 用例 '{title}' 没有关联需求，跳过")
            return
        
        case_id = get_case_id_from_labels(node)
        
        if case_id and case_id in case_ids:
            if verbose:
                print(f"  ⚠ 跳过重复用例: {title} (ID: {case_id})")
            return
        
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
    
    if 'symbol-pin' in markers or 'pushpin-red' in markers:
        new_path = path + [title] if title else path
        for child in children:
            parse_tree(child, new_path, current_requirement, prerequisites, found_star_red, all_requirements, case_ids, verbose)
        return
    
    if found_star_red and current_requirement:
        has_testcase_child = any(is_testcase_like(child) for child in children)
        
        if has_testcase_child:
            new_prerequisites = prerequisites + [title] if title else prerequisites
            for child in children:
                parse_tree(child, path, current_requirement, new_prerequisites, found_star_red, all_requirements, case_ids, verbose)
        else:
            new_prerequisites = prerequisites + [title] if title else prerequisites
            for child in children:
                parse_tree(child, path, current_requirement, new_prerequisites, found_star_red, all_requirements, case_ids, verbose)
        return
    
    for child in children:
        parse_tree(child, path, current_requirement, prerequisites, found_star_red, all_requirements, case_ids, verbose)


def parse_config_xmind(root_topic: Dict) -> Dict[str, str]:
    """解析配置类型的XMind节点"""
    config = {
        "plan": "",
        "repo": "",
        "token": "",
        "organization_id": ""
    }
    
    children = root_topic.get('children', {}).get('attached', [])
    
    for child in children:
        title = get_title(child).strip()
        child_children = child.get('children', {}).get('attached', [])
        
        if not child_children:
            continue
        
        value = get_title(child_children[0]).strip()
        
        if '测试计划' in title or 'plan' in title.lower():
            config['plan'] = value
        elif '用例库' in title or 'repo' in title.lower() or '库' in title:
            config['repo'] = value
        elif '令牌' in title or 'token' in title.lower():
            config['token'] = value
        elif '组织' in title or 'organization' in title.lower() or 'org' in title.lower():
            config['organization_id'] = value
    
    return config


def is_config_sheet(root_topic: Dict) -> bool:
    """判断sheet是否为配置sheet"""
    title = get_title(root_topic)
    
    if '配置' in title or 'config' in title.lower():
        return True
    
    children = root_topic.get('children', {}).get('attached', [])
    config_keywords = ['测试计划', '用例库', '令牌', 'token', '组织', 'organization', 'plan', 'repo']
    
    for child in children:
        child_title = get_title(child).lower()
        if any(keyword.lower() in child_title for keyword in config_keywords):
            return True
    
    return False


def parse_xmind(filename: str, verbose: bool = False) -> Tuple[Dict[str, str], List[Dict]]:
    """
    解析XMind文件（支持多sheet）
    
    Args:
        filename: XMind文件路径
        verbose: 是否输出详细日志
    
    Returns:
        (config, requirements) - 配置字典和需求列表
    """
    with zipfile.ZipFile(filename, 'r') as z:
        content_json = z.read('content.json').decode('utf-8')
    
    xmind_data = json.loads(content_json)
    
    config = {
        "plan": "",
        "repo": "",
        "token": "",
        "organization_id": ""
    }
    all_requirements = []
    case_ids = set()
    
    if verbose:
        print(f"文件包含 {len(xmind_data)} 个sheet")
    
    for i, sheet in enumerate(xmind_data, 1):
        root_topic = sheet['rootTopic']
        root_title = get_title(root_topic)
        
        if verbose:
            print(f"  Sheet #{i}: {root_title}")
        
        if is_config_sheet(root_topic):
            if verbose:
                print(f"    -> 配置sheet")
            sheet_config = parse_config_xmind(root_topic)
            for key, value in sheet_config.items():
                if value:
                    config[key] = value
        else:
            if verbose:
                print(f"    -> 测试用例sheet")
            children = root_topic.get('children', {}).get('attached', [])
            
            for child in children:
                parse_tree(child, [], None, [], False, all_requirements, case_ids, verbose)
    
    return config, all_requirements


def parse_xmind_to_dict(filename: str, verbose: bool = False) -> Dict[str, Any]:
    """
    解析XMind文件，返回标准dict格式
    
    Args:
        filename: XMind文件路径
        verbose: 是否输出详细日志
    
    Returns:
        {"config": {...}, "cases": [...]} - 标准JSON格式
    """
    config, requirements = parse_xmind(filename, verbose)
    
    return {
        "config": config,
        "cases": requirements
    }


def print_summary(data: Dict[str, Any]) -> None:
    """打印解析结果摘要"""
    print("\n" + "="*80)
    print("解析完成!")
    print("="*80)
    
    if data.get('config'):
        print("\n配置信息:")
        print(json.dumps(data['config'], ensure_ascii=False, indent=2))
    
    total_cases = sum(len(req['case_list']) for req in data.get('cases', []))
    print(f"\n总需求数: {len(data.get('cases', []))}")
    print(f"总用例数: {total_cases}")
    
    if data.get('cases'):
        print("\n" + "="*80)
        print("用例预览:")
        print("="*80)
        for req in data['cases']:
            print(f"\n需求: {req['requirement_name']}")
            for i, case in enumerate(req['case_list'], 1):
                steps_preview = ", ".join([s['step'] for s in case['steps'][:3]])
                if len(case['steps']) > 3:
                    steps_preview += "..."
                print(f"  {i}. {case['title']}")
                print(f"     优先级: {case['priority']}, 结果: {case['test_result'] or '未执行'}")
                print(f"     步骤: {steps_preview}")


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("XMind测试用例解析工具 V5")
        print("")
        print("用法:")
        print("  python3 xmind_parser.py <xmind文件1> [xmind文件2...] [-o 输出文件]")
        print("")
        print("示例:")
        print("  python3 xmind_parser.py demo.xmind")
        print("  python3 xmind_parser.py demo.xmind -o result.json")
        print("  python3 xmind_parser.py demo1.xmind demo2.xmind -o result.json")
        print("")
        print("作为模块使用:")
        print("  from xmind_parser import parse_xmind_to_dict")
        print("  data = parse_xmind_to_dict('demo.xmind')")
        sys.exit(1)
    
    output_file = None
    input_files = []
    
    for arg in sys.argv[1:]:
        if arg == '-o' or arg == '--output':
            continue
        elif arg.endswith('.xmind') or arg.endswith('.xmind'):
            input_files.append(arg)
        elif output_file is None and (arg.endswith('.json') or arg == '-o'):
            if arg != '-o':
                output_file = arg
    
    if len(sys.argv) > 2:
        for i, arg in enumerate(sys.argv):
            if arg == '-o' and i + 1 < len(sys.argv):
                output_file = sys.argv[i + 1]
    
    if not input_files:
        print("错误: 请指定至少一个XMind文件")
        sys.exit(1)
    
    final_config = {
        "plan": "",
        "repo": "",
        "token": "",
        "organization_id": ""
    }
    all_requirements = []
    
    print("\n" + "="*80)
    print("开始解析XMind文件...")
    print("="*80 + "\n")
    
    for filename in input_files:
        if not os.path.exists(filename):
            print(f"⚠ 文件不存在: {filename}")
            continue
        
        print(f"\n处理文件: {filename}")
        print("-" * 80)
        
        config, requirements = parse_xmind(filename, verbose=True)
        
        for key, value in config.items():
            if value:
                final_config[key] = value
        
        all_requirements.extend(requirements)
        
        total_cases = sum(len(req['case_list']) for req in requirements)
        print(f"  ✓ 需求数: {len(requirements)}")
        print(f"  ✓ 用例数: {total_cases}")
    
    result = {
        "config": final_config,
        "cases": all_requirements
    }
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"\n结果已保存到: {output_file}")
    
    print_summary(result)


if __name__ == '__main__':
    main()
