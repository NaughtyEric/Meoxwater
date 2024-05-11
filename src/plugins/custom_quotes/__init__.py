import json
import logging

from nonebot import get_driver, on_fullmatch, on_command
from nonebot.matcher import Matcher
from nonebot.rule import CommandArg, Message
from nonebot.log import logger

from .config import Config
from nonebot.adapters.onebot.v11 import MessageSegment, GroupMessageEvent

import os
import random
import re

global_config = get_driver().config
config = Config.parse_obj(global_config)

# 自己做着玩的要什么可拓展性啊 硬编码！

path = global_config.quote_path

caramel_event = on_fullmatch(("焦糖", "caramel"), priority=5, ignorecase=True)

submit = on_command("submit", priority=5)

@caramel_event.handle()
async def caramel(bot, event: GroupMessageEvent):
    # 群聊必须是657148784
    if event.group_id != 657148784:
        return
    if not os.path.exists(path + "/caramel"):
        await caramel_event.finish("暂无焦糖语录。")
    img_count = len(os.listdir(path + "/caramel"))
    rnd = random.randint(1, img_count)

    # 先检查是否有对应的图片，忽略后缀
    for file in os.listdir(path + "/caramel"):
        if re.match(f"{rnd}\..*", file):
            extention = file.split(".")[-1]
            if extention.lower() in ["jpg", "jpeg", "png", "gif", "bmp"]:
                await caramel_event.finish(MessageSegment.image(f"file:///{path}/caramel/{file}"))
            elif extention.lower() in ["txt"]:
                with open(f"{path}/caramel/{file}", "r") as f:
                    await caramel_event.finish(f.read())
            await caramel_event.finish(f"喵呜？第{rnd}条内容存在问题！")
    await caramel_event.finish(f"咿呀！第{rnd}条内容不存在喵！")






