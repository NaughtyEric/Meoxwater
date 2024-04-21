from nonebot import get_driver
from nonebot import on_keyword, on_command
from nonebot.rule import to_me
from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)

ping_checker = on_command("ping", aliases={"测试"}, rule=to_me)

mohen_checker = on_keyword({"墨痕", "mohen"})

configs_handler = on_keyword({"配置"}, rule=to_me())

@ping_checker.handle()
async def checker_func():
    await ping_checker.finish("pong!")

# 只接收3486660556的私聊消息
@configs_handler.handle()
async def configs_handler_func(event):
    if event.get_user_id() == '3486660556' and event.is_private():
        msg = ''
        for k, v in config.dict().items():
            msg += f'{k}: {v}\n'
        print(msg)
        await configs_handler.finish("已经发送到控制台！")
    else:
        await configs_handler.finish("你没有权限查看配置！")

@mohen_checker.handle()
async def mohen_checker_func():
    await mohen_checker.finish("墨痕縩篳！")
