#!/usr/bin/env python3
"""Test MCP server handshake and list available tools."""
import json
import subprocess
import sys

PYTHON = "./server/venv/bin/python"

MESSAGES = [
    {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1.0"}
    }},
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
]

proc = subprocess.Popen(
    [PYTHON, "-m", "server.main"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)

try:
    for msg in MESSAGES:
        line = json.dumps(msg) + "\n"
        proc.stdin.write(line)
        proc.stdin.flush()

        if "id" in msg:  # only expect response for requests (not notifications)
            response_line = proc.stdout.readline()
            if not response_line:
                print("ERROR: Server closed stdout unexpectedly")
                stderr = proc.stderr.read()
                if stderr:
                    print(f"STDERR:\n{stderr}")
                sys.exit(1)
            resp = json.loads(response_line)
            print(f">> Request:  {msg['method']}")
            print(f"<< Response: {json.dumps(resp, indent=2)}")
            print()
finally:
    proc.terminate()
    proc.wait()

# Print any stderr output
stderr = proc.stderr.read()
if stderr:
    print(f"Server stderr:\n{stderr}")
