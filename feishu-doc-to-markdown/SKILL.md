---
name: feishu-doc-to-markdown
description: 把飞书云文档（/wiki/ 或 /docx/ 链接）抓取并导出为本地 Markdown 文档，同时下载文中的图片、视频、画板等素材到本地 assets 目录。当用户给出飞书文档链接并要求"抓一下""导出""转成 markdown""形成文档"时使用。依赖 lark-cli（飞书 connector 已连接）。
agent_created: true
metadata:
  author: workbuddy
  version: "1.0"
---

# 飞书文档 → 本地 Markdown

把一篇飞书云文档完整导出成「Markdown 正文 + 本地素材」的目录。

## 硬性前置：绕过失效代理

**这是最容易踩的坑，每次调用 `lark-cli` 都必须处理。**

当前环境的 `HTTP_PROXY=http://127.0.0.1:7897` 经常失效，直接调用会报：

```
proxyconnect tcp: dial tcp 127.0.0.1:7897: connectex: No connection could be made
```

**所有 `lark-cli` 命令都要加前缀**：

```bash
env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy -u ALL_PROXY -u all_proxy NO_PROXY="*" no_proxy="*" lark-cli ...
```

先跑一次 `lark-cli docs +fetch` 探活，报上面那个错就说明要走绕代理前缀，之后全程带上。

## 流程

### 1. 看结构

```bash
lark-cli docs +fetch --doc "<URL或token>" --scope outline --max-depth 3
```

拿到标题层级和 `document_id`、`revision_id`，同时判断文档规模。

### 2. 抓全文

```bash
lark-cli docs +fetch --doc "<URL>" --doc-format markdown --detail simple > "<工作区绝对路径>/_fetch.json"
```

- 输出是 JSON，`data.document.content` 是 markdown 正文。
- **不要用 `/tmp`**：Git Bash 的 `/tmp` 对 Windows Python 不可见，临时文件必须写到工作区绝对路径。
- **别把中间文件跨调用传递**：实测 `> _fetch.json` 重定向出来的文件在后续调用里可能是 0 字节或直接消失（同一条命令也可能被框架重复执行两次，第二次拿到空输入）。
  **推荐一条命令内用管道跑完**，不落中间文件：

```bash
env -u HTTP_PROXY ... lark-cli docs +fetch --doc "<URL>" --doc-format markdown --detail simple 2>/dev/null \
  | PYTHONIOENCODING=utf-8 <python> -c "
import sys, json
d = json.loads(sys.stdin.read())
open('<标题>.md','w',encoding='utf-8').write(d['data']['document']['content'])
"
```

- 生成脚本要写成**幂等**的：重复执行得到同样结果、不会因为中间文件已删除而崩。字符串替换要用正则而非 `str.replace`，否则双跑会把 `./assets/x.png` 越替越长成 `./assets/x/x.png`。
- 出错时看的是第二次执行的报错，不要被误导；先 `ls` 确认产物是否已经生成。

### 交付前必做：路径校验

```bash
<python> -c "
import io,os,re,glob
bad=0
for md in sorted(glob.glob('*.md')):
    t=io.open(md,encoding='utf-8').read()
    paths=re.findall(r']\(\./([^)]+)\)',t)
    miss=[p for p in paths if not os.path.exists(p)]
    print(md,'refs',len(paths),'missing',miss); bad+=len(miss)
print('TOTAL MISSING',bad)
"
```

`TOTAL MISSING` 必须是 0 才交付。

然后 `Read` 这个 `_content.md` 再人工整理成最终文档（需要转换飞书专有标签，见第 4 步）。

### 3. 下载素材

**关键：`+media-download` 常因无导出权限失败**，报：

```
current identity does not have export permission for this document media
```

**改用 `+media-preview`，它能成功下载图片和视频**：

```bash
lark-cli docs +media-preview --token "<file_token>" --output "./<目录>/assets/<名字>"
```

