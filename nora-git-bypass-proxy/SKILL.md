---
name: nora-git-bypass-proxy
description: >
  配置 Git 仓库绕过本地 HTTP 代理，直接使用 WiFi/直连访问内网 Git 服务器。
  当 Git 操作因代理设置（如 Clash）导致无法访问内网 GitLab 等内部服务时使用此技能。
  触发词：git 代理、绕过代理、直连、proxy、502、git clone 失败、内网 GitLab。
agent_created: true
---

# Git Bypass Proxy

## 用途

解决因本地 HTTP 代理（Clash/Shadowsocks 等，常见端口 7897）导致无法访问内网 Git 服务器的问题。

## 何时使用

- `git clone/pull/fetch` 返回 502/连接超时
- 已知本地有代理但未运行（`HTTP_PROXY=127.0.0.1:7897` 已设置）
- 目标 Git 服务器是内网地址（如 `ec-gitlab.ecgtool.com`）

## 工作流程

### 诊断

先检查环境变量中是否有代理：

```bash
echo "HTTP_PROXY=$HTTP_PROXY"
echo "http_proxy=$http_proxy"
```

如果输出 `127.0.0.1:7897` 之类，说明代理已设置但可能未运行。

### 测试直连

```bash
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy
curl -s -o /dev/null -w "HTTP:%{http_code}" --connect-timeout 10 --noproxy '*' "http://目标服务器"
```

如果返回 200/302（而非 502），说明直连可用。

### 临时绕代理（单次）

```bash
export http_proxy="" https_proxy="" HTTP_PROXY="" HTTPS_PROXY=""
git -c http.proxy="" clone http://host/repo.git
```

### 永久绕代理（推荐）

对每个内网仓库设置一次，一劳永逸：

```bash
cd <repo-dir>
git config http.proxy ""
```

验证：

```bash
git config --list --local | grep proxy
# 应输出: http.proxy=
```

之后所有 git 操作自动绕过代理，无需每次指定 `-c http.proxy=""`。

### 重要约束

- 此配置仅影响当前仓库，不影响其他仓库或全局 git 配置
- 如果代理恢复正常，需要手动改回 `git config http.proxy ""`
- 对于非 git 的 HTTP 请求（如 curl），仍需手动 unset 代理变量
