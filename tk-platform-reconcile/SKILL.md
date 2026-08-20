---
name: tk-platform-reconcile
description: >
  TK 平台账单对账工具。用户通过对话发送 Excel 结算文件路径，
  自动与 Hologres 数据库进行对账核对，输出差异报告并回显摘要。
  触发关键词：账单对账、结算核对、对一下账、TK 对账、TikTok 账单、
  Tokopedia 账单、Excel 对比、发我 xlsx、帮我核对。
license: Proprietary
compatibility: Requires Python 3.8+, openpyxl, pg8000. Requires network access to Hologres.
metadata:
  author: settle-team
  version: "1.1"
  platform: TikTok Shop / Tokopedia
---

# TK 平台账单对账工具

## Agent 执行流程

用户通过聊天发送 Excel 文件路径后，按以下步骤执行：

### Step 1 — 获取 Excel 文件

收到用户消息后，按以下优先级逐一判断：

---

**情况 A：消息中包含文件附件（钉钉对话框直接发送文件）**

钉钉对话框发送的文件不会自动落盘到服务器，需根据平台提供的内容选择处理方式：

| 平台提供的内容 | 处理方式 |
|--------------|---------|
| 文件下载 URL | `python scripts/reconcile.py --url "<download_url>"` |
| base64 文件内容 | `python scripts/reconcile.py --base64 "<base64_string>"` |
| `downloadCode` / `mediaId` | 先调用 DingTalk API 换取下载 URL，再用 `--url` 参数 |

> 钉钉机器人消息中，文件类型消息（msgtype=file）通常携带 `downloadCode`，
> 需调用 `https://oapi.dingtalk.com/robot/message/download` 换取真实下载地址，
> 再使用 `--url` 传入脚本。

---

**情况 B：消息中包含本地文件路径**

消息中出现 `.xlsx` 或 `.xls` 路径时（文件已在服务器上）：

```bash
python scripts/reconcile.py "/path/to/TK3631.xlsx"
```

---

**情况 C：消息中既无附件也无路径**

主动回复用户：
> 请通过以下方式提供 Excel 文件：
> 1. 直接在对话框中发送文件（.xlsx）
> 2. 告诉我文件在服务器上的完整路径

---

### Step 2 — 执行对账脚本

| 场景 | 命令 |
|------|------|
| 钉钉附件（下载 URL） | `python scripts/reconcile.py --url "<url>"` |
| 钉钉附件（base64 内容） | `python scripts/reconcile.py --base64 "<base64>"` |
| 本地路径 | `python scripts/reconcile.py "<file_path>"` |
| 指定配置文件 | `python scripts/reconcile.py "<file>" --env /path/to/.env` |

> `assets/.env` 中已配置数据库连接，脚本自动读取，无需额外参数。

### Step 3 — 将结果回显给用户

脚本执行完成后，把控制台输出的对账摘要直接回复给用户，格式示例：

```
============================================================
  🎉🎊 对账结果：完全匹配！恭喜恭喜！太棒了！
============================================================
  客户代码    ：ntwfswp
  店    铺    ：SOKINTOOL3631
  平    台    ：tiktok
  账单开始时间：2026-02-01 00:00:00
  账单结束时间：2026-02-28 23:59:59
  Excel 订单总数    ：1683
  数据库订单总数    ：1683
  Excel 总结算金额  ：35068361
  数据库总结算金额  ：35068361

  ✅ 所有订单金额完美匹配，账单核对无误！
  💪 你的数据真的很干净，继续保持！加油！
============================================================
```

### Step 4 — 询问是否发送 Excel 报告

摘要回显后，询问用户：

> 是否需要将完整对账报告（Excel 文件）发送给您？
> 报告包含：对账摘要 / 差异明细 / Excel明细 / 数据库明细

---

## 对账规则

| 场景 | 处理方式 |
|------|----------|
| Excel 与 DB 金额一致 | 标记匹配 ✅ |
| Excel 金额 ≠ DB 金额 | 记录差异：`金额差异` |
| Excel 有、DB 无（金额 ≠ 0） | 记录差异：`Excel有/DB无` |
| Excel 有、DB 无（金额 = 0） | 自动补齐，标记匹配 ✅ |
| DB 有、Excel 无 | 记录差异：`DB有/Excel无` |

---

## 常见问题处理

| 问题 | 处理方式 |
|------|----------|
| 文件不存在 | 提示用户确认路径后重试 |
| 数据库连接失败 | 提示检查 `assets/.env`，确认网络可访问 Hologres |
| 未找到店铺信息 | 提示用户确认 Excel 中 orderId 是否有效 |
| Sheet 名不是 `Order details` | 提示用户确认是否为 TK 平台标准导出格式 |

---

## 数据库依赖

| 数据库 | 表 | 用途 |
|--------|----|------|
| `eccang` | `erp_eb.orders` | 获取 company_code、user_account、platform |
| `bi` | `bi_xpj_profit_settlement.xpj_ads_profit_settlement_order_detail` | 查询结算明细 |

配置文件：[assets/.env](assets/.env)

输出模板：[references/OUTPUT_TEMPLATE.md](references/OUTPUT_TEMPLATE.md)
