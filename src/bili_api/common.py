from bilibili_api import Credential

from src.config import cfg


def get_credential() -> Credential:
    return Credential(
        sessdata=cfg.bili_sessdata.value,
        bili_jct=cfg.bili_jct.value,
        buvid3=cfg.bili_buvid3.value,
    )
