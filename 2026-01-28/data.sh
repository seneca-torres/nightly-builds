#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
import json
import os
import re
import subprocess
import time
from glob import glob
from pathlib import Path

ROOT = Path('/Users/vicmacmini/clawd')
NOW = time.time()


def run(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, text=True)
        return out.strip()
    except Exception:
        return ""


def read_file(path):
    try:
        return Path(path).read_text()
    except Exception:
        return ""


def parse_cron_lines(lines, source, has_user_field=False):
    jobs = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('@'):
            parts = line.split()
            schedule = parts[0]
            cmd_parts = parts[1:]
            user = None
            if has_user_field and len(parts) >= 3:
                user = parts[1]
                cmd_parts = parts[2:]
            command = " ".join(cmd_parts)
        else:
            parts = line.split()
            if len(parts) < 6:
                continue
            schedule = " ".join(parts[:5])
            if has_user_field:
                user = parts[5]
                cmd_parts = parts[6:]
            else:
                user = None
                cmd_parts = parts[5:]
            command = " ".join(cmd_parts)
        if not command:
            continue
        name = Path(command.split()[0]).name
        jobs.append({
            "name": name,
            "schedule": schedule,
            "command": command,
            "user": user,
            "source": source,
            "last_run_time": None,
            "last_status": "unknown",
            "next_run": None,
        })
    return jobs


cron_jobs = []

# User crontab
crontab_out = run("crontab -l")
if crontab_out:
    cron_jobs.extend(parse_cron_lines(crontab_out.splitlines(), "user:crontab", has_user_field=False))

# /etc/crontab
etc_crontab = read_file("/etc/crontab")
if etc_crontab:
    cron_jobs.extend(parse_cron_lines(etc_crontab.splitlines(), "/etc/crontab", has_user_field=True))

# /etc/cron.d/*
for path in sorted(glob("/etc/cron.d/*")):
    content = read_file(path)
    if content:
        cron_jobs.extend(parse_cron_lines(content.splitlines(), path, has_user_field=True))


services = []
for svc in ["clawdbot-gateway", "clawdbot-shaq-diesel"]:
    show = run(f"systemctl show {svc} -p Id -p ActiveState -p SubState -p UnitFileState -p ActiveEnterTimestamp -p ExecMainStatus -p Result")
    data = {}
    for line in show.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            data[k] = v
    services.append({
        "name": svc,
        "active_state": data.get("ActiveState", "unknown"),
        "sub_state": data.get("SubState", "unknown"),
        "unit_file_state": data.get("UnitFileState", "unknown"),
        "last_started": data.get("ActiveEnterTimestamp", ""),
        "exec_main_status": data.get("ExecMainStatus", ""),
        "result": data.get("Result", ""),
    })


# Nightly build history
nightly_path = ROOT / "NIGHTLY-BUILDS.md"
completed_builds = []
if nightly_path.exists():
    lines = nightly_path.read_text().splitlines()
    in_completed = False
    for line in lines:
        if line.strip().startswith("### Completed"):
            in_completed = True
            continue
        if in_completed and line.strip().startswith("### "):
            break
        if in_completed:
            m = re.match(r"^\s*[-*]\s+(.*)", line)
            if m:
                completed_builds.append(m.group(1).strip())
            else:
                m2 = re.match(r"^\s*\d+\.\s+(.*)", line)
                if m2:
                    completed_builds.append(m2.group(1).strip())


# Project inventory
projects = []
for name in ["one-play-a-day-app", "cai-strategy-app", "raspberry-pi-scripts"]:
    path = ROOT / name
    exists = path.exists()
    item = {
        "name": name,
        "path": str(path),
        "exists": exists,
    }
    if exists:
        stat = path.stat()
        item["last_modified"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
        git_dir = path / ".git"
        if git_dir.exists():
            branch = run(f"git -C {path} rev-parse --abbrev-ref HEAD")
            dirty = bool(run(f"git -C {path} status --porcelain"))
            item["git_branch"] = branch or None
            item["git_dirty"] = dirty
        else:
            item["git_branch"] = None
            item["git_dirty"] = None
    projects.append(item)


# Health status
health = {}

# Disk
df_out = run("df -P /")
disk = {"mount": "/"}
if df_out:
    parts = df_out.splitlines()[-1].split()
    if len(parts) >= 6:
        disk.update({
            "filesystem": parts[0],
            "size": parts[1],
            "used": parts[2],
            "available": parts[3],
            "use_percent": int(parts[4].strip('%')),
            "mount": parts[5],
        })
health["disk"] = disk

# Memory + swap
meminfo = read_file("/proc/meminfo")
mem = {}
if meminfo:
    info = {}
    for line in meminfo.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            info[k.strip()] = int(v.strip().split()[0])
    total = info.get("MemTotal", 0)
    available = info.get("MemAvailable", 0)
    used = max(total - available, 0)
    mem = {
        "total_kb": total,
        "used_kb": used,
        "available_kb": available,
        "used_percent": int((used / total) * 100) if total else 0,
    }
    swap_total = info.get("SwapTotal", 0)
    swap_free = info.get("SwapFree", 0)
    swap_used = max(swap_total - swap_free, 0)
    mem["swap_total_kb"] = swap_total
    mem["swap_used_kb"] = swap_used
    mem["swap_used_percent"] = int((swap_used / swap_total) * 100) if swap_total else 0
health["memory"] = mem

# CPU temp
cpu_temp_c = None
temp_raw = read_file("/sys/class/thermal/thermal_zone0/temp")
if temp_raw:
    try:
        cpu_temp_c = round(int(temp_raw.strip()) / 1000, 1)
    except Exception:
        cpu_temp_c = None
if cpu_temp_c is None:
    vcg = run("vcgencmd measure_temp")
    m = re.search(r"temp=([0-9.]+)" , vcg)
    if m:
        cpu_temp_c = float(m.group(1))
health["cpu_temp_c"] = cpu_temp_c


# Health indicators

def indicator(value, yellow, red, higher_is_worse=True):
    if value is None:
        return "unknown"
    if higher_is_worse:
        if value >= red:
            return "red"
        if value >= yellow:
            return "yellow"
        return "green"
    else:
        if value <= red:
            return "red"
        if value <= yellow:
            return "yellow"
        return "green"

health_indicators = {
    "disk": indicator(health.get("disk", {}).get("use_percent"), 70, 85),
    "memory": indicator(health.get("memory", {}).get("used_percent"), 70, 85),
    "swap": indicator(health.get("memory", {}).get("swap_used_percent"), 20, 50),
    "cpu_temp": indicator(health.get("cpu_temp_c"), 70, 80),
}


payload = {
    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(NOW)),
    "cron_jobs": cron_jobs,
    "services": services,
    "nightly_builds_completed": completed_builds,
    "projects": projects,
    "health": health,
    "health_indicators": health_indicators,
}

print(json.dumps(payload, indent=2))
PY
