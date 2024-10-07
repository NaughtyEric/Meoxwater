# 花里胡哨的东西想到了就加进来
import logging
from asyncio import sleep
from random import random, sample

import nonebot.adapters
from nonebot import on_keyword, on_command, get_driver, on_fullmatch
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, PokeNotifyEvent
from nonebot.exception import MatcherException
from nonebot.params import CommandArg
import time
import datetime

from nonebot import require

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

global_config = get_driver().config

good_night = on_fullmatch(('晚安', '晚安啦', '晚安了'), priority=5)
good_morning = on_fullmatch(('早上好', '早安', '早'), priority=5)
sleep_immediately = on_command('睡觉', aliases={'sleep'}, priority=5)
silent = on_command('silent', priority=5)
# repeater = on_message(priority=10)
# poke_poke = on_metaevent(block=True, priority=5)
IGNORE = []


def add_ignore(user_id: int):
    IGNORE.append((user_id, time.time()))


def remove_ignore():
    # CD 5分钟
    for i in range(len(IGNORE)):
        if time.time() - IGNORE[i][1] >= 300:
            IGNORE.pop(i)
            break


GOOD_NIGHT_WORDS = [
    ['晚安喵，愿你的梦境不受梦魇侵扰~', '晚安喵，做个好梦~', '快去睡觉吧，喵喵'],
    ['把细碎的烦恼暂时关掉，把月亮挂好睡个好觉。虽然已经夜深人静，还是要祝你做个好梦喵~', '唔……已经这么晚了喵，快睡觉吧，晚安喵喵~',
     '（打呵欠）好晚了呃啊……晚安喵……（睡着）'],
    ['啊……呃……晚安喵？', '（猫娘没有回复，也许她并不能理解为什么有人要现在和她说晚安？）', '（不可置信地看表，发出困惑的喵喵声）']
]
GOOD_MOENING_WORDS = [
    ['起きて📢起きて📢起きて📢起きて📢起きて📢起きて📢起きて📢起きて📢起きて📢起きて📢起きて'
     '📢起きて📢起きて📢起きて📢起きて📢起きて📢起きて📢起きて📢起きて📢', '早上好，新的一天也要活力满满喵~', '早上好，新的一天开始了喵~'],
    ['（戳表）这都几点了喵！还在早安？起床，起床喵！', '（嫌弃脸）你这个懒猫，起床啦！（掀被子）', '起床！起床！（拍拍）'],
    ['早上好……喵？（陷入思考）（死机）', '（猫娘没有回复，也许她并不能理解为什么有人要现在和她说早上好？）', '（不可置信地看表，发出困惑的喵喵声）']
]


@good_night.handle()
async def _(bot, event: GroupMessageEvent):
    t = time.localtime()
    sender = event.sender.user_id
    remove_ignore()
    # 屏蔽模块：阻止bot对单一用户的重复回复
    if sender in [i[0] for i in IGNORE]:
        return
    add_ignore(sender)
    global GOOD_NIGHT_WORDS
    # 如果是在晚上八点到十二点之间，就回复晚安
    if 20 <= t.tm_hour < 24:
        await good_night.finish(sample(GOOD_NIGHT_WORDS[0], 1)[0])
    # 如果是在凌晨0点到5点之间，就回复晚安
    elif 0 <= t.tm_hour < 5:
        await good_night.finish(sample(GOOD_NIGHT_WORDS[1], 1)[0])
    else:
        await good_night.finish(sample(GOOD_NIGHT_WORDS[2], 1)[0])


@good_morning.handle()
async def _(bot, event: GroupMessageEvent):
    t = time.localtime()
    sender = event.sender.user_id
    remove_ignore()
    if sender in [i[0] for i in IGNORE]:
        return
    add_ignore(sender)
    global GOOD_MOENING_WORDS
    if 5 <= t.tm_hour < 10:
        await good_morning.finish(sample(GOOD_MOENING_WORDS[0], 1)[0])
    elif 10 <= t.tm_hour < 17:
        await good_morning.finish(sample(GOOD_MOENING_WORDS[1], 1)[0])
    else:
        await good_morning.finish(sample(GOOD_MOENING_WORDS[2], 1)[0])


@sleep_immediately.handle()
async def _(bot: Bot, event, message: nonebot.adapters.Message = CommandArg()):
    WHITELIST = global_config.whitelist
    if isinstance(event, GroupMessageEvent):
        sender = event.sender.user_id
        if sender in WHITELIST:
            await sleep_immediately.finish('好的，晚安~')
        else:
            msg = message.extract_plain_text()
            try:
                time_length = float(msg)
                if time_length <= 0:
                    await sleep_immediately.finish('睡觉时长必须大于0。')
                # 转换为秒
                scd = int(time_length * 3600)
                await bot.set_group_ban(group_id=event.group_id, user_id=event.sender.user_id, duration=scd)
                current_time = datetime.datetime.now()
                sleep_time = current_time + datetime.timedelta(seconds=scd)
                await sleep_immediately.finish(f'好的，晚安喵~\n你的起床时间是{sleep_time.strftime("%Y-%m-%d %H:%M:%S")}'
                                               f'，到时候再来水群吧')
            except ValueError:
                await sleep_immediately.finish('请指定睡觉时长。')
            except MatcherException:
                raise
            except Exception as e:
                await sleep_immediately.finish(f'好的，晚安喵~\nTips: /sleep <时长>获取深度睡眠。')


# @poke_poke.handle()
# async def _(bot: Bot, event: NudgeEvent):
#     sender = event.from_id
#     nonebot.logger.debug(f"poke_poke: {event.target}")
#     if sender != event.target and event.target == int(bot.self_id):
#         await poke_poke.finish(Message([MessageSegment(MessageSegment.type.POKE, {"qq": sender})]))
#     else:
#         await poke_poke.finish()

@silent.handle()
async def _(bot: Bot, event, message: nonebot.adapters.Message = CommandArg()):
    WHITELIST = global_config.whitelist
    if isinstance(event, GroupMessageEvent):
        sender = event.sender.user_id
        if sender in WHITELIST:
            msg = message.extract_plain_text()
            try:
                time_length = float(msg)
                if time_length <= 0:
                    await silent.finish('禁言时长必须大于0。')
                # 转换为秒
                scd = int(time_length * 60)
                await bot.set_group_whole_ban(group_id=event.group_id, enable=True)
                await sleep(scd)
                await bot.set_group_whole_ban(group_id=event.group_id, enable=False)
            except ValueError:
                await silent.finish('请指定禁言时长。')
        else:
            await silent.finish('你没有权限使用此命令。')
