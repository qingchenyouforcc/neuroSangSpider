from __future__ import annotations

import json
import platform
import subprocess
import sys
from datetime import datetime
from typing import Any

from loguru import logger

from src.config import IS_WINDOWS, subprocess_options


_DEVICE_INFO_LOGGED = False


def _safe_one_line(text: str, max_len: int = 260) -> str:
    s = " ".join(str(text).split())
    if len(s) > max_len:
        return s[: max_len - 1] + "…"
    return s


def _run_powershell_json(command: str, *, timeout_s: float = 2.5) -> Any | None:
    """Run PowerShell and parse stdout as JSON (best-effort)."""
    if not IS_WINDOWS:
        return None

    args = [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        command,
    ]

    try:
        p = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            **subprocess_options(),
        )
    except Exception as e:
        logger.debug(f"[device] powershell failed: {e}")
        return None

    stdout = (p.stdout or "").strip()
    if not stdout:
        return None

    try:
        return json.loads(stdout)
    except Exception:
        # 有时会混入 warning 文本，降级为原始字符串
        return stdout


def _ps_first(obj: Any) -> Any:
    if isinstance(obj, list) and obj:
        return obj[0]
    return obj


def collect_device_info() -> dict[str, Any]:
    info: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "arch": platform.machine(),
        "frozen": bool(getattr(sys, "frozen", False)),
    }

    # 避免写入过多隐私信息：不记录用户名/主机名/序列号

    if IS_WINDOWS:
        os_info = _ps_first(
            _run_powershell_json(
                "Get-CimInstance Win32_OperatingSystem | "
                "Select-Object Caption,Version,BuildNumber,OSArchitecture | "
                "ConvertTo-Json -Compress"
            )
        )
        if os_info is not None:
            info["windows.os"] = os_info

        cpu_info = _ps_first(
            _run_powershell_json(
                "Get-CimInstance Win32_Processor | "
                "Select-Object Name,Manufacturer,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed | "
                "ConvertTo-Json -Compress"
            )
        )
        if cpu_info is not None:
            info["cpu"] = cpu_info

        mem_info = _ps_first(
            _run_powershell_json(
                "Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory | ConvertTo-Json -Compress"
            )
        )
        if isinstance(mem_info, dict) and "TotalPhysicalMemory" in mem_info:
            info["memory"] = mem_info

        gpu_info = _run_powershell_json(
            "Get-CimInstance Win32_VideoController | "
            "Select-Object Name,AdapterRAM,DriverVersion,Status | "
            "ConvertTo-Json -Compress"
        )
        if gpu_info is not None:
            info["gpu"] = gpu_info

        sound_info = _run_powershell_json(
            "Get-CimInstance Win32_SoundDevice | Select-Object Name,Manufacturer,Status | ConvertTo-Json -Compress"
        )
        if sound_info is not None:
            info["sound"] = sound_info

    else:
        # 跨平台兜底：仅记录基础信息
        info["processor"] = platform.processor()

    return info


def _format_bytes(n: int | float | str | None) -> str:
    try:
        v = float(n)  # type: ignore[arg-type]
    except Exception:
        return "<unknown>"

    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while v >= 1024 and i < len(units) - 1:
        v /= 1024
        i += 1
    if i == 0:
        return f"{int(v)} {units[i]}"
    return f"{v:.2f} {units[i]}"


def log_device_info_once() -> None:
    global _DEVICE_INFO_LOGGED
    if _DEVICE_INFO_LOGGED:
        return
    _DEVICE_INFO_LOGGED = True

    try:
        info = collect_device_info()

        # 组一条简短 INFO 摘要（避免刷屏），详细内容放 DEBUG
        cpu_name = None
        if isinstance(info.get("cpu"), dict):
            cpu_name = info["cpu"].get("Name")

        os_caption = None
        if isinstance(info.get("windows.os"), dict):
            os_caption = info["windows.os"].get("Caption")

        mem_total = None
        if isinstance(info.get("memory"), dict):
            mem_total = info["memory"].get("TotalPhysicalMemory")

        sound = info.get("sound")
        sound_count = len(sound) if isinstance(sound, list) else (1 if isinstance(sound, dict) else 0)

        gpu = info.get("gpu")
        gpu_name = None
        if isinstance(gpu, list) and gpu:
            gpu_name = gpu[0].get("Name") if isinstance(gpu[0], dict) else None
        elif isinstance(gpu, dict):
            gpu_name = gpu.get("Name")

        logger.info(
            "设备信息: OS={} | CPU={} | 内存={} | GPU={} | 声卡设备数={}".format(
                _safe_one_line(os_caption or info.get("platform", "<unknown>")),
                _safe_one_line(cpu_name or "<unknown>"),
                _format_bytes(mem_total),
                _safe_one_line(gpu_name or "<unknown>"),
                sound_count,
            )
        )
        logger.debug(f"[device] details={info}")
    except Exception:
        logger.opt(exception=True).debug("[device] failed to collect device info")
