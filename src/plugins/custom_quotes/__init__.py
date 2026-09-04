import json
import os
import random

from nonebot import get_driver, get_plugin_config, on_command, on_message
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment
from nonebot.log import logger
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me

from .config import Config

global_config = get_driver().config
config = get_plugin_config(Config)

# 素材根目录，Config 已保证以 / 结尾
path = config.quote_path

IMAGE_EXTS = {"jpg", "jpeg", "png", "gif", "bmp", "webp"}

# 触发词(小写) -> 词条 dict，词条结构见 assets/custom_quotes/quotes.json
_trigger_map: dict = {}


def load_quotes() -> int:
    """从 JSON 配置加载触发词表，返回词条数量。"""
    global _trigger_map
    with open(config.quote_config_filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    trigger_map = {}
    for entry in data.get("quotes", []):
        for trigger in entry.get("triggers", []):
            trigger_map[trigger.lower()] = entry
    _trigger_map = trigger_map
    return len(data.get("quotes", []))


try:
    load_quotes()
except (OSError, json.JSONDecodeError) as e:
    logger.warning(f"custom_quotes 配置加载失败，插件将不响应任何触发词: {e}")


def _match_entry(event: GroupMessageEvent):
    entry = _trigger_map.get(event.get_plaintext().strip().lower())
    if entry is None:
        return None
    groups = entry.get("groups")
    if groups and event.group_id not in groups:
        return None
    return entry


async def _quote_rule(event: GroupMessageEvent) -> bool:
    return _match_entry(event) is not None


quote_matcher = on_message(rule=_quote_rule, priority=10)
reload_quotes = on_command(
    "reload_quotes", aliases={"重载语录"}, rule=to_me(), permission=SUPERUSER, priority=5
)


@quote_matcher.handle()
async def _(event: GroupMessageEvent):
    entry = _match_entry(event)
    if entry is None:
        return
    # 候选池 = JSON 里的文本回复 + 素材目录下的文件，等概率抽取
    pool = [("text", reply) for reply in entry.get("replies", [])]
    sub_dir = entry.get("dir", "").strip("/")
    if sub_dir:
        dir_path = f"{path}{sub_dir}"
        if os.path.isdir(dir_path):
            pool += [("file", f"{dir_path}/{f}") for f in os.listdir(dir_path)]
    if not pool:
        await quote_matcher.finish("喵呜？内容不存在喵！")
    kind, value = random.choice(pool)
    if kind == "text":
        await quote_matcher.finish(value)
    ext = value.rsplit(".", 1)[-1].lower()
    if ext in IMAGE_EXTS:
        await quote_matcher.finish(MessageSegment.image(f"file:///{value}"))
    if ext == "txt":
        with open(value, "r", encoding="utf-8") as f:
            await quote_matcher.finish(f.read().strip("\n"))
    await quote_matcher.finish("喵呜？内容存在问题！")


@reload_quotes.handle()
async def _():
    try:
        count = load_quotes()
    except (OSError, json.JSONDecodeError) as e:
        await reload_quotes.finish(f"重载失败喵：{e}")
    await reload_quotes.finish(f"已重载 {count} 个语录词条喵！")
