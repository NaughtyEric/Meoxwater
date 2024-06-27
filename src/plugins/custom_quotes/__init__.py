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

caramel_event = on_fullmatch(("焦糖", "caramel"), priority=10, ignorecase=True)
fb_event = on_fullmatch("发病", priority=10, ignorecase=True)
trioxwater_event = on_fullmatch(("三氧水", "trioxwater", "三氧", "三氧猫"), priority=10, ignorecase=True)

# submit = on_command("submit", priority=5)

def common(group_id, sub_path: str, event: GroupMessageEvent):
    if event.group_id != group_id:
        return
    if not os.path.exists(path + sub_path):
        raise FileNotFoundError(f"没有找到对应的文件内容。")
    msg_count = len(os.listdir(path + sub_path))
    dir_list = os.listdir(path + sub_path)
    file = dir_list[random.randint(0, msg_count - 1)]
    logger.debug(f"file: {file}")
    return file, file.split(".")[-1]

@caramel_event.handle()
async def caramel(bot, event: GroupMessageEvent):
    # 群聊必须是657148784
    try:
        file, ext = common(657148784, "/caramel", event)
    except:
        await caramel_event.finish("喵呜？内容不存在喵！")
    else:
        if ext.lower() in ["jpg", "jpeg", "png", "gif", "bmp"]:
            await caramel_event.finish(MessageSegment.image(f"file:///{path}/caramel/{file}"))
        elif ext.lower() in ["txt"]:
            with open(f"{path}/caramel/{file}", "r") as f:
                await caramel_event.finish(f.read().strip('\n'))
        await caramel_event.finish("喵呜？内容存在问题！")


@fb_event.handle()
async def fb(bot, event: GroupMessageEvent):
    try:
        file, ext = common(657148784, "/fb", event)
    except:
        await fb_event.finish("喵呜？内容不存在喵！")
    else:
        if ext.lower() in ["jpg", "jpeg", "png", "gif", "bmp"]:
            await fb_event.finish(MessageSegment.image(f"file:///{path}/fb/{file}"))
        elif ext.lower() in ["txt"]:
            with open(f"{path}/fb/{file}", "r") as f:
                await fb_event.finish(f.read().strip('\n'))
        await fb_event.finish("喵呜？内容存在问题！")

@trioxwater_event.handle()
async def trioxwater(bot, event: GroupMessageEvent):
    try:
        file, ext = common(657148784, "/trioxwater", event)
    except:
        await trioxwater_event.finish("喵呜？内容不存在喵！")
    else:
        if ext.lower() in ["jpg", "jpeg", "png", "gif", "bmp"]:
            await trioxwater_event.finish(MessageSegment.image(f"file:///{path}/trioxwater/{file}"))
        elif ext.lower() in ["txt"]:
            with open(f"{path}/trioxwater/{file}", "r") as f:
                await trioxwater_event.finish(f.read().strip('\n'))
        await trioxwater_event.finish("喵呜？内容存在问题！")
