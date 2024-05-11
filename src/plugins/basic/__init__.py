from nonebot import get_driver, log, Bot
from nonebot import on_keyword, on_command, on_message
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.matcher import Matcher
from nonebot.rule import to_me
from .config import Config

import re

global_config = get_driver().config
config = Config.parse_obj(global_config)
BLOCKLIST = global_config.blocklist
ADMIN = global_config.admin

# 检测是否在线
ping_checker = on_command("ping", aliases={"测试"}, rule=to_me, priority=5)
# 墨痕縩篳：测试寄气人在线性
mohen_checker = on_keyword({"墨痕", "mohen"}, priority=5)
# 阻塞：阻止不同机器人之间无限递归，也可以当成黑名单用
blocker = on_message(priority=1, block=False)
add_blocker = on_command("block", rule=to_me, priority=5)
remove_blocker = on_command("unblock", rule=to_me, priority=5)
print_blocker = on_command("blocklist", rule=to_me, priority=5)

# 启动时加载
@get_driver().on_startup
async def on_startup():
    log.logger.debug(f"阻塞名单: {BLOCKLIST}")

@get_driver().on_shutdown
async def on_shutdown():
    # TODO: 保存配置
    pass

@ping_checker.handle()
async def checker_func():
    await ping_checker.finish("pong!")

@blocker.handle()
async def _(message: MessageEvent, matcher: Matcher):
    if message.sender.user_id in BLOCKLIST:
        log.logger.debug(f"已被阻塞的消息: {message.get_plaintext()}")
        matcher.stop_propagation()
    else:
        log.logger.debug(f"未被阻塞的消息: {message.get_plaintext()}")
        matcher.skip()

@add_blocker.handle()
async def add_blocker_func(bot: Bot, message: MessageEvent):
    # 查找是否@了人
    sender = message.sender.user_id
    at_list = re.findall(r"\[CQ:at,qq=(\d+)]", message.raw_message)
    at_list = [int(at) for at in at_list if
               (int(at) != sender and int(at) not in BLOCKLIST and int(at) not in ADMIN and int(at) != int(bot.self_id))]
    if at_list:
        BLOCKLIST.extend(at_list)
        # 刷新配置
        global_config.blocklist = BLOCKLIST
        await add_blocker.finish(f"已将{str(at_list).strip('[]')}加入阻塞名单。")
    else:
        await add_blocker.finish("请@要加入阻塞名单的人。不能将自己或已被阻塞的人加入阻塞名单。")

@remove_blocker.handle()
async def remove_blocker_func(message: MessageEvent):
    # 查找是否@了人
    sender = message.sender.user_id
    at_list = re.findall(r"\[CQ:at,qq=(\d+)]", message.raw_message)
    at_list = [int(at) for at in at_list if
               (int(at) in BLOCKLIST and int(at) != sender and int(at) not in ADMIN)]
    if at_list:
        for at in at_list:
            BLOCKLIST.remove(at)
        # 刷新配置
        global_config.blocklist = BLOCKLIST
        await remove_blocker.finish(f"已将{str(at_list).strip('[]')}从阻塞名单中移除。")
    else:
        await remove_blocker.finish("请@要从阻塞名单中移除的人。不能将自己或未被阻塞的人从阻塞名单中移除。")


@print_blocker.handle()
async def print_blocker_func(bot: Bot, message: MessageEvent):
    if message.sender.user_id in ADMIN:
        # 发送到私聊
        await bot.send_private_msg(user_id=message.sender.user_id, message=f"阻塞名单: {BLOCKLIST}")
        await print_blocker.finish("已将阻塞名单发送到私聊。")
    else:
        await print_blocker.finish("你没有权限查看阻塞名单。")



@mohen_checker.handle()
async def mohen_checker_func():
    await mohen_checker.finish("墨痕縩篳！")
