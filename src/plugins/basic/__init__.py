from nonebot import get_driver, log
from nonebot import on_keyword, on_command, on_message
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.matcher import Matcher
from nonebot.rule import to_me
from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)
WHITELIST = global_config.whitelist

ping_checker = on_command("ping", aliases={"测试"}, rule=to_me)

mohen_checker = on_keyword({"墨痕", "mohen"})

# blocker = on_message(priority=100)

# 启动时加载
@get_driver().on_startup
async def on_startup():
    log.logger.debug(f"白名单: {WHITELIST}")

@ping_checker.handle()
async def checker_func():
    await ping_checker.finish("pong!")

# @blocker.handle()
# async def blocker_func(message: MessageEvent, matcher: Matcher):
#     if message.sender.user_id in WHITELIST:
#         matcher.stop_propagation()


@mohen_checker.handle()
async def mohen_checker_func():
    await mohen_checker.finish("墨痕縩篳！")
