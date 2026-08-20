"""Start a background HTTP server on remote via paramiko, with proper channel timeout"""
import paramiko
import sys
import time

HOST = "172.18.175.33"
PORT = 2222
USER = "root"
PASS = "WPZJG0FsYjxbJbNA"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER, password=PASS, timeout=10)

transport = ssh.get_transport()

# Step 1: Kill existing process on 9494
chan = transport.open_session()
chan.settimeout(5)
chan.exec_command("fuser -k 9494/tcp 2>/dev/null; sleep 1; echo KILL_DONE")
time.sleep(3)
try:
    out = b""
    while chan.recv_ready():
        out += chan.recv(4096)
    print("Cleanup:", out.decode().strip())
except Exception:
    pass
chan.close()

# Step 2: Start server in background
chan2 = transport.open_session()
chan2.settimeout(5)
chan2.exec_command(
    "cd /home/project/nora && nohup python3 -m http.server 9494 --bind 0.0.0.0 "
    "> /tmp/nora_server.log 2>&1 & echo SERVER_PID=$!"
)
time.sleep(2)
try:
    out = b""
    while chan2.recv_ready():
        out += chan2.recv(4096)
    print("Start:", out.decode().strip())
except Exception:
    pass
chan2.close()

# Step 3: Verify it's running
chan3 = transport.open_session()
chan3.settimeout(5)
chan3.exec_command("ss -tlnp | grep 9494 && curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:9494/")
time.sleep(2)
try:
    out = b""
    while chan3.recv_ready():
        out += chan3.recv(4096)
    print("Verify:", out.decode().strip())
except Exception:
    pass
chan3.close()

ssh.close()
print("Done!")
