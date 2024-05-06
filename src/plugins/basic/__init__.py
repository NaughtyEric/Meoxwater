from nonebot import get_driver, log
from nonebot import on_keyword, on_command, on_message
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.matcher import Matcher
from nonebot.rule import to_me
from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)
BLOCKLIST = global_config.blocklist

# 检测是否在线
ping_checker = on_command("ping", aliases={"测试"}, rule=to_me)
# 墨痕縩篳：测试寄气人在线性
mohen_checker = on_keyword({"墨痕", "mohen"})
# 阻塞：阻止不同机器人之间无限递归
blocker = on_message(priority=1)

# 启动时加载
@get_driver().on_startup
async def on_startup():
    log.logger.debug(f"阻塞名单: {BLOCKLIST}")

@ping_checker.handle()
async def checker_func():
    await ping_checker.finish("pong!")

@blocker.handle()
async def blocker_func(message: MessageEvent, matcher: Matcher):
    if message.sender.user_id in BLOCKLIST:
        matcher.stop_propagation()


@mohen_checker.handle()
async def mohen_checker_func():
    await mohen_checker.finish("墨痕縩篳！")
