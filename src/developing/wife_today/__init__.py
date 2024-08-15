from nonebot.adapters.mirai2 import GroupMessage
from .config import Config
from nonebot.adapters.mirai2.bot import Bot
from nonebot import get_driver
from nonebot import on_fullmatch
from .wife_management import GlobalManager

driver = get_driver()
global_manager = None

@driver.on_startup
async def init_global_manager(bot: Bot):
    global global_manager
    global_manager = GlobalManager(bot, Config.today_waifu_record_dir)
    pass

today_wife = on_fullmatch("今日老婆", priority=5)
@today_wife.handle()
async def today_wife_handle(bot: Bot, event: GroupMessage):
    await today_wife.finish()


