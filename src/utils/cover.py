from __future__ import annotations

from pathlib import Path
import re
from typing import Optional

from loguru import logger
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from qfluentwidgets import FluentIcon as FIF

import requests
from bilibili_api import video, sync

from src.config import CACHE_DIR, VIDEO_DIR, ASSETS_DIR, USER_AGENT, cfg
from src.core.data_io import load_from_all_data
from src.bili_api.common import get_credential


def _load_pixmap_from_file(fp: Path, size: int) -> QPixmap | None:
    try:
        if fp.exists():
            pix = QPixmap(str(fp))
            if not pix.isNull():
                return pix.scaled(size, size)
    except Exception:
        logger.exception(f"加载封面文件失败: {fp}")
    return None


def _extract_embedded_cover(audio_path: Path) -> bytes | None:
    """尽量从常见格式中提取内嵌封面。

    支持：MP3(ID3 APIC)、M4A/MP4(covr)、FLAC(pictures)。
    """
    try:
        # MP3
        try:
            from mutagen.id3 import ID3

            tags = ID3(str(audio_path))
            for key in tags.keys():
                if key.startswith("APIC"):
                    return tags[key].data
        except Exception:
            pass

        # M4A/MP4
        try:
            from mutagen.mp4 import MP4

            tags = MP4(str(audio_path)).tags
            if tags and "covr" in tags:
                covr = tags["covr"]
                if covr:
                    return bytes(covr[0])
        except Exception:
            pass

        # FLAC
        try:
            from mutagen.flac import FLAC

            f = FLAC(str(audio_path))
            if f.pictures:
                return f.pictures[0].data
        except Exception:
            pass
    except Exception:
        logger.exception(f"提取内嵌封面失败: {audio_path}")
    return None


def get_cover_pixmap(audio_path: Path, size: int = 48) -> QPixmap:
    """获取音频封面缩略图的 QPixmap。

    优先级：
    1) 缓存目录 data/cache/covers/<stem>.(jpg/png/jpeg)
    2) 音频同目录 <stem>.(jpg/png/jpeg)
    3) 内嵌封面（提取并缓存为 jpg）
    4) 默认相册图标
    """
    try:
        covers_dir = CACHE_DIR / "covers"
        covers_dir.mkdir(parents=True, exist_ok=True)

        candidates = [
            covers_dir / f"{audio_path.stem}.jpg",
            covers_dir / f"{audio_path.stem}.png",
            covers_dir / f"{audio_path.stem}.jpeg",
            audio_path.with_suffix(".jpg"),
            audio_path.with_suffix(".png"),
            audio_path.with_suffix(".jpeg"),
        ]

        for fp in candidates:
            pix = _load_pixmap_from_file(fp, size)
            if pix:
                return pix

        # 尝试从标签中提取
        data = _extract_embedded_cover(audio_path)
        if data:
            try:
                pix = QPixmap()
                if pix.loadFromData(data):
                    # 写入缓存以便下次复用
                    cache_fp = covers_dir / f"{audio_path.stem}.jpg"
                    try:
                        pix.save(str(cache_fp), "JPG")
                    except Exception:
                        logger.warning(f"封面缓存写入失败: {cache_fp}")
                    return pix.scaled(size, size)
            except Exception:
                logger.exception(f"从标签构建图片失败: {audio_path}")

        # 尝试从 B 站拉取封面
        try:
            bvid = _match_bvid_by_audio(audio_path)
            if bvid:
                img_bytes = _fetch_bilibili_cover_bytes(bvid)
                if img_bytes:
                    pix = QPixmap()
                    if pix.loadFromData(img_bytes):
                        cache_fp = covers_dir / f"{audio_path.stem}.jpg"
                        try:
                            pix.save(str(cache_fp), "JPG")
                        except Exception:
                            logger.warning(f"封面缓存写入失败: {cache_fp}")
                        return pix.scaled(size, size)
        except Exception:
            logger.exception(f"B 站封面获取失败: {audio_path}")
    except Exception:
        logger.exception(f"获取封面失败: {audio_path}")

    # 兜底默认图标：将应用主图标等比缩放并居中绘制到 size×size 画布
    return _fallback_app_icon(size)


def _fallback_app_icon(size: int) -> QPixmap:
    try:
        canvas = QPixmap(size, size)
        canvas.fill(Qt.GlobalColor.transparent)

        # 首选 main.ico，其次可扩展为 main.png
        src = None
        for name in ("main.png", "main.ico"):
            p = ASSETS_DIR / name
            if p.exists():
                src = QPixmap(str(p))
                if not src.isNull():
                    break
        if src is None or src.isNull():
            # 回退到 Fluent 内置相册图标
            return QIcon(FIF.ALBUM.path()).pixmap(size, size)

        scaled = src.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        x = int((size - scaled.width()) / 2)
        y = int((size - scaled.height()) / 2)

        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.drawPixmap(x, y, scaled)
        painter.end()
        return canvas
    except Exception:
        logger.exception("绘制兜底应用图标失败，回退到内置图标")
        return QIcon(FIF.ALBUM.path()).pixmap(size, size)


# ---------------------- Bilibili helpers ----------------------

_KEEP_CHARS = re.compile(r"[\u4e00-\u9fff\w]+", re.UNICODE)


def _normalize_text(s: str) -> str:
    s = s.lower()
    parts = _KEEP_CHARS.findall(s)
    s = "".join(parts)
    # 去掉常见后缀
    s = s.replace("fix", "")
    return s


def _match_bvid_by_audio(audio_path: Path) -> Optional[str]:
    """根据音频文件名在本地视频数据里匹配 BV 号。

    策略：归一化文件名与标题，互相包含则认为匹配，取最优（最长匹配）。
    """
    try:
        total = load_from_all_data(VIDEO_DIR)
        if not total:
            return None
        stem_norm = _normalize_text(audio_path.stem)
        if not stem_norm:
            return None
        best = (0, None)  # (score, bvid)
        for item in total.get_data():
            title = str(item.get("title", ""))
            bvid = item.get("bv")
            if not bvid:
                continue
            title_norm = _normalize_text(title)
            if not title_norm:
                continue
            score = 0
            if stem_norm in title_norm:
                score = len(stem_norm)
            elif title_norm in stem_norm:
                score = len(title_norm)
            if score > best[0]:
                best = (score, bvid)
        return best[1]
    except Exception:
        logger.exception("匹配 BV 失败")
        return None


def _fetch_bilibili_cover_bytes(bvid: str) -> Optional[bytes]:
    """通过 BVID 获取视频封面二进制数据。"""
    try:
        v = video.Video(bvid, credential=get_credential())
        info = sync(v.get_info())
        # 常见结构含 pic 或 View.pic
        cover_url = None
        if isinstance(info, dict):
            cover_url = info.get("pic")
            if not cover_url and "View" in info and isinstance(info["View"], dict):
                cover_url = info["View"].get("pic")
        if not cover_url:
            return None

        # 应用代理设置
        proxies = {}
        if cfg.enable_proxy.value and cfg.proxy_url.value:
            proxies = {
                "http": cfg.proxy_url.value,
                "https": cfg.proxy_url.value,
            }

        resp = requests.get(
            cover_url,
            timeout=8,
            headers={"User-Agent": USER_AGENT},
            proxies=proxies,
        )
        if resp.status_code == 200 and resp.content:
            return resp.content
        return None
    except Exception:
        logger.exception(f"下载封面失败: {bvid}")
        return None
