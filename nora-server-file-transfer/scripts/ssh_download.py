"""Download files from remote server via SFTP using paramiko"""
import paramiko
import sys
import os

HOST = "172.18.175.33"
PORT = 2222
USER = "root"
PASS = "WPZJG0FsYjxbJbNA"

remote_file = "/tmp/nora.tar.gz"
local_file = r"F:\元气满满\nora\nora.tar.gz"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER, password=PASS, timeout=10)

sftp = ssh.open_sftp()
print(f"Downloading {remote_file} ...")
sftp.get(remote_file, local_file)
print(f"Saved to {local_file}")
print(f"Size: {os.path.getsize(local_file)} bytes")

sftp.close()
ssh.close()
print("Done!")
