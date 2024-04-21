from nonebot import get_driver
from nonebot import on_keyword, on_command
from nonebot.rule import to_me
from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)

ping_checker = on_command("ping", aliases={"测试"}, rule=to_me)

mohen_checker = on_keyword({"墨痕", "mohen"})

@ping_checker.handle()
async def checker_func():
    await ping_checker.finish("pong!")



@mohen_checker.handle()
async def mohen_checker_func():
    await mohen_checker.finish("墨痕縩篳！")
