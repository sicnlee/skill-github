---
name: nora-ssh-remote-exec
description: >
  通过 paramiko SSH 连接远程 Linux 服务器并执行命令。
  当用户需要连接远程服务器、在服务器上运行命令、查看服务器状态时使用此技能。
  触发词：SSH、远程服务器、172.18.175.33、执行命令、服务器操作。
agent_created: true
---

# SSH Remote Exec

## 用途

通过 paramiko 库 SSH 连接远程服务器，安全执行任意命令并返回结果。

## 何时使用

- 用户提供服务器 IP、端口、账号、密码并要求连接
- 需要在远程服务器上执行 Shell 命令
- 查看服务器状态（磁盘、内存、进程等）

## 工作流程

### 前置要求

确保 paramiko 已安装：
```bash
pip install paramiko
```

### 快速执行

使用 `scripts/ssh_exec.py` 脚本，该脚本预置了默认连接信息（172.18.175.33:2222, root），可直接传入命令执行：

```bash
python <skill-dir>/scripts/ssh_exec.py "<command>"
```

### 自定义连接

如需连接其他服务器，在 Python 中使用 paramiko：

```python
import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<host>', port=<port>, username='<user>', password='<pwd>', timeout=10)
stdin, stdout, stderr = ssh.exec_command('<command>')
print(stdout.read().decode())
ssh.close()
```

### 重要约束

- paramiko `exec_command` 等待后台进程时可能挂起，不要直接在远程启动 nohup 后台进程
- 对于需要后台运行的服务，使用 `scripts/ssh_start_server.py`（见 remote-python-server 技能）
- 命令执行完后务必关闭连接
- 不要在日志中输出明文密码
