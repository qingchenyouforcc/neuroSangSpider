def av2bv(x: int) -> str:
    """av to bv"""
    alphabet = "fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF"
    x = (x ^ 0x0A93_B324) + 0x2_0840_07C0
    r = list("BV1**4*1*7**")
    for v in [11, 10, 3, 8, 4, 6]:
        x, d = divmod(x, 58)
        r[v] = alphabet[d]
    return "".join(r)


def bv2av(x: str) -> int:
    """bv to av"""
    alphabet = "fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF"
    r = 0
    for i, v in enumerate([11, 10, 3, 8, 4, 6]):
        r += alphabet.find(x[v]) * 58**i
    return (r - 0x2_0840_07C0) ^ 0x0A93_B324


def url2bv(url: str) -> str:
    """bv to url"""
    if "?" in url:
        url = url.split("?")[0]
    url = url[::-1][:14][::-1]
    url = url.replace("/", "")
    url = url.replace("\n", "", 1)
    return url
