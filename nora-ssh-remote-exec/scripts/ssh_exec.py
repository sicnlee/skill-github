"""SSH remote command executor for 172.18.175.33:2222"""
import paramiko
import sys

HOST = "172.18.175.33"
PORT = 2222
USER = "root"
PASS = "WPZJG0FsYjxbJbNA"

def run(cmd):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=PORT, username=USER, password=PASS, timeout=10)
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    out = stdout.read().decode()
    err = stderr.read().decode()
    exit_code = stdout.channel.recv_exit_status()
    ssh.close()
    if out:
        print(out, end="")
    if err:
        print(err, end="", file=sys.stderr)
    return exit_code

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ssh_exec.py <command>")
        print("Example: python ssh_exec.py 'ls -la /root'")
        sys.exit(1)
    cmd = " ".join(sys.argv[1:])
    sys.exit(run(cmd))
