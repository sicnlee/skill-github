---
name: wandox-admin
description: 易仓 Wandox 管理后台。查询技能列表、剧本列表，查看技能详情和剧本内容，创建/修改/删除草稿剧本，以及测试剧本执行。当用户需要查看平台有哪些技能、剧本，了解某个技能/剧本的详细配置，创建新剧本，修改或删除已有剧本，或者测试剧本执行效果时使用。
cli_version: ">=1.0.0"
---

# Wandox 管理后台 + 剧本创作助手

连接 Wandox 管理后台 API，提供技能与剧本的查询、创建、编辑、删除和测试能力。同时内置剧本创作引导流程，帮助不懂代码的用户从业务问题出发，一步步产出可运行的草稿剧本。

## 安装

在 `mcp.json` 中添加：

```json
{
  "mcpServers": {
    "wandox-admin": {
      "type": "http",
      "url": "https://ai-api.wandox.com/mcp/platform/admin/mcp/"
    }
  }
}
```

## 首次使用

1. 调用 `auth_login` → 返回授权链接
2. 在浏览器中打开链接 → 登录管理后台 → 点击"确认授权"
3. 调用 `auth_poll` 传入 device_code → 授权成功
4. 之后所有工具即可正常使用（Token 有效期 8 小时，过期自动刷新）

---

## 工具清单（17 个）

### 认证（3 个）
| 工具 | 用途 |
|------|------|
| `auth_login` | 获取设备码和授权链接 |
| `auth_poll` | 轮询获取访问令牌 |
| `auth_status` | 查询当前认证状态 |

### 技能（3 个）
| 工具 | 用途 |
|------|------|
| `list_skills` | 查询技能列表（支持关键词/分类筛选） |
| `get_skill_detail` | 查看技能详情（参数 schema、输出字段） |
| `list_skill_categories` | 查询技能分类列表 |

### 剧本查询（5 个）
| 工具 | 用途 |
|------|------|
| `list_playbooks` | 查询剧本列表（支持类型/状态/分类/关键词筛选） |
| `get_playbook_detail` | 查看剧本详情（含完整 YAML 配置） |
| `list_playbook_types` | 查询剧本类型列表 |
| `list_playbook_categories` | 查询剧本分类列表 |
| `get_playbook_spec` | 获取剧本 YAML 编写规范 |

### 剧本管理（5 个）
| 工具 | 用途 | 限制 |
|------|------|------|
| `create_draft_playbook` | 创建草稿剧本 | 不支持 exploration/topa |
| `validate_playbook_yaml` | 验证 YAML 格式 | 创建/修改前校验 |
| `update_playbook` | 修改草稿剧本 | 仅自己创建 + draft 状态 |
| `delete_playbook` | 删除草稿剧本 | 仅自己创建 + draft 状态，不可恢复 |
| `test_playbook_steps` | 测试剧本步骤执行 | 支持变量引用和步骤间数据传递 |

### 权限管理（3 个）
| 工具 | 用途 |
|------|------|
| `grant_playbook_permission` | 授权公司/用户访问指定剧本（scope=company/user 时必须） |
| `revoke_playbook_permission` | 撤销公司/用户的访问权限 |
| `list_playbook_permissions` | 查看剧本当前的权限配置列表 |

### 剧本创作指南（1 个）
| 工具 | 用途 |
|------|------|
| `get_authoring_guide` | 获取指定域的剧本创作指南（术语、工程事实、红线、Prompt 提示等） |

---

## 使用规则

- **Domain 必须明确**：技能和剧本按业务域隔离（maiduo / yunduo / eccang），查询和操作时必须指定 domain
- **域间严格隔离**：不同域的技能和剧本完全独立，不能跨域复用
- **ID 不可编造**：skill_id / playbook_id 必须从列表结果中获取
- **先列表后详情**：查看详情前先确认目标存在
- **只改自己的草稿**：修改和删除仅限自己创建的 draft 状态剧本
- **删除不可恢复**：删除操作是永久的，务必确认后再执行
- **测试后发布**：新创建或修改的剧本建议先测试再发布
- **不支持 exploration/topa**：创建和修改不支持探索剧本和智能体循环类型

---

## 剧本创作黄金路径

当用户想**创建新剧本**时，按以下流程引导。`get_authoring_guide(domain)` 返回的 JSON 包含以下字段，各步骤按需使用：

