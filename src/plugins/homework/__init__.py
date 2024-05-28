import nonebot.adapters
from nonebot import on_command
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import GroupMessageEvent

query = on_command("作业", priority=5)
state = on_command("state", priority=5)

@query.handle()
async def _(bot:Bot, event:GroupMessageEvent):
    sender = event.sender.user_id
    await query.finish("作业功能暂未开放。")

@state.handle()
async def _(bot:Bot, event:GroupMessageEvent):
    sender = event.sender.user_id
    await state.finish("作业功能暂未开放。")