- 不写扩展名会自动根据 Content-Type 补全。
- **扩展名不总是 png**：同一篇文档里可能混着 `.png` 和 `.jpg`。替换正文路径时用 `glob('assets/xx/img%02d.*' % i)` 探测真实文件名，别写死 `.png`。
- 画板（`<whiteboard token="...">`）用 `+media-download --type whiteboard` 反而可以成功，导出为 jpg。

**批量下载会限流**：不加间隔地连续跑超过约 13 次会中断（命令整体 exit 1，该批后续全部不执行）。
做法是**分批，每批 5 个左右，批内 `sleep 2`**——实测 25 张图分 5 批、批内 sleep 2 全程零中断，比每批 3 个省一半调用。
素材特别多时（>30 张）再降到每批 3 个。某一批失败就单独重跑该批。

```bash
for t in "token1:name1" "token2:name2" "token3:name3"; do
  tok="${t%%:*}"; name="${t##*:}"
  env -u HTTP_PROXY ... lark-cli docs +media-preview --token "$tok" --output "./out/assets/$name"
  sleep 2
done
```

素材命名建议按出现顺序编号 + 语义后缀，如 `01-create-entry.png`、`02-data-types.png`，方便与正文对照。

**跑完必须核对**：`ls <目录> | wc -l` 对比 token 数量。实测连续跑 11 次时前 9 次成功、第 10 次静默返回空、第 11 次被跳过——所以末尾丢失是常态，把缺的那几个单独重跑一次即可补齐（重试通常一次就过），不必整批重来。

### 4. 转换飞书专有标签

| 飞书返回 | 转成 |
| --- | --- |
| `<callout emoji="✍️">…</callout>` | `> ✍️ …` 引用块（保留 emoji 和换行） |
| `<figure view-type="Preview"><source name="x.mp4" .../></figure>` | Markdown 无法内嵌视频，写成 `🎬 assets/x.mp4（原名、分辨率、大小）` |
| `<grid>` 里装的是视频 `<figure>` | 视频版分栏：`<table><tr><td>🎬 <b>原名.mp4</b><br>1080×1920 ｜ 8.1 MB<br>本地文件：<code>assets/xx/video01.mp4</code></td>…</tr></table>` |
| `<title>…</title>`（正文开头，文档标题） | 提出来做 h1，**正文里原有的 `#` 标题整体降一级**（`#`→`##`、`##`→`###`），否则会和标题撞成同级 |
| `<whiteboard token="...">` | 导出图后按普通图片引用 |
| `<sheet sheet-id="..." token="...">` | **必须**读取内容还原成 Markdown 表格，见下 |
| `<grid><column width-ratio="0.5">` | 飞书多栏图片网格。Markdown 不支持分栏，**首选转成 HTML 一行表格**保留并排语义：`<table><tr><td><img src="a.png" width="100%"></td><td><img src="b.png" width="100%"></td></tr></table>`；若目标渲染器不吃 HTML，再降级为按 column 顺序展开成连续图片 |
| `<img>` / `![](https://feishu.cn/file/xxx)` | 换成下载的本地图片路径 `![说明](assets/xx.png)` |
| 代码块语言标记大写（` ```Markdown `、```JSON ```） | 统一小写（` ```markdown `、```json ```） |
| ` ```Plain Text ` | 改成 ` ```text ` |
| 标题里自带加粗（`## **一、xxx**`） | 去掉 `**`，写成 `## 一、xxx` |
| 连续空行 3 个以上 | 压成 1 个空行 |

**内嵌表格要单独读取**（否则正文里只剩一个空标签）：

```bash
lark-cli sheets +csv-get --spreadsheet-token "<token>" --sheet-id "<sheet-id>"
```

注意参数是 `--spreadsheet-token`，不是 `--spreadsheet`。返回 `annotated_csv` 每行带 `[row=N]` 前缀，据此还原表格。

### 5. 组装最终文档

目录结构：

```
<文档标题>/
  <文档标题>.md
  assets/
    01-xxx.png
    ...
```

正文 **开头加来源元信息**，方便回溯：

```markdown
> 来源：飞书云文档 <原始 URL>
> 文档 ID：`xxx` ｜ 版本：`NNN` ｜ 抓取时间：YYYY-MM-DD
```

