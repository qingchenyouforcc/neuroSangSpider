from __future__ import annotations

import json
import platform
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from src.config import CACHE_DIR, IS_WINDOWS, subprocess_options


_DEVICE_INFO_LOGGED = False
_DEVICE_INFO_THREAD_STARTED = False


def _cache_path() -> Path:
    return CACHE_DIR / "device_info.json"


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
        # 合并为一次 PowerShell 调用，避免多次启动 powershell.exe 带来的启动卡顿
        combined = _run_powershell_json(
            """
            $os = Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,OSArchitecture
            $cpu = Get-CimInstance Win32_Processor | Select-Object Name,Manufacturer,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed
            $mem = Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory
            $gpu = Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM,DriverVersion,Status
            $sound = Get-CimInstance Win32_SoundDevice | Select-Object Name,Manufacturer,Status
            [pscustomobject]@{ os=$os; cpu=$cpu; memory=$mem; gpu=$gpu; sound=$sound } | ConvertTo-Json -Compress
            """,
            timeout_s=6.0,
        )

        if isinstance(combined, dict):
            os_info = _ps_first(combined.get("os"))
            if os_info is not None:
                info["windows.os"] = os_info

            cpu_info = _ps_first(combined.get("cpu"))
            if cpu_info is not None:
                info["cpu"] = cpu_info

            mem_info = _ps_first(combined.get("memory"))
            if isinstance(mem_info, dict) and "TotalPhysicalMemory" in mem_info:
                info["memory"] = mem_info

            gpu_info = combined.get("gpu")
            if gpu_info is not None:
                info["gpu"] = gpu_info

            sound_info = combined.get("sound")
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


def _read_cache() -> dict[str, Any] | None:
    try:
        fp = _cache_path()
        if not fp.exists():
            return None
        raw = fp.read_text(encoding="utf-8")
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _write_cache(info: dict[str, Any]) -> None:
    try:
        fp = _cache_path()
        fp.parent.mkdir(parents=True, exist_ok=True)
        tmp = fp.with_suffix(".tmp")
        tmp.write_text(json.dumps(info, ensure_ascii=False), encoding="utf-8")
        tmp.replace(fp)
    except Exception:
        # 缓存失败不影响主流程
        logger.opt(exception=True).debug("[device] failed to write cache")


def _summarize_and_log(info: dict[str, Any], *, source: str) -> None:
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
        "设备信息({}): OS={} | CPU={} | 内存={} | GPU={} | 声卡设备数={}".format(
            source,
            _safe_one_line(os_caption or info.get("platform", "<unknown>")),
            _safe_one_line(cpu_name or "<unknown>"),
            _format_bytes(mem_total),
            _safe_one_line(gpu_name or "<unknown>"),
            sound_count,
        )
    )
    logger.debug(f"[device] details({source})={info}")


def log_device_info_async(*, max_cache_age_s: int = 7 * 24 * 3600) -> None:
    """非阻塞写入设备信息。

    - 启动时优先读取缓存并立即输出（几乎零开销）
    - 后台线程异步刷新采集结果，完成后再补一条日志
    """
    global _DEVICE_INFO_LOGGED, _DEVICE_INFO_THREAD_STARTED

    if _DEVICE_INFO_LOGGED:
        return
    _DEVICE_INFO_LOGGED = True

    cached = _read_cache()
    if isinstance(cached, dict):
        # 不严格依赖时间字段（可能缺失/旧版本缓存）
        try:
            ts = cached.get("timestamp")
            if isinstance(ts, str):
                dt = datetime.fromisoformat(ts)
                age = (datetime.now() - dt).total_seconds()
            else:
                age = 1e18
        except Exception:
            age = 1e18

        if age <= float(max_cache_age_s):
            _summarize_and_log(cached, source="缓存")
        else:
            _summarize_and_log(cached, source="缓存(过期)")

    if _DEVICE_INFO_THREAD_STARTED:
        return
    _DEVICE_INFO_THREAD_STARTED = True

    def _worker() -> None:
        try:
            info = collect_device_info()
            _write_cache(info)
            _summarize_and_log(info, source="实时")
        except Exception:
            logger.opt(exception=True).debug("[device] async collect failed")

    t = threading.Thread(target=_worker, name="device-info", daemon=True)
    t.start()
