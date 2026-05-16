#!/usr/bin/env python3
"""gateway_fd_soak.py — Lightweight gateway FD/resource soak helper (ALF-263).

Periodically samples file-descriptor and resource metrics for a running
gateway process (and optionally its children) and appends rows to a CSV
file so you can track FD growth over time without touching gateway behavior.

Usage
-----
    python scripts/gateway_fd_soak.py --pid <PID> [options]

    # Auto-detect the running gateway PID and poll every 10 s for 1 hour:
    python scripts/gateway_fd_soak.py --interval 10 --duration 3600

    # Poll a specific PID every 5 s, writing to a custom CSV:
    python scripts/gateway_fd_soak.py --pid 12345 --interval 5 --out /tmp/soak.csv

Options
-------
    --pid PID           Gateway PID to monitor (default: auto-detect via ps/launchctl).
    --interval SECS     Sampling interval in seconds (default: 30).
    --duration SECS     How long to run before stopping (default: run until Ctrl-C).
    --out PATH          CSV output path (default: /tmp/hermes_gateway_fd_soak.csv).
    --no-children       Skip aggregating child-process FD counts.

CSV columns
-----------
    timestamp           ISO-8601 wall clock.
    pid                 Monitored PID.
    fd_total            Total open FD count for the process.
    fd_close_wait       Sockets in CLOSE_WAIT state associated with the PID.
    fd_sqlite           File handles whose path ends with .db / .sqlite / .sqlite3.
    fd_pipe             PIPE / FIFO handles.
    rss_kb              Resident set size in KB.
    child_count         Number of direct child processes.
    fd_children_total   Aggregate FD count across all child processes (0 if --no-children).

Notes
-----
* This script is **read-only** — it only calls /proc (Linux), lsof, ps, and
  netstat/ss; it never writes to or signals the gateway process.
* Requires Python 3.8+.  ``lsof`` and ``ps`` must be on PATH (standard on
  macOS and most Linux distros).  On Linux, ``ss`` is preferred over
  ``netstat`` for CLOSE_WAIT counting but ``netstat`` is used as a fallback.
* Missing metrics are recorded as -1 so the CSV row is always complete.
* ALF-263 background: the gateway previously ran under launchd's default
  256-FD limit.  The plist generator now emits SoftResourceLimits /
  HardResourceLimits NumberOfFiles=65536.  Use this script to verify that
  FD counts stay well under the new limit during extended operation.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import os
import subprocess
import sys
import time
from pathlib import Path


# ---------------------------------------------------------------------------
# Helper: run a subprocess and return stdout lines, never raising on failure.
# ---------------------------------------------------------------------------

def _run(cmd: list[str]) -> list[str]:
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=10,
            text=True,
        )
        return result.stdout.splitlines()
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Auto-detect gateway PID
# ---------------------------------------------------------------------------

def _autodetect_pid() -> int | None:
    """Return the PID of a running hermes gateway process, or None."""
    # Try launchctl on macOS first
    lines = _run(["launchctl", "list"])
    for line in lines:
        if "hermes" in line.lower() and "gateway" in line.lower():
            parts = line.split()
            if parts and parts[0].lstrip("-").isdigit():
                pid = int(parts[0])
                if pid > 0:
                    return pid

    # Fall back to ps
    for pattern in ["hermes.*gateway", "gateway.*hermes", "run.py.*gateway"]:
        lines = _run(["pgrep", "-f", pattern])
        if lines:
            try:
                return int(lines[0].strip())
            except ValueError:
                pass

    # Last resort: search for hermes gateway processes via ps
    lines = _run(["ps", "aux"])
    for line in lines:
        lower = line.lower()
        if "hermes" in lower and "gateway" in lower and "grep" not in lower:
            parts = line.split()
            if len(parts) > 1:
                try:
                    return int(parts[1])
                except ValueError:
                    pass
    return None


# ---------------------------------------------------------------------------
# Metric samplers
# ---------------------------------------------------------------------------

def _fd_total(pid: int) -> int:
    """Total open FD count for *pid*."""
    # /proc is available on Linux
    proc_fd = Path(f"/proc/{pid}/fd")
    if proc_fd.is_dir():
        try:
            return sum(1 for _ in proc_fd.iterdir())
        except PermissionError:
            pass

    # macOS / fallback: lsof
    lines = _run(["lsof", "-p", str(pid)])
    # subtract 1 for the header line
    count = max(0, len(lines) - 1)
    return count if count >= 0 else -1


def _fd_close_wait(pid: int) -> int:
    """Number of sockets in CLOSE_WAIT state for *pid*."""
    # Try ss (Linux)
    lines = _run(["ss", "-tp"])
    count = sum(
        1 for line in lines
        if "CLOSE-WAIT" in line and f"pid={pid}," in line
    )
    if count:
        return count

    # Try netstat (macOS / Linux fallback)
    lines = _run(["netstat", "-anp"])  # Linux
    if not lines:
        lines = _run(["netstat", "-anv"])  # macOS (no -p)

    # macOS lsof-based approach: parse tcp sockets in CLOSE_WAIT
    lsof_lines = _run(["lsof", "-p", str(pid), "-iTCP", "-sTCP:CLOSE_WAIT"])
    return max(0, len(lsof_lines) - 1)


def _fd_sqlite(pid: int) -> int:
    """FD handles whose resolved path looks like a SQLite database."""
    lines = _run(["lsof", "-p", str(pid)])
    count = 0
    for line in lines[1:]:  # skip header
        lower = line.lower()
        if lower.endswith(".db") or ".db " in lower or ".sqlite" in lower:
            count += 1
    return count


def _fd_pipe(pid: int) -> int:
    """PIPE / FIFO handles for *pid*."""
    # /proc on Linux
    proc_fd = Path(f"/proc/{pid}/fd")
    if proc_fd.is_dir():
        count = 0
        try:
            for entry in proc_fd.iterdir():
                try:
                    target = os.readlink(str(entry))
                    if "pipe:" in target or "fifo:" in target.lower():
                        count += 1
                except OSError:
                    pass
        except PermissionError:
            pass
        return count

    # macOS / fallback: lsof
    lines = _run(["lsof", "-p", str(pid)])
    return sum(1 for line in lines[1:] if "\tpipe" in line.lower() or "fifo" in line.upper())


def _rss_kb(pid: int) -> int:
    """Resident set size in KB for *pid*."""
    # /proc/status on Linux
    proc_status = Path(f"/proc/{pid}/status")
    if proc_status.is_file():
        try:
            for line in proc_status.read_text().splitlines():
                if line.startswith("VmRSS:"):
                    return int(line.split()[1])
        except Exception:
            pass

    # ps on macOS / fallback
    lines = _run(["ps", "-o", "rss=", "-p", str(pid)])
    if lines:
        try:
            return int(lines[0].strip())
        except ValueError:
            pass
    return -1


def _child_count(pid: int) -> int:
    """Number of direct child processes of *pid*."""
    lines = _run(["pgrep", "-P", str(pid)])
    return len([l for l in lines if l.strip().isdigit()])


def _children_pids(pid: int) -> list[int]:
    lines = _run(["pgrep", "-P", str(pid)])
    result = []
    for line in lines:
        line = line.strip()
        if line.isdigit():
            result.append(int(line))
    return result


def _fd_children_total(pid: int) -> int:
    """Aggregate FD count across all direct children."""
    total = 0
    for child_pid in _children_pids(pid):
        v = _fd_total(child_pid)
        if v >= 0:
            total += v
    return total


# ---------------------------------------------------------------------------
# Sample → dict
# ---------------------------------------------------------------------------

def sample(pid: int, *, include_children: bool = True) -> dict:
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    return {
        "timestamp": now,
        "pid": pid,
        "fd_total": _fd_total(pid),
        "fd_close_wait": _fd_close_wait(pid),
        "fd_sqlite": _fd_sqlite(pid),
        "fd_pipe": _fd_pipe(pid),
        "rss_kb": _rss_kb(pid),
        "child_count": _child_count(pid),
        "fd_children_total": _fd_children_total(pid) if include_children else 0,
    }


FIELDNAMES = [
    "timestamp", "pid", "fd_total", "fd_close_wait",
    "fd_sqlite", "fd_pipe", "rss_kb", "child_count", "fd_children_total",
]


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Hermes gateway FD/resource soak helper (ALF-263)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--pid", type=int, default=None, help="Gateway PID (auto-detect if omitted)")
    parser.add_argument("--interval", type=float, default=30.0, help="Polling interval in seconds (default: 30)")
    parser.add_argument("--duration", type=float, default=None, help="Stop after this many seconds (default: run forever)")
    parser.add_argument("--out", default="/tmp/hermes_gateway_fd_soak.csv", help="CSV output path")
    parser.add_argument("--no-children", action="store_true", help="Skip child FD aggregation")
    args = parser.parse_args()

    pid = args.pid
    if pid is None:
        pid = _autodetect_pid()
        if pid is None:
            print("ERROR: Could not auto-detect gateway PID. Pass --pid explicitly.", file=sys.stderr)
            sys.exit(1)
        print(f"[soak] Auto-detected gateway PID: {pid}", file=sys.stderr)

    out_path = Path(args.out)
    write_header = not out_path.exists() or out_path.stat().st_size == 0

    print(f"[soak] Writing metrics to {out_path}  (interval={args.interval}s)", file=sys.stderr)

    deadline = time.monotonic() + args.duration if args.duration else None

    with out_path.open("a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()

        try:
            while True:
                row = sample(pid, include_children=not args.no_children)
                writer.writerow(row)
                fh.flush()
                print(
                    f"[soak] {row['timestamp']}  pid={row['pid']}"
                    f"  fd={row['fd_total']}"
                    f"  close_wait={row['fd_close_wait']}"
                    f"  sqlite={row['fd_sqlite']}"
                    f"  pipe={row['fd_pipe']}"
                    f"  rss={row['rss_kb']}KB"
                    f"  children={row['child_count']}"
                    f"  fd_children={row['fd_children_total']}",
                    file=sys.stderr,
                )
                if deadline is not None and time.monotonic() >= deadline:
                    break
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n[soak] Interrupted by user.", file=sys.stderr)

    print(f"[soak] Done. CSV written to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
