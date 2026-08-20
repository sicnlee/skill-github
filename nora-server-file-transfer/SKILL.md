---
name: nora-server-file-transfer
description: >
  通过 SFTP 在远程服务器和本地之间传输文件。
  当用户需要从远程服务器下载文件到本地、或上传文件到远程服务器时使用此技能。
  触发词：下载到本地、从服务器下载、上传到服务器、文件传输、SFTP。
agent_created: true
---

# Server File Transfer

## 用途

通过 SFTP 协议在本地电脑和远程 Linux 服务器之间传输文件。

## 何时使用

- 从远程服务器下载文件/目录到本地
- 上传本地文件到远程服务器
- 当本地无法直接访问某些内网资源，需要通过服务器中转时

## 工作流程

### 从服务器下载文件

使用 `scripts/ssh_download.py` 脚本：

```bash
python <skill-dir>/scripts/ssh_download.py
```

该脚本通过 paramiko SFTP 将服务器上的 `/tmp/nora.tar.gz` 下载到本地 `F:\元气满满\nora\nora.tar.gz`。

### 自定义传输

编辑脚本中的变量：
- `remote_path`: 服务器上的源文件路径
- `local_path`: 本地目标文件路径
- `ssh_host/port/user/password`: 连接凭证

### 打包传输目录

对于目录传输，先在服务器上打包：

```bash
python <ssh-exec-dir>/scripts/ssh_exec.py "cd /home/project/<dir> && tar czf /tmp/<name>.tar.gz --exclude=.git ."
```

再通过 SFTP 下载 tar.gz 文件，最后在本地解压。

### 重要约束

- 大文件传输可能超时，建议先打包压缩
- 传输完成后清理服务器上的临时文件
- 密码特殊字符需注意编码
