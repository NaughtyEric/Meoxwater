"""
Author: TrioxWater
Created: 2024-5-7
Description:
恶臭数字论证器（全恼）
"""

from nonebot import on_command
from nonebot.adapters import Message, Bot
from nonebot.exception import MatcherException
from nonebot.params import CommandArg
from nonebot.rule import to_me

on_homo = on_command("homo", rule=to_me, priority=5)

@on_homo.handle()
async def _(bot: Bot, message: Message=CommandArg()):
    content = message.extract_plain_text()
    try:
        x = int(content)
    except MatcherException:
        raise
    except ValueError:
        await on_homo.finish("请输入够恶臭的数字")
    except Exception as e:
        pass


