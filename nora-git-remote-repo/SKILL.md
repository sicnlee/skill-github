---
name: nora-git-remote-repo
description: >
  在远程服务器上管理 Git 仓库：clone、pull、查看日志。
  当用户需要在远程服务器上克隆或更新 Git 项目时使用此技能。
  触发词：服务器上 clone、远程 git、拉取代码、git pull、更新服务器项目。
agent_created: true
---

# Git Remote Repo

## 用途

在通过 SSH 连接的远程服务器上执行 Git 操作（clone、pull、log），并自动清理 remote URL 中的明文密码。

## 何时使用

- 用户要求在远程服务器上 clone 一个 Git 仓库
- 用户要求在远程服务器上 pull/更新已有项目
- 需要查看远程服务器上项目的 Git 日志

## 工作流程

### 前置条件

远程服务器必须已通过 SSH 连接（参考 ssh-remote-exec 技能），且已安装 git。

### Clone 仓库

1. 先在服务器上创建目标目录
2. 使用带凭据的 URL clone（`http://user:pwd@host/repo.git`）
3. Clone 完成后立即清理 remote URL 中的密码：

```bash
python <ssh-exec-dir>/scripts/ssh_exec.py "mkdir -p /home/project && cd /home/project && git clone 'http://user:password@host/repo.git' 2>&1"
python <ssh-exec-dir>/scripts/ssh_exec.py "cd /home/project/repo && git remote set-url origin 'http://host/repo.git' && git remote -v"
```

### Pull 更新

1. 先设置带凭据的 remote URL
2. 执行 pull
3. 清理密码

```bash
python <ssh-exec-dir>/scripts/ssh_exec.py "cd /home/project/repo && git remote set-url origin 'http://user:pwd@host/repo.git' && git pull origin master 2>&1 && git remote set-url origin 'http://host/repo.git' && git log --oneline -5"
```

### 重要约束

- Clone 时 URL 中的密码特殊字符需 URL 编码（如 `(` → `%28`）
- 每次操作后必须清理 remote URL 中的密码
- GitLab 内网地址可能无法从本地直接访问，优先使用服务器中转
