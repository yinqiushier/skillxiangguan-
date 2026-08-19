---
name: support-ticket-create
description: Udeer Support daily 工单创建接口单条请求工具 - 根据浏览器 curl 复现 /api/v2/tickets/create，支持 token 参数化、payload 覆盖和响应检查
license: MIT
compatibility: opencode
metadata:
  version: "1.0"
  author: opencode
  platform: Udeer Support Daily
---

# Udeer Support 工单创建

## 功能

根据浏览器抓到的 `curl` 复现 daily 环境工单创建接口：

`POST https://support-daily.udeer.ai/api/v2/tickets/create`

默认 payload 来源于用户提供的请求，但脚本会默认生成新的 `ticketNumber`，避免重复提交同一个单号。

## 文件

- `SKILL.md` - 使用说明
- `create_ticket.py` - 单条工单创建脚本

## 使用

推荐通过环境变量传 token，避免命令历史里长期保留 token：

```bash
export UDEER_SUPPORT_TOKEN='<Bearer token 或裸 token>'
python3 /home/yinqiushier/.opencode/skills/support-ticket-create/create_ticket.py
```

也可以直接传参：

```bash
python3 /home/yinqiushier/.opencode/skills/support-ticket-create/create_ticket.py \
  --token '<Bearer token 或裸 token>'
```

覆盖常用字段：

```bash
python3 /home/yinqiushier/.opencode/skills/support-ticket-create/create_ticket.py \
  --title '自动化测试' \
  --car-id 'E1024A' \
  --customer-name 'test' \
  --problem-time '2026-05-14 10:36:10'
```

只查看将要发送的请求，不真正提交：

```bash
python3 /home/yinqiushier/.opencode/skills/support-ticket-create/create_ticket.py --dry-run
```

## Token 规则

脚本按以下顺序取 token：

1. `--token`
2. 环境变量 `UDEER_SUPPORT_TOKEN`

如果 token 失效、缺失或接口返回 401/403，需要向用户索要新的 `authorization` token。

## 默认 Payload

默认字段：

```json
{
  "title": "自动化测试",
  "description": "<p>自动化测试</p>",
  "type": "异常排查",
  "carId": "E1024A",
  "problemDuration": "less_than_3_minutes",
  "viewType": "1",
  "assignedTo": "0",
  "priorityId": 1,
  "moduleTags": [],
  "isCustomerComplaint": false,
  "customerName": "test",
  "statusId": 11,
  "assignedRole": "PAE"
}
```

`ticketNumber` 默认自动生成 UUID，`problemTime` 默认使用当前时间。

## 判断结果

- HTTP 2xx 且响应 JSON 中 `code` 为 `0`、`200`、`"0"`、`"200"` 或 `message` 包含成功时，视为创建成功。
- HTTP 401/403 时，先判断 token 失效，向用户索要新 token 后重试。
- 其他错误输出 HTTP 状态码、响应 `code`、`message` 和响应体摘要。
