from bilibili_api import Credential
# from bilibili_api.clients.CurlCFFIClient import CurlCFFIClient as CurlCFFIClient

from common.config import cfg


def get_credential() -> Credential:
    return Credential(
        sessdata=cfg.bili_sessdata.value,
        bili_jct=cfg.bili_jct.value,
        buvid3=cfg.bili_buvid3.value,
    )
