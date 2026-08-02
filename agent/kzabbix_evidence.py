#!/usr/bin/env python3
from __future__ import annotations

import glob
import json
import os
import re
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUTPUT = Path("/var/tmp/kzabbix/evidence.json")
SECRET = re.compile(
    r"(?i)(password|passwd|secret|token|authorization|api[_-]?key)(\s*[:=]\s*)[^\s,;]+"
)


def redact(text: str) -> str:
    return SECRET.sub(r"\1\2[REDACTED]", text)


def run(args: list[str], *, timeout: int = 10, limit: int = 6000) -> str:
    try:
        result = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return f"unavailable: {type(exc).__name__}"
    output = result.stdout.strip()
    if result.returncode and result.stderr:
        output = f"{output}\n{result.stderr.strip()}".strip()
    return redact(output[-limit:])


def read_text(path: str, limit: int = 3000) -> str:
    try:
        return redact(Path(path).read_text(encoding="utf-8", errors="replace").strip()[-limit:])
    except OSError as exc:
        return f"unavailable: {exc.strerror or type(exc).__name__}"


def process_io_sample() -> dict[int, tuple[int, int, str]]:
    result: dict[int, tuple[int, int, str]] = {}
    for io_path in glob.glob("/proc/[0-9]*/io"):
        try:
            pid = int(io_path.split("/")[2])
            values = {}
            for line in Path(io_path).read_text().splitlines():
                key, value = line.split(":", 1)
                values[key] = int(value.strip())
            name = Path(f"/proc/{pid}/comm").read_text(errors="replace").strip()
            result[pid] = (values.get("read_bytes", 0), values.get("write_bytes", 0), name)
        except (OSError, ValueError):
            continue
    return result


def top_process_io() -> list[dict[str, Any]]:
    before = process_io_sample()
    time.sleep(0.5)
    after = process_io_sample()
    rows = []
    for pid, (read_after, write_after, name) in after.items():
        if pid not in before:
            continue
        read_before, write_before, _ = before[pid]
        read_delta = max(0, read_after - read_before)
        write_delta = max(0, write_after - write_before)
        if not read_delta and not write_delta:
            continue
        rows.append(
            {
                "pid": pid,
                "process": redact(name)[:120],
                "read_bytes_per_0_5s": read_delta,
                "write_bytes_per_0_5s": write_delta,
            }
        )
    return sorted(
        rows,
        key=lambda row: row["read_bytes_per_0_5s"] + row["write_bytes_per_0_5s"],
        reverse=True,
    )[:20]


def network_counters() -> list[dict[str, Any]]:
    rows = []
    try:
        lines = Path("/proc/net/dev").read_text().splitlines()[2:]
        for line in lines:
            interface, values = line.split(":", 1)
            fields = values.split()
            rows.append(
                {
                    "interface": interface.strip(),
                    "rx_bytes": int(fields[0]),
                    "rx_errors": int(fields[2]),
                    "rx_dropped": int(fields[3]),
                    "tx_bytes": int(fields[8]),
                    "tx_errors": int(fields[10]),
                    "tx_dropped": int(fields[11]),
                }
            )
    except (OSError, ValueError, IndexError):
        return []
    return rows


def nvme_sysfs() -> list[dict[str, str]]:
    devices = []
    for path in sorted(glob.glob("/sys/class/nvme/nvme[0-9]*")):
        devices.append(
            {
                "device": Path(path).name,
                "model": read_text(f"{path}/model", 200),
                "firmware": read_text(f"{path}/firmware_rev", 100),
                "state": read_text(f"{path}/state", 100),
            }
        )
    return devices


def collect() -> dict[str, Any]:
    return {
        "schema": "kzabbix-evidence-v1",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "host": socket.gethostname(),
        "system": {
            "uptime": run(["uptime"], limit=1000),
            "loadavg": read_text("/proc/loadavg", 500),
            "memory": run(["free", "-m"], limit=3000),
            "filesystems": run(["df", "-hT", "-x", "tmpfs", "-x", "devtmpfs"], limit=5000),
            "failed_units": run(["systemctl", "--failed", "--no-pager", "--no-legend"], limit=5000),
        },
        "pressure": {
            "cpu": read_text("/proc/pressure/cpu", 1000),
            "io": read_text("/proc/pressure/io", 1000),
            "memory": read_text("/proc/pressure/memory", 1000),
        },
        "disk": {
            "iostat": run(["iostat", "-xz", "1", "2"], timeout=8, limit=10000),
            "diskstats": read_text("/proc/diskstats", 7000),
            "top_process_io": top_process_io(),
            "nvme": nvme_sysfs(),
        },
        "processes": run(
            ["ps", "-eo", "pid,ppid,user,stat,comm,%cpu,%mem", "--sort=-%cpu"], limit=6000
        ),
        "containers": run(
            [
                "docker",
                "stats",
                "--no-stream",
                "--format",
                "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.BlockIO}}\t{{.NetIO}}",
            ],
            timeout=12,
            limit=6000,
        ),
        "network": network_counters(),
        "logs": {
            "journal_warning": run(
                [
                    "journalctl",
                    "--since",
                    "-5 minutes",
                    "--priority",
                    "warning..alert",
                    "--no-pager",
                    "-n",
                    "120",
                    "--output",
                    "short-iso",
                ],
                limit=8000,
            ),
            "kernel_warning": run(
                [
                    "journalctl",
                    "-k",
                    "--since",
                    "-10 minutes",
                    "--priority",
                    "warning..alert",
                    "--no-pager",
                    "-n",
                    "100",
                    "--output",
                    "short-iso",
                ],
                limit=7000,
            ),
            "syslog_errors": run(
                [
                    "sh",
                    "-c",
                    (
                        "tail -n 500 /var/log/syslog | grep -Ei "
                        "'error|fail|warn|critical|timeout|i/o|nvme|disk|oom|segfault' | tail -n 100"
                    ),
                ],
                limit=7000,
            ),
        },
    }


def write_evidence(data: dict[str, Any]) -> None:
    OUTPUT.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if len(raw.encode()) > 60_000:
        data["logs"] = {
            key: value[-2000:] if isinstance(value, str) else value
            for key, value in data.get("logs", {}).items()
        }
        data["processes"] = str(data.get("processes", ""))[:3000]
        data["containers"] = str(data.get("containers", ""))[:3000]
        raw = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    temporary = OUTPUT.with_suffix(".tmp")
    temporary.write_text(raw, encoding="utf-8")
    temporary.chmod(0o644)
    temporary.replace(OUTPUT)


if __name__ == "__main__":
    write_evidence(collect())
