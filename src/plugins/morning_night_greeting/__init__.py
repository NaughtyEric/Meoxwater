from nonebot import on_command, get_driver, on_fullmatch, get_plugin_config
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.plugin import PluginMetadata
from .config import Config
import json
from functools import lru_cache
from datetime import datetime
import time

__plugin_meta__ = PluginMetadata(
    name="MorningNightGreeting",
    description="向说早安和晚安的用户问好",
    usage="早安/晚安",
    type="application",
    config=Config,
    extra={},
)

config = get_plugin_config(Config)

good_night = on_fullmatch(('晚安', '晚安啦', '晚安了', '晚安喵'), priority=5)
good_morning = on_fullmatch(('早上好', '早安', '早', '早喵'), priority=5)

@lru_cache(maxsize=1)
def load_replies(file_path=config.mngreeting_replies_filepath):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_current_period_response(category, current_time=None):
    """
    根据当前时间获取对应时间段的回复内容。

    :param category: "morning" 或 "night"
    :param current_time: 可选，用于测试或指定时间，格式为 datetime.time
    :return: 匹配到的回复字符串列表或 None
    """
    replies_dict = load_replies()
    if current_time is None:
        now = datetime.now().time()
    else:
        now = current_time
    for period, responses in replies_dict.get(category, {}).items():
        start_str, end_str = period.split('-')
        start = datetime.strptime(start_str, "%H:%M:%S").time()
        end = datetime.strptime(end_str, "%H:%M:%S").time()
        if start <= end:
            if start <= now < end:
                return responses
        else:
            if now >= start or now < end:
                return responses
    raise ValueError("No matching period found for the given time.")


_user_last_trigger_time = {}

@good_night.handle()
async def _(event: GroupMessageEvent):
    t = datetime.now().time()
    sender = event.sender.user_id
    now_timestamp = time.time()
    cooldown = config.mngreeting_cooldown
    last_time = _user_last_trigger_time.get(sender, 0)
    if now_timestamp - last_time < cooldown:
        return
    _user_last_trigger_time[sender] = now_timestamp
    try:
        responses = get_current_period_response("night", t)
        if responses:
            await good_night.finish(responses[0])
    except ValueError:
        await good_night.finish("没有匹配的晚安时间段，请联系管理员检查配置文件。")


@good_morning.handle()
async def _(event: GroupMessageEvent):
    t = datetime.now().time()
    sender = event.sender.user_id
    now_timestamp = time.time()
    cooldown = config.mngreeting_cooldown
    last_time = _user_last_trigger_time.get(sender, 0)
    if now_timestamp - last_time < cooldown:
        return
    _user_last_trigger_time[sender] = now_timestamp
    try:
        responses = get_current_period_response("morning", t)
        if responses:
            await good_morning.finish(responses[0])
    except ValueError:
        await good_morning.finish("没有匹配的早安时间段，请联系管理员检查配置文件。")

