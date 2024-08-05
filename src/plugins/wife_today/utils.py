import hashlib
import httpx
import nonebot
from nonebot import get_driver
from .config import Config
from pathlib import Path

class WifeManager:
    def __init__(self, config: Config):
        self.cache_dir: Path = config.today_waifu_record_dir




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

def get_group_record(gid: str) -> dict:
    """
    获取群组记录字典对象
    优先从内存中获取，若内存中不存在则尝试从记录文件夹查找本地文件，若本地文件不存在则新建空文件 并返回相应对象
    """
    pass

