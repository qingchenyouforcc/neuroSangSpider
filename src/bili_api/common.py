from bilibili_api import Credential, request_settings
from loguru import logger

from src.config import cfg


def get_credential() -> Credential:
    return Credential(
        sessdata=cfg.bili_sessdata.value,
        bili_jct=cfg.bili_jct.value,
        buvid3=cfg.bili_buvid3.value,
    )


def apply_proxy_if_enabled() -> None:
    """如果启用代理，则应用代理设置"""
    if cfg.enable_proxy.value and cfg.proxy_url.value:
        request_settings.set_proxy(cfg.proxy_url.value)
        logger.debug(f"bilibili_api 已应用代理: {cfg.proxy_url.value}")


def get_proxies() -> dict[str, str]:
    """获取代理配置字典，用于 requests 库"""
    if cfg.enable_proxy.value and cfg.proxy_url.value:
        return {
            "http": cfg.proxy_url.value,
            "https": cfg.proxy_url.value,
        }
    return {}
