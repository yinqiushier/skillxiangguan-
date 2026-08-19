---
name: ticket-api-tester
description: Udeer工单创建接口测试 - 支持新接口/api/v2/tickets/create和老接口/api/workItem/create的批量自动化测试，生成结构化测试报告
license: MIT
compatibility: opencode
metadata:
  version: "1.0"
  author: xianyue
  platform: Udeer Support API
---

# Udeer工单创建接口测试

## 概述

根据 CSV 测试用例批量执行工单创建接口测试，自动判断 PASS/FAIL，输出带 HTTP 状态码和响应体code的结构化报告。

也支持按 CSV 中已有成功用例作为模板创建单个工单：只覆盖 `title` 和 `description`，其他字段原样保留。适合后续生成迁移测试数据，避免误删默认负责人、参与人、研发负责人等字段。

## 前置条件

确保测试用例文件存在：
```
C:\Users\lenovo\Desktop\create接口\web\ticket_create_api_testcases.csv
```

## 使用方法

加载 skill 后，运行脚本并传入 token：

### 仅测试新接口 /api/v2/tickets/create
```bash
python3 /home/yinqiushier/.opencode/skills/ticket-api-tester/run_tests.py \
  --new-token "<你的新接口token>" \
  --only-new
```

### 测试新老两个接口
```bash
python3 /home/yinqiushier/.opencode/skills/ticket-api-tester/run_tests.py \
  --new-token "<新接口token>" \
  --old-token "<老接口token>"
```

### 指定其他环境
```bash
python3 /home/yinqiushier/.opencode/skills/ticket-api-tester/run_tests.py \
  --new-token "<token>" \
  --base-url "https://support-daily.udeer.ai" \
  --only-new
```

### 按模板创建单个工单
默认使用 CSV 第 1 行作为模板，只覆盖标题和描述：
```bash
python3 /home/yinqiushier/.opencode/skills/ticket-api-tester/run_tests.py \
  --new-token "<token>" \
  --base-url "https://support-daily.udeer.ai" \
  --create-from-template \
  --title "USPV2重复子单-待确认-测试" \
  --description "<p>USPV2重复子单待确认测试</p>"
```

指定 CSV 中某一行作为模板：
```bash
python3 /home/yinqiushier/.opencode/skills/ticket-api-tester/run_tests.py \
  --new-token "<token>" \
  --base-url "https://support-daily.udeer.ai" \
  --create-from-template \
  --template-index 1 \
  --title "USPV2普通工单-待确认" \
  --description "<p>只改标题和描述，其他字段沿用模板</p>"
```

按模板标题选择模板行：
```bash
python3 /home/yinqiushier/.opencode/skills/ticket-api-tester/run_tests.py \
  --new-token "<token>" \
  --base-url "https://support-daily.udeer.ai" \
  --create-from-template \
  --template-title "正常创建" \
  --title "USPV2普通工单-待确认" \
  --description "<p>只改标题和描述，其他字段沿用模板</p>"
```

按模板创建结果会追加到：
`C:\Users\lenovo\Desktop\create接口\web\template_create_results.csv`

注意：脚本会自动清理当前终端中的 `HTTP_PROXY/HTTPS_PROXY` 等代理环境变量，避免 daily 环境 HTTPS 握手失败。

## 测试用例说明

CSV 字段：
`title,description,type,carId,problemTime,problemDuration,ticketNumber,viewType,customerName,customerPhone,isCustomerComplaint,assignedTo,assignedRole,partner,rdAssignedList,source,priorityId,期望结果`

**期望结果规则：**
- 包含"应失败"或"失败" → 接口返回错误时为 PASS
- 其他 → 接口返回 200 且 message 含"成功"/"success"时为 PASS

## 输出

结果保存到桌面 `create接口/web/` 目录：
- `new_api_test_results.csv` - 新接口测试结果
- `old_api_test_results.csv` - 老接口测试结果
- `template_create_results.csv` - 按模板创建单个工单的结果

输出列：
| 列名 | 说明 |
|------|------|
| title | 用例标题 |
| 期望结果 | CSV中的期望结果 |
| HTTP状态码 | 实际HTTP响应码 |
| 响应体code | 响应体中的code字段 |
| 响应message | 响应消息 |
| 返回工单id | 创建的工单ID |
| 测试结果 | PASS / FAIL / ERROR |

## 文件位置

- skill: `/home/yinqiushier/.opencode/skills/ticket-api-tester/`
- 脚本: `run_tests.py`
- 测试用例: `C:\Users\lenovo\Desktop\create接口\web\ticket_create_api_testcases.csv`
- 结果输出: `C:\Users\lenovo\Desktop\create接口\web/*_api_test_results.csv`
