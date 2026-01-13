from __future__ import annotations

import os
import platform
import sys
from typing import Any

from loguru import logger


_AUDIO_ENV_LOGGED = False


def log_audio_environment_once(tag: str = "audio") -> None:
    """记录一次性的音频/多媒体环境信息，帮助排查“没声音”。"""
    global _AUDIO_ENV_LOGGED
    if _AUDIO_ENV_LOGGED:
        return
    _AUDIO_ENV_LOGGED = True

    try:
        from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR

        logger.debug(
            f"[{tag}] platform={platform.platform()} py={sys.version.split()[0]} qt={QT_VERSION_STR} pyqt={PYQT_VERSION_STR}"
        )
    except Exception:
        logger.debug(f"[{tag}] platform={platform.platform()} py={sys.version.split()[0]}")

    # 这些环境变量有时会影响 Qt 多媒体后端选择
    for k in (
        "QT_MEDIA_BACKEND",
        "QT_MULTIMEDIA_PREFERRED_PLUGINS",
        "QT_DEBUG_PLUGINS",
        "QT_LOGGING_RULES",
    ):
        v = os.environ.get(k)
        if v is not None:
            logger.debug(f"[{tag}] env {k}={v!r}")

    # 设备枚举：没有默认设备/设备被禁用时，常见导致“播放正常但无声”
    try:
        from PyQt6.QtMultimedia import QMediaDevices

        outputs = list(QMediaDevices.audioOutputs())
        default_out = QMediaDevices.defaultAudioOutput()

        def _desc(dev: Any) -> str:
            try:
                return str(dev.description())
            except Exception:
                return "<unknown>"

        logger.debug(f"[{tag}] audioOutputs={len(outputs)} default={_desc(default_out)}")
        # 只输出前若干个，避免日志过长
        for i, dev in enumerate(outputs[:12]):
            logger.debug(f"[{tag}] output[{i}] {_desc(dev)}")
    except Exception:
        logger.opt(exception=True).debug(f"[{tag}] failed to query audio outputs via QMediaDevices")


def _safe_str(value: Any) -> str:
    try:
        return str(value)
    except Exception:
        return "<unprintable>"


def _get_player_snapshot(player: Any) -> dict[str, Any]:
    snap: dict[str, Any] = {}

    try:
        snap["playbackState"] = int(player.playbackState())  # type: ignore[attr-defined]
    except Exception:
        pass

    try:
        snap["mediaStatus"] = int(player.mediaStatus())  # type: ignore[attr-defined]
    except Exception:
        pass

    try:
        snap["error"] = int(player.error())  # type: ignore[attr-defined]
    except Exception:
        pass

    try:
        snap["errorString"] = _safe_str(player.errorString())  # type: ignore[attr-defined]
    except Exception:
        pass

    try:
        snap["duration_ms"] = int(player.duration())  # type: ignore[attr-defined]
    except Exception:
        pass

    try:
        snap["position_ms"] = int(player.position())  # type: ignore[attr-defined]
    except Exception:
        pass

    try:
        # QMediaPlayer.source() -> QUrl
        snap["source"] = _safe_str(player.source())  # type: ignore[attr-defined]
    except Exception:
        pass

    # 音频输出（如果可拿到）：音量/静音/设备选择
    audio_out = None
    try:
        audio_out = player.audioOutput()  # type: ignore[attr-defined]
    except Exception:
        audio_out = None

    if audio_out is not None:
        try:
            snap["audio.volume"] = float(audio_out.volume())
        except Exception:
            pass
        try:
            snap["audio.muted"] = bool(audio_out.isMuted())
        except Exception:
            # 兼容不同 API
            try:
                snap["audio.muted"] = bool(audio_out.muted())
            except Exception:
                pass
        try:
            dev = audio_out.device()
            snap["audio.device"] = _safe_str(getattr(dev, "description", lambda: dev)())
        except Exception:
            pass

    return snap


def log_player_snapshot(player: Any, *, label: str = "player", reason: str = "snapshot") -> None:
    """在关键时刻输出播放器状态快照（DEBUG 级别）。"""
    try:
        snap = _get_player_snapshot(player)
        logger.debug(f"[audio] {label} {reason}: {snap}")
    except Exception:
        logger.opt(exception=True).debug(f"[audio] failed to build snapshot for {label} ({reason})")


def attach_qt_audio_debug(player: Any, *, label: str = "player") -> None:
    """给 QMediaPlayer 挂调试信号，自动记录错误/状态变化。

    目标：当用户反馈“没声音”时，从日志能看到：
    - 是否报错/报什么错
    - 媒体状态是否 invalid/buffering/stalled
    - 当前音量/静音/输出设备
    """
    log_audio_environment_once()

    # 避免重复挂载
    try:
        if getattr(player, "_audio_debug_attached", False):
            return
        setattr(player, "_audio_debug_attached", True)
    except Exception:
        # 如果对象不允许 setattr，也不要影响播放
        pass

    def _dump(reason: str) -> None:
        log_player_snapshot(player, label=label, reason=reason)

    # 初始快照
    _dump("attach")

    # QMediaPlayer 信号（尽量兼容不同 Qt/PyQt6 版本）
    try:
        if hasattr(player, "errorOccurred"):
            player.errorOccurred.connect(
                lambda *a: (logger.error(f"[audio] {label} errorOccurred args={a}"), _dump("errorOccurred"))
            )
    except Exception:
        logger.opt(exception=True).debug(f"[audio] failed to connect errorOccurred for {label}")

    try:
        if hasattr(player, "mediaStatusChanged"):
            player.mediaStatusChanged.connect(
                lambda s: (logger.debug(f"[audio] {label} mediaStatusChanged={int(s)}"), _dump("mediaStatusChanged"))
            )
    except Exception:
        logger.opt(exception=True).debug(f"[audio] failed to connect mediaStatusChanged for {label}")

    try:
        if hasattr(player, "playbackStateChanged"):
            player.playbackStateChanged.connect(
                lambda s: (
                    logger.debug(f"[audio] {label} playbackStateChanged={int(s)}"),
                    _dump("playbackStateChanged"),
                )
            )
    except Exception:
        logger.opt(exception=True).debug(f"[audio] failed to connect playbackStateChanged for {label}")

    try:
        if hasattr(player, "sourceChanged"):
            player.sourceChanged.connect(
                lambda u: (logger.debug(f"[audio] {label} sourceChanged={_safe_str(u)}"), _dump("sourceChanged"))
            )
    except Exception:
        logger.opt(exception=True).debug(f"[audio] failed to connect sourceChanged for {label}")

    # 音频输出对象的信号（如果能拿到）
    try:
        audio_out = player.audioOutput() if hasattr(player, "audioOutput") else None
    except Exception:
        audio_out = None

    if audio_out is not None:
        try:
            if hasattr(audio_out, "volumeChanged"):
                audio_out.volumeChanged.connect(
                    lambda v: logger.debug(f"[audio] {label} audioOutput.volumeChanged={float(v)}")
                )
        except Exception:
            pass
        try:
            if hasattr(audio_out, "mutedChanged"):
                audio_out.mutedChanged.connect(
                    lambda m: logger.debug(f"[audio] {label} audioOutput.mutedChanged={bool(m)}")
                )
        except Exception:
            pass
        try:
            if hasattr(audio_out, "deviceChanged"):
                audio_out.deviceChanged.connect(
                    lambda d: logger.debug(
                        f"[audio] {label} audioOutput.deviceChanged={_safe_str(getattr(d, 'description', lambda: d)())}"
                    )
                )
        except Exception:
            pass
