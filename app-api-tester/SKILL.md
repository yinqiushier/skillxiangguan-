---
name: app-api-tester
description: APP端工单创建接口测试 - 支持新老接口对比、自动化测试、安全测试、测试报告生成
license: MIT
compatibility: opencode
metadata:
  version: "1.1"
  author: opencode
  platform: Alibaba Cloud
---

# APP工单接口测试 Skill

## 功能概述

自动化测试 APP 端工单创建接口，支持：
- 新老接口对比测试
- 安全专项测试（SQL注入、XSS、重放、未授权等）
- 自动化用例生成
- 详细测试报告

## 文件结构

```
app-api-tester/
├── SKILL.md           # 本说明文件
├── config.json        # 配置文件（token、URL等）
├── run_tests.py       # 运行所有测试用例
├── gen_report.py       # 生成对比报告
├── get_details.py      # 获取工单详情对比
└── test_security.py    # 安全专项测试
```

## 使用方法

### 1. 配置
编辑 `config.json` 设置：
- `token`: API Token
- `work_dir`: 工作目录
- `old_api_url`: 老接口地址
- `new_api_url`: 新接口地址

### 2. 运行测试
```bash
python3 run_tests.py
```

### 3. 生成报告
```bash
python3 gen_report.py
```

### 4. 安全测试
```bash
python3 test_security.py
```

## 测试用例格式

CSV文件（15列）：
```
测试用例名称,ticketNumber,source,type,title,description,problemDuration,problemTime,carId,viewType,customerName,customerPhone,phonePrefix,attachment,期望结果
```

## 安全测试用例

| 用例 | 说明 |
|------|------|
| SQL注入 | 测试'; DROP TABLE等 |
| XSS | 测试<script>等 |
| 重放攻击 | 重复提交 |
| 未授权访问 | 无token访问 |
| 超大负载 | 超出限制的数据 |

## 注意事项

1. Token 需保持有效，过期需更新
2. 运行前确保网络通畅
3. 安全测试会创建测试数据，请定期清理