**文末附素材清单表格**（文件名 / 说明 / 大小），并在表格下注明被还原的内嵌表格来源。

**标题层级**：原文档用 h1 或 h2 起手都可以，导出时统一按语义规范化（h1 作章、h2 作节）。

**正文内容保持原样，不要润色、不要改写、不要纠错**（包括原文的错别字和口语化表达），只做格式转换。

**批量导出多篇同系列文档时**，所有 md 放同一目录，素材按文档分子目录，避免多篇的 `img01.png` 互相覆盖：

```
output/
  《A》.md
  《B》.md
  assets/
    a-slug/   01.png 02.png ...
    b-slug/   01.png 02.png ...
```

正文里引用 `./assets/a-slug/xx.png`。若先做了单篇、后来才加第二篇，把先前的图移进子目录后同步批量替换 md 里的路径即可。

### 6. 收尾

- 删除临时文件 `_fetch.json`、`_content.md`。
- `present_files` 呈现：md 文件放第一个，后面跟 2-3 张有代表性的图片或视频。

## 真实案例参考

- `PdgIwQiu1invImkw599cWMM8n2b` → 《【1-2】Coze对话式Agent实战初体验》，1 图 + 3 视频
- `J2eHwigzQiidlBkUzKtc30YhnPb` → 《【2-1】Coze智能体初体验-养生馆智能体》，19 张截图
- `GZtpwdpvEiTTqnkZaH3cwLX0nJg` → 《【2-3】Coze变量以及数据类型》，2 图 + 1 画板 + 1 内嵌表格
- `JzF7wUKmeiOwkNkdFXUct0htnXj` → 《【2-5】Coze大模型节点-哪吒表情包生成器》，8 图 + 1 画板；提示词内容在截图里，需注明「无文本版提示词」
- `DsZZw8U9Ri3XDxkQV0gcmzBCnyf` → 《【2-2】Coze工作流基础-文生图工作流实战》，10 图 + 1 画板
- `BiKrwAxkXiNp9tkOtpecmh02nTc` → 《【2-4】Coze工作流基础-IF选择器》，11 图
- `BJAjwf0BNiWXqNkGd5ycUHxdn5g` → 《【2-8】Coze画板模块-小红书宠物问诊封面》，11 图
- `GjkYwmqKziH4VOkubO0cum8jnvh` → 《【2-11】Coze抠图模块-证件照生成器》，10 图（含 1 组三图分栏 grid）
- `KctVwn3iIi2FUNkX3k4c1EbFnqf` → 《【2-9】Coze实战进阶-儿童绘本故事》，25 图，多处 `<grid>` 多栏排版
- `SNfMw6CYTiwzeDk2euKc9SlwnOd` → 《【2-10】Coze批处理模块-小红书养生食谱卡片》，14 图，两处三栏 `<grid>`；
  正文步骤标题是加粗段落（`**开始节点：**`）而非真标题，保留原样不改成 heading
- `PMF9wCENWiq7OMkpoYucebRLnYm` → 《【2-14】Coze文本转文档-教辅智能体自动组卷工作流》，7 图；
  步骤说明是「`**开始节点**：xxx`」式加粗行内标签，保留原样
- `HyFVwCV6fiiWG8kHgDTcj0zQnVb` → 《【2-15】Coze图片识别-作文批改工作流》，11 图（1 组三图 grid + 1 处 callout）
- `PI2fwzPqJiOQelkfwSecUQFzn6c` → 《【3-3】Coze电商-一键换装App》，13 图，两处三栏 `<grid>`；
  标题在 `<title>` 标签里（不在正文首行），正文用 h1 + h3 混合层级，需规范化为 h1 + h2 + h3
- `G1phwiot8iPA5LkrYImcaheJnSg` → 《【3-2】Coze爆款短视频-养生赛道短视频》，29 图 + 2 视频（视频在一个两栏 `<grid>` 里）；
  节点说明用「`**作用：**`／`**输入：**`」加粗行内标签，保留原样
