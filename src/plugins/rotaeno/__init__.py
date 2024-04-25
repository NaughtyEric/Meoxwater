from nonebot import get_driver

from .config import Config

driver = get_driver()

global_config = get_driver().config
config = Config.parse_obj(global_config)


@driver.on_startup
async def load_music():
    pass