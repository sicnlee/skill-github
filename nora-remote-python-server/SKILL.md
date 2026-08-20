---
name: nora-remote-python-server
description: >
  在远程服务器上使用 Python HTTP Server 启动静态 Web 服务。
  当用户需要在远程服务器上运行 Python HTTP 服务、启动 Web 项目时使用此技能。
  触发词：启动服务、跑起来、HTTP server、端口、python http、nohup 启动。
agent_created: true
---

# Remote Python HTTP Server

## 用途

在远程 Linux 服务器上使用 Python 内置 HTTP Server 启动静态网站服务，设置指定端口并绑定 0.0.0.0。

## 何时使用

- 用户要求在远程服务器上"跑起来"一个静态 Web 项目
- 用户指定了端口号
- 用户希望通过浏览器访问服务器上的项目

## 工作流程

### 前置条件

- 远程服务器已通过 SSH 连接（参考 ssh-remote-exec 技能）
- 服务器上已安装 Python 3
- 项目目录已存在

### 启动服务

使用 `scripts/ssh_start_server.py` 脚本，该脚本通过 paramiko channel 机制解决 nohup 后台进程的挂起问题：

```bash
python <skill-dir>/scripts/ssh_start_server.py
```

默认配置：
- 项目目录: `/home/project/nora`
- 端口: `9494`
- 绑定地址: `0.0.0.0`

### 自定义参数

如需修改目录或端口，编辑脚本中的变量：
- `project_dir`: 项目路径
- `port`: 监听端口

### 验证服务

使用 ssh_exec.py 验证服务是否正常运行：

```bash
python <ssh-exec-dir>/scripts/ssh_exec.py "curl -s -o /dev/null -w '%{http_code}' http://localhost:<port>/"
```

### 重要约束

- 不要直接通过 paramiko `exec_command` 执行 nohup 命令，会无限等待
- 改用 `scripts/ssh_start_server.py` 的 channel 机制或 `invoke_shell()` + `send()` 方式
- 服务启动前先 kill 占用同一端口的旧进程
- 务必绑定 `--bind 0.0.0.0`，否则外网无法访问
