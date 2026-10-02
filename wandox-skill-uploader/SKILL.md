---
name: "wandox-skill-uploader"
description: "从 YApi 接口文档批量导入并创建 Wandox 技能。当用户提供 YApi 接口链接并要求上传技能到 Wandox 平台时使用此技能。此技能适用于用户提供 YApi 链接 + domain/category/adapter_type/ui_hint 参数的场景。"
agent_created: true
---

# Wandox 技能批量上传

从 YApi 接口文档批量导入、创建并启用 Wandox 技能的标准工作流。

## 前置条件

1. wandox MCP 已配置并连接（`~/.workbuddy/mcp.json` 中有 wandox 条目）
2. 已完成钉钉授权登录（首次使用时走 auth_login → auth_poll 流程）

## 核心流程

用户提供 YApi 链接时，提取 `interface_id`（URL 中 `/api/` 后的数字部分），按以下步骤执行：

### Step 0：授权登录

1. 检查 `~/.wandox/mcp_auth_token.json` 是否存在
2. 存在 → 调 `auth_status(auth_token=...)` 验证有效性
   - **注意 token 文件有两种格式**：旧格式 `{"auth_token": "eyJ..."}`（JWT，有效期约 8 小时）；新格式 `{"user_token": "...", "admin_token": "..."}`（长效）。新格式请取 **`admin_token`** 传入，user_token 权限不足
3. 不存在或失效 → 调 `auth_login` → 引导用户浏览器授权 → `auth_poll(device_code)` → 保存 token 到 `~/.wandox/mcp_auth_token.json`
4. **MCP 工具命名空间有两种**：`mcp__wandox__*` 与 `mcp__wandox-admin__*`（功能相同）。用 ToolSearch 查不到前者时改用后者

### Step 1：导入预览（可选，用于核对）

调用 `import_skills_from_yapi` 获取 YApi 接口定义预览：

```
interface_ids: [127916]       # 注意是整数数组，不是字符串
domain: 用户指定的 domain（默认 maiduo）
system_code: 用户指定的 category（默认 MFC）
auth_token: 从 Step 0 获取
```

预览返回 skill_spec（含 skill_id、name、params_schema、response_schema 等），可用于与用户确认。

### Step 2：检查是否已存在

调用 `get_skill_detail` 检查技能是否已存在：

```
skill_id: 从预览结果获取（如 MFC.wechat.login）
domain: 用户指定的 domain
auth_token: ...
```

- **不存在（404）** → 走「一键导入」流程（Step 3a）
- **存在** → 走「更新」流程（Step 3b）

### Step 3a：一键导入创建（推荐）

调用 `import_interface_to_system` 一步到位，自动完成 YApi 解析 → 创建能力 → 字段映射 → 设置 ui_hint/category → 启用：

```
domain: maiduo
connector_code: MFC              # 系统编码，同 system_code
interface_id: 127916             # YApi 接口 ID（整数）
system_code: MFC                 # 默认同 connector_code
ui_hint: table                   # 用户指定（table/chart/form/card 等）
category: MFC                    # 用户指定
auth_token: ...
```

导入成功后技能自动处于 `active` 状态，无需手动 enable。

### Step 3b：更新已有技能

1. 调用 `update_capability` 更新字段（name/api_path/api_method/input_schema/output_schema/description）
2. 需传入 `connector_code` 和 `capability_code`（即 skill_id）
3. 更新后技能自动同步，无需手动 enable

### Step 4：验证结果

调用 `get_skill_detail` 确认技能状态为 `active`，检查 ui_hint/category/params_schema 等字段是否符合预期。

## 关键注意事项

1. **import_interface_to_system 是首选方式**：一步完成创建+字段映射+ui_hint+category+启用，无需手动 create_skill/enable_skill
2. **ui_hint 支持**：`import_interface_to_system` 直接支持 ui_hint 参数，无需后台手动设置
3. **auth_token 持久化**：首次授权后必须保存到 `~/.wandox/mcp_auth_token.json`，后续会话直接读取复用
4. **interface_ids 格式**：`import_skills_from_yapi` 的 interface_ids 是整数数组 `[127916]`，不是字符串
5. **技能自动启用**：通过 `import_interface_to_system` 创建的技能默认 status=active，无需额外启用步骤
6. **ToolSearch 工具加载**：wandox MCP 工具为 deferred tools，每次会话需先 ToolSearch 加载 schema 再调用
7. **adapter_type 映射**：用户指定 `gateway` 时，平台实际存储为 `integration_gateway`
8. **array 类型不支持嵌套字段**：`update_capability` 的 output_schema 中，array 类型的 `items.properties` 会被平台丢弃。如需展示数组内部字段，必须将所有字段打平为顶层属性（不用 array 类型）
9. **出参打平方案**：当用户需要将 records/paginator/totalData 等嵌套结构打平时：
   - 将所有子对象的字段提升为顶层属性
   - 同名字段去重（如 records 和 totalData 都有 salesAmount，只保留一个）
   - 不需要加前缀（除非用户明确要求区分来源）
   - 同时更新 `properties` 和 `x_output_fields` 两个位置
