import json

from nonebot import get_driver, on_fullmatch

from .config import Config
from nonebot.adapters.mirai2 import MessageSegment

import os
import random
import re

global_config = get_driver().config
config = Config.parse_obj(global_config)

# 自己做着玩的要什么可拓展性啊 硬编码！

path = global_config.quote_path

caramel_event = on_fullmatch(("焦糖", "caramel"), priority=5, ignorecase=True)
caramel_said = ["捏的怎么人人都会拇指MM夕烧"]

@caramel_event.handle()
async def caramel():
    if not os.path.exists(path + "caramel"):
        await caramel_event.finish("暂无焦糖语录。")
    img_count = len(os.listdir(path + "caramel"))
    rnd = random.randint(1, img_count)
    if rnd > img_count:
        rnd -= img_count
        await caramel_event.finish(caramel_said[rnd])
    else:
        # 先检查是否有对应的图片，忽略后缀
        for file in os.listdir(path + "caramel"):
            if re.match(f"{rnd}.*", file):
                extention = file.split(".")[-1]
                if extention.lower() not in ["jpg", "jpeg", "png", "gif", "bmp"]:
                    await caramel_event.finish(f"喵呜？第{rnd}张图片存在问题！")
                await caramel_event.finish(MessageSegment.image(f"{path}/caramel/{rnd}.{extention}"))
        await caramel_event.finish(f"咿呀！图片不存在喵！")






