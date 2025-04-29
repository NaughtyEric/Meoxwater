# 花里胡哨的东西想到了就加进来
import datetime
from asyncio import sleep

import nonebot.adapters
from nonebot import on_command, get_driver
from nonebot import require
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.exception import MatcherException
from nonebot.params import CommandArg

require("nonebot_plugin_apscheduler")

global_config = get_driver().config

sleep_immediately = on_command('睡觉', aliases={'sleep'}, priority=5)
silent = on_command('silent', priority=5)

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