10. **output_schema 格式要求（关键！）**：
    - `properties` 中字段描述必须用 `title`（不是 `label`），否则平台会静默丢弃所有字段（update_capability 返回 success 但 response_schema 为空）
    - `x_output_fields` 必须是对象数组 `[{name, type, label}]`，不能是字符串数组 `["field1", "field2"]`
    - 正确格式示例：
      ```json
      {
        "type": "object",
        "properties": {
          "fieldName": {"type": "number", "title": "字段描述", "description": ""}
        },
        "x_output_fields": [
          {"name": "fieldName", "type": "number", "label": "字段描述", "default": "", "example": "", "required": false, "description": ""}
        ]
      }
      ```
11. **auth_token 失效处理**：会话中途 auth_token 可能失效（auth_status 返回"未登录"），此时 get_skill_detail/update_capability 都会报错。需重新 auth_login → auth_poll 获取新 token
12. **token 失效后 get_skill_detail 返回 404**：不要误以为技能被删除，先检查 auth_status，重新登录后再查
13. **description 会覆盖 title/label（关键！）**：output_schema 中 `properties[].description` 非空时，平台会用 description 值覆盖 `title` 和 `x_output_fields[].label`。例如设 title="出库成本"、description="保留3位小数"，最终平台显示 label 为"保留3位小数"而非"出库成本"。
    - **正确解法：构造 output_schema 时 description 就写与 title 完全相同的值**（description == title 时覆盖无害）。描述信息全部合并进 title。
    - **传 `description: ""` 不会清除已有值**——平台会忽略空字符串、保留原来的 description。想改必须传非空的新值。
    - YApi 自动同步的场景下，平台生成的 description 本身就等于 title，属于安全状态，无需再 update_capability 清理（清理也清不掉）。
    - 只有当发现 title 与 description 不一致时才需要修正，此时显式传入与 title 相同的 description。
14. **大 payload 处理（关键！）**：当 output_schema 超过 ~15KB（约 70+ 字段）时，DeferExecuteTool 可能无法传递完整参数。解决方案：用 Python urllib 直接调用 Wandox MCP JSON-RPC 接口
    - MCP 服务器 URL 从 `~/.workbuddy/mcp.json` 的 `mcpServers.wandox.url` 获取
    - 流程：(1) `initialize` 请求 → (2) `notifications/initialized` 通知 → (3) `tools/call` 调用
    - 用 Python 生成 output_schema JSON 文件，再读取文件内容传入 JSON-RPC 请求
    - 参考 `C:/Users/HUAWEI/.workbuddy/wandox_update.py` 和 `gen_schema.py`
    - 也可用此方法批量处理多个技能更新
15. **批量上传整个 YApi 项目**：先用 `list_yapi_interfaces(project_id=...)` 列出全部接口，再按 `_id` 升序逐个 `import_interface_to_system`。同源接口出参结构高度相似，验证过第一个后，后续同构接口（相同字段组合）可只核对 `output_count` 是否吻合，不必每个都调 get_skill_detail
16. **判断是否需要打平的决策规则（重要）**：导入后先看 `output_count` 并 `get_skill_detail` 确认有没有 array/object 类型的出参字段。YApi 常常只定义到 array/object 这一层、不写 item 结构，此时分两种情况处理：
    - **外层还有可用字段**（如币种、时间区间、汇总值）→ 这类多为图表/卡片接口，可**保持不打平**直接交付，技能仍有取值能力。典型：now/sameCompare 趋势序列、list 分布数据
    - **出参 100% 依赖嵌套**（output_count=1，整个 data 就是一个 object 或 array）→ **必须打平**，否则技能取不到任何字段。此时要向用户索要内部字段列表，**不要照接口描述硬猜字段名**
    - YApi 拿不到 item 结构时的排查顺序：`import_skills_from_yapi` 预览 → 对比同项目同源接口的出参 → curl YApi 开放 API（通常需登录会失败）。三者都无果就只能问用户
17. **同项目接口的 YApi 描述可能互相写错**：遇到 `[endpoint]` 标注与接口实际 path 不符、或描述与出参结构对不上时，以接口 `path` 字段和真实出参为准导入（导入结果不受描述影响），但要提醒用户回 YApi 修正。曾遇两个相邻接口的 endpoint 标注和图表/表格业务描述双双写反的情况
