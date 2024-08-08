# 花里胡哨的东西想到了就加进来
import logging
from random import random

import nonebot.adapters
from nonebot import on_keyword, on_command, get_driver, on_fullmatch
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, PokeNotifyEvent
from nonebot.exception import MatcherException
from nonebot.params import CommandArg
import time
import datetime

global_config = get_driver().config

good_night = on_fullmatch(('晚安', '晚安啦', '晚安了'), priority=5)
good_morning = on_fullmatch(('早上好', '早安', '早'), priority=5)
sleep_immediately = on_command('睡觉', aliases={'sleep'}, priority=5)
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


@good_night.handle()
async def _(bot, event: GroupMessageEvent):
    t = time.localtime()
    sender = event.sender.user_id
    remove_ignore()
    # 屏蔽模块：阻止bot对单一用户的重复回复
    if sender in [i[0] for i in IGNORE]:
        return
    add_ignore(sender)
    # 如果是在晚上十点到十二点之间，就回复晚安
    if 22 <= t.tm_hour < 24:
        await good_night.finish('晚安喵，愿你的梦境不受梦魇侵扰~')
    # 如果是在凌晨0点到6点之间，就回复晚安
    elif 0 <= t.tm_hour < 6:
        await good_night.finish('把细碎的烦恼暂时关掉，把月亮挂好睡个好觉。虽然已经夜深人静，还是要祝你做个好梦喵~')
    else:
        await good_night.finish('啊……呃，晚安……喵？')

@good_morning.handle()
async def _(bot, event: GroupMessageEvent):
    t = time.localtime()
    sender = event.sender.user_id
    remove_ignore()
    if sender in [i[0] for i in IGNORE]:
        return
    add_ignore(sender)
    if 5 <= t.tm_hour < 10:
        await good_morning.finish('早上好，新的一天也要活力满满喵~')
    elif 10 <= t.tm_hour < 17:
        if random() < 0.2:
            await good_morning.finish('起きて📢起きて📢起きて📢起きて📢起きて📢起きて📢起きて📢起きて📢起きて📢起きて📢起きて📢'
                                      '起きて📢起きて📢起きて📢起きて📢起きて📢起きて📢起きて📢起きて📢')
        await good_morning.finish('（戳表）这都几点了喵！还在早安？起床，起床喵！')
    else:
        await good_morning.finish('早上好……喵？（陷入思考）（死机）')


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