- `V2lww0sBhiYudskl6awcDWWwn7d` → 《【3-5】Coze电商-一键生成种草带货视频》，2 视频 + 6 图；
  **`outline` 返回空**（文档通篇无标题块），这种不能拆章节，要保持段落原文，只在文末加素材清单
- `QXftwoSoKidDkmk486wcUUzrnVg` → 《【3-6】Coze电商-一键生成AB剧情对话带货视频》，11 图 + 1 视频（视频是独立的 `<figure>`，不在 grid 里）；
  正文只有 1 个 h1、其余全是加粗段落，属正常，不用补标题
- `GEDHwqRs7ijgnhkqVNdc6Mrvnmb` → 《【3-9】Coze漫剧-角色三视图和场景图》，13 图，两处两栏 `<grid>`；
  正文标题全是 h3（`### 开始节点：`），规范化成 h2
- `NqvYwO89JiY4WtkujCIcyNdxnRu` → 《【3-10】Coze教育-作文批改助手App》，31 图 + 5 处 callout，无视频无画板；
  31 张图分 6 批下载（6/6/6/6/6/1）全程零失败，说明「每批 ≤6 + sleep 1」的节奏对 30+ 张也够用
- `Fin2wT3nPiuRC1kyXo1cn7b8nAc` → 《【3-12】Coze教育-教学管理-题库与智能组卷》，11 图 + 2 处 callout；
  原文「三、引用工作流」用了 `###`（与「一」「二」的 `##` 不同级），**保持原样不纠正**——只做格式转换，不顺手修作者的层级笔误。
  callout 正文里带 `**加粗**` 时，转引用块要保留加粗
- `TKB1wjUDSi6IsKk0NpRc9vfLnYb` → 《【3-14】Coze教育-教培机构-招生咨询与课程推荐智能体》，21 图 + 1 内嵌多维表格（20 列字段定义）；
  表格用 `lark-cli sheets +csv-get` 取 `annotated_csv` 字段还原成 Markdown 表；注意该接口返回 JSON 而非 CSV，要先 `json.load` 再取 `data['annotated_csv']`
  **批量下载易触发 429 限流**（提示"使用量已超出频率限制"，带固定重置时间）；遇到 429 先停下来、过段时间再续传，断点可从已下载列表推算
- `E6DpwcaVCik4JvkrlEXcB02unee` → 《【3-16】Coze教育-学员答疑与薄弱点辅导智能体》，18 图 + 5 处 callout，无视频/画板/grid；
  18 张分 3 批（6/6/6）零失败；标题已是标准 h1+h2/h3，无需 `<title>` 提级，直接转 callout→引用块即可
- `VtzcwDdYCiI21KkCwYfcwhJfnZc` → 《【3-18】Coze金融-客户需求采集与适当性辅助智能体》，11 图 + 1 处 callout，无视频/画板/grid；
  正文较短（~1.3k 字符），标准 h1+h2 结构，2 批（6/5）下载零失败，全流程无特殊处理
- `Y9CWwaJzsiAiJlkWdxdcI93un7e` → 《【3-20】Coze法律-合同与文书初筛智能体》，1 视频 + 21 图；
  视频用 `<figure>` 标签（`<source ... token=.../>`），走 `media-preview` 下载；正文章节原文是 h3，规范化成 h2；
  callout 里强调"只能做初筛提示，不能替律师给最终法律意见"，保留原样

### 遇到 `outline` 为空时

说明原文没有任何标题块，**不要自作主张把段落里的"开始节点："之类文字提升成 heading**——那属于改写。
做法：正文照原文段落排，只在开头加来源元信息、结尾加素材清单，并在清单下注明"原文档无标题层级"。

## 速查

| 目的 | 命令 |
| --- | --- |
| 看目录 | `docs +fetch --doc <URL> --scope outline --max-depth 3` |
| 抓全文 | `docs +fetch --doc <URL> --doc-format markdown --detail simple` |
| 下图片/视频 | `docs +media-preview --token <tok> --output <path>` |
| 下画板 | `docs +media-download --type whiteboard --token <tok> --output <path>` |
| 读内嵌表格 | `sheets +csv-get --spreadsheet-token <tok> --sheet-id <id>` |