| 字段 | 用途 | 使用时机 |
|------|------|----------|
| `user_profile` | 服务对象画像（典型用户、语言、痛点） | 理解用户背景 |
| `terminology` | 业务术语表 | 用户问什么是 X 时直接讲 |
| `step_minus1_guide` | Step -1 引导（必做事项、子系统提示、追问话术） | Step -1 |
| `step0_categories` | 业务问题类别选项 | Step 0 |
| `step0_granularity` | 颗粒度选项 | Step 0 |
| `engineering_facts` | 域工程事实（技术限制 + 务实策略） | Step 2/4 |
| `prompt_tips` | Prompt 写作提示 | Step 4 |
| `calculator_template` | direct-calculator 标准写法（仅 yunduo） | Step 4 |
| `scope_rules` | scope 选择规则 | Step 5 |
| `redlines` | 红线规则 | 全程 |
| `examples` | 典型对话样例（完整 Step 0-7 演练） | 参考学习 |
| `missing_capability_template` | 缺能力时的处理话术（仅 yunduo） | Step -1 发现盖不住时 |
| `closing_template` | 收尾话术模板 | Step 7 |

---

### Step -1：调研版图

**必须先跑**，不可跳过。

1. 调用 `get_authoring_guide(domain)` 获取该域的完整创作指南
2. 阅读 `step_minus1_guide` 字段，了解该域的必做事项和子系统提示
3. 调用 `list_skills(domain, page_size=50)` 拉全量技能列表
4. 调用 `list_playbooks(domain, type="standard", status="published")` 拉已发布样板
5. 用 `step_minus1_guide.ask_template` 向用户追问子系统范围
6. 如果调研发现用户诉求**明显盖不住**（技能不存在），参考 `missing_capability_template`（如有）告知用户

### Step 0：确认需求（一次问两件事）

根据 `step0_categories` 和 `step0_granularity`，问用户：

1. **业务问题类别**：你想解决什么问题？（给出该域的选项列表，参考 triggers 匹配用户原话）
2. **颗粒度**：每次跑剧本时的数据范围？（给出该域的选项列表）

收齐后复述确认：
> 我理解你想要：在 **{domain}** 创建一个 **{类别}** 剧本，颗粒度是 **{颗粒度}**。对吗？

用户没明确 OK **不进 Step 1**。

**高风险类别防呆**：如果用户选了"自动化执行"或"自动化处置"类别，必须先提醒写动作风险，建议先做 standard 版本（只看不做），用户确认后再做 action 版。参考 `examples` 中的高风险样例。

### Step 1：选样板

从 Step -1 拉到的已发布剧本中，推荐最接近的 1-2 个作为参考样板。告诉用户：
- 样板名称和大致结构（几步、做什么）
- 我会参考它但会根据你的需求简化/调整

参考 `examples` 中的样例了解推荐话术风格。

### Step 2：确认技能

1. 根据业务需求，从 `list_skills` 结果中找相关技能
2. **必须** `get_skill_detail` 验证技能的真实入参和输出字段
3. 不要凭印象假设技能参数——以 `get_skill_detail` 返回为准
4. 参考 `engineering_facts` 了解该域的技术限制（如 eccang 没有 direct-calculator）

### Step 3：方案确认

向用户讲清楚：
- 剧本几步、每步做什么
- 需要用户填什么参数（params）
- 有什么限制或取舍（参考 `engineering_facts` 中的务实策略）

用户确认后进入起草。

### Step 4：起草 YAML

1. 调用 `get_playbook_spec()` 获取 YAML 规范
2. 参考 `engineering_facts` 决定剧本骨架（如 maiduo/yunduo 用三段式，eccang 用 2 步）
3. 参考 `prompt_tips` 写 AI 步骤的 prompt（注意域特有要求）
4. 如果是 yunduo 且需要 calculator，参考 `calculator_template` 照抄写法
5. **Prompt 自检**：
   - P0（必须）：有没有幻觉风险？字段对照表列了吗？输出格式明确吗？客户隔离做了吗（yunduo）？
   - P1（应该）：角色设定合理吗？边界情况处理了吗？中英文字段对照列了吗（eccang）？
   - P2（建议）：输出是否对用户友好？主管类输出有没有具体到人+卡点（eccang）？

### Step 5：创建

