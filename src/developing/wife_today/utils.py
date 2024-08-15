import hashlib

import httpx


def remove_a_pair(d: dict, key: int):
    """
    从dict中移除相对应的一对。即：若成功移除了key->val，则同时移除val->key。
    """
    if key in d.keys():
        val = d[key]
        d.pop(key)
        d.pop(val)


"""
来源：nonebot_plugin_today_waifu
"""
async def download_avatar(uid: str) -> bytes:
    """
    根据 qq号 获取头像
    """
    url = f"http://q1.qlogo.cn/g?b=qq&nk={uid}&s=640"
    data = await download_url(url)
    if not data or hashlib.md5(data).hexdigest() == "acef72340ac0e914090bd35799f5594e":
        url = f"http://q1.qlogo.cn/g?b=qq&nk={uid}&s=100"
        data = await download_url(url)
    return data


async def download_url(url: str) -> bytes:
    async with httpx.AsyncClient() as client:
        for i in range(3):
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    continue
                return resp.content
            except Exception as e:
                print(f"Error downloading {url}, retry {i}/3: {str(e)}")