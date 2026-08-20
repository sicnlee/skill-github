---
name: get-weather
description: 查询指定城市的实时天气信息，包括温度、天气状况和湿度。当用户询问天气、气温、下雨、晴天等与天气相关的问题时使用此技能。从用户输入中提取城市名称，调用 wttr.in 接口获取数据，并以标准格式返回中文天气摘要。
metadata:
  author: yuanyuan
  version: "1.0"
allowed-tools: fetch_url
---

## 天气查询技能

当用户询问某地天气时，按以下步骤执行。

### 步骤

1. **提取城市名称**：从用户输入中识别目标城市（支持中文城市名，如"北京"、"上海"；也支持英文，如"Beijing"）。

2. **调用天气接口**：使用 `fetch_url` 工具请求以下 URL（将 `{city}` 替换为实际城市名）：

   ```
   fetch_url("https://wttr.in/{city}?format=j1&lang=zh")
   ```

   接口配置详见 [assets/config.json](assets/config.json)。

3. **解析返回数据**：从返回的 JSON 中提取以下字段：
   - `current_condition[0].temp_C` — 当前温度（摄氏度）
   - `current_condition[0].weatherDesc[0].value` — 天气状况描述
   - `current_condition[0].humidity` — 湿度百分比

4. **格式化输出**：按照 [references/OUTPUT_TEMPLATE.md](references/OUTPUT_TEMPLATE.md) 中定义的模板组织返回内容，以简洁的中文天气摘要回复用户。

### 常见边界情况

- **城市识别失败**：若无法从用户输入中提取城市，请询问用户"请问您想查询哪个城市的天气？"
- **接口返回错误**：若 HTTP 状态码非 200 或返回内容为空，告知用户"暂时无法获取该城市的天气信息，请稍后重试。"
- **城市名含空格**（如"New York"）：替换为 `+` 后再拼接 URL，例如 `https://wttr.in/New+York?format=j1&lang=zh`。
- **中文城市名**：直接使用中文拼接 URL，wttr.in 支持中文地名解析。