1. `validate_playbook_yaml(yaml_content)` — 校验格式
2. `create_draft_playbook(...)` — 创建草稿
3. scope 和权限：读取 `get_authoring_guide` 返回的 `scope_rules` 字段，按其中的 `rule` 指示操作

### Step 6：测试

1. `test_playbook_steps(...)` — 用真实或 mock 参数跑一遍
2. 检查每步的 success/error/data
3. **特别注意**：如果数据字段跟预期不一致（如中文 vs 英文枚举），回 Step 4 修 prompt 的字段对照表
4. 建议先只跑 step1 看真实数据格式，再跑完整流程

### Step 7：收尾

参考 `closing_template`，告知用户：
- 剧本 ID 和状态
- 后续可做的操作（运行/修改/分享/删除）
- **不替用户发布**

---

## 通用红线

- **scope 和权限**：按 `get_authoring_guide` 返回的 `scope_rules.rule` 操作
- **action 类剧本有写动作风险**：创建前必须用户明确知道会做什么写操作 + 作用范围 + 不可撤销性。建议先做 standard 版本（只看不做），确认后再做 action 版
- **patrol 类剧本是定时跑的**：用户没说"我要定时"，默认创 standard（手动跑）
- **域特有红线**：参考 `redlines` 字段，每个域有额外的安全约束
- **不要凭印象假设技能参数**：必须 `get_skill_detail` 验真，实际字段可能跟想象不同
- **测试时先跑 step1 看真实数据**：字段名、枚举值可能跟文档不一致（如中文 vs 英文），看到真实数据再写 prompt
- **缺能力时不要硬上**：如果 Step -1 调研发现技能不存在，告知用户并给出替代方案，不要硬写一个调不到数据的剧本

---

## 典型用法

### 查询技能和剧本

```
用户：查看麦多有哪些技能
AI  → list_skills(domain="maiduo")

用户：运多有哪些已发布的标准剧本
AI  → list_playbooks(domain="yunduo", type="standard", status="published")
```

### 创建剧本（完整流程）

```
用户：帮我创建一个看销量下跌的剧本

AI  → get_authoring_guide(domain="maiduo")           # Step -1: 获取创作指南
AI  → list_skills(domain="maiduo", page_size=50)     # Step -1: 拉技能版图
AI  → list_playbooks(domain="maiduo", type="standard", status="published")  # Step -1: 拉样板

AI  → 问用户 Step 0 问题（类别 + 颗粒度）
AI  → 复述确认

AI  → get_skill_detail(skill_id="xxx", domain="maiduo")  # Step 2: 验证技能
AI  → 跟用户确认方案                                       # Step 3

AI  → get_playbook_spec()                                 # Step 4: 获取 YAML 规范
AI  → 起草 YAML + Prompt 自检

AI  → validate_playbook_yaml(yaml_content="...")          # Step 5: 校验
AI  → create_draft_playbook(...)                          # Step 5: 创建

AI  → test_playbook_steps(...)                            # Step 6: 测试
AI  → 收尾告知                                             # Step 7
```

### 修改和删除剧本

```
用户：帮我修改这个剧本的名称
AI  → update_playbook(playbook_id="xxx", domain="maiduo", name="新名称")

用户：把这个草稿删掉
AI  → delete_playbook(playbook_id="xxx", domain="maiduo")
```

---

## 架构说明

```
┌─────────────────────────────────────────────┐
│  AI 客户端（Kiro / Cursor / Claude 等）      │
└──────────────────┬──────────────────────────┘
                   │ MCP 协议（HTTP）
┌──────────────────▼──────────────────────────┐
│  MCP Server（部署在 Wandox 服务器）          │
│  ├── tools: 17 个                           │
│  │   ├── 查询 + 创建 + 编辑 + 删除 + 测试  │
│  │   └── get_authoring_guide（动态创作指南） │
│  ├── prompts: 使用规则动态下发              │
│  ├── authoring_guides/: 各域 YAML 配置文件  │
│  └── auth: 设备流登录 + Token 自动刷新      │
└──────────────────┬──────────────────────────┘
                   │ 内部调用
┌──────────────────▼──────────────────────────┐
│  Wandox Admin API                           │
│  /api/v1/admin-panel/*                      │
└─────────────────────────────────────────────┘
```

动态内容（术语表、工程事实、红线、Prompt 提示等）存储在服务端 `authoring_guides/*.yaml`，平台可随时更新，无需重新发布 skill。
