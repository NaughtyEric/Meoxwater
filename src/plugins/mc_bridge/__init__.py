import json
import re

from nonebot import (
    get_bot,
    get_bots,
    get_plugin_config,
    on_command,
    on_message,
    on_notice,
)
from nonebot.adapters.minecraft import (
    Bot as MCBot,
    MessageSegment as MCSegment,
    PlayerAchievementEvent,
    PlayerChatEvent,
    PlayerDeathEvent,
    PlayerJoinEvent,
    PlayerQuitEvent,
)
from nonebot.adapters.onebot.v11 import (
    Bot as QQBot,
    GroupMessageEvent,
    Message,
    MessageEvent,
)
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me

from .config import Config

config = get_plugin_config(Config)

DEFAULT_FORMATS = {
    "chat": "[{server}] <{player}> {message}",
    "join": "[{server}] {player} 加入了游戏",
    "quit": "[{server}] {player} 离开了游戏",
    "death": "[{server}] {message}",
    "achievement": "[{server}] {player} 达成了进度 [{message}]",
    "qq_to_mc": "[QQ] <{sender}> {message}",
}
SYNC_KINDS = ("chat", "join", "quit", "death", "achievement")

# server_name -> 词条 dict，词条结构见 assets/mc_bridge/servers.json
_server_map: dict = {}
# QQ 群号 -> [server_name, ...]，仅包含开启了 qq_to_mc 的服务器
_qq_to_mc_group_map: dict = {}


def load_servers() -> int:
    """从 JSON 配置加载服务器互通表，返回服务器数量。"""
    global _server_map, _qq_to_mc_group_map
    with open(config.mc_bridge_config_filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    server_map = {}
    group_map: dict = {}
    for entry in data.get("servers", []):
        name = entry.get("server_name")
        if not name:
            continue
        entry.setdefault("groups", [])
        entry.setdefault("mc_to_qq", {})
        entry.setdefault("qq_to_mc", True)
        entry.setdefault("allow_command", False)
        entry.setdefault("formats", {})
        for kind in SYNC_KINDS:
            entry["mc_to_qq"].setdefault(kind, True)
        server_map[name] = entry
        if entry["qq_to_mc"]:
            for group_id in entry["groups"]:
                group_map.setdefault(group_id, []).append(name)
    _server_map, _qq_to_mc_group_map = server_map, group_map
    return len(server_map)


try:
    load_servers()
except (OSError, json.JSONDecodeError) as e:
    logger.warning(f"mc_bridge: 配置加载失败，互通功能不会生效: {e}")


def _fmt(entry: dict, key: str, **kwargs) -> str:
    template = entry.get("formats", {}).get(key) or DEFAULT_FORMATS[key]
    return template.format(**kwargs)


def _render_translate(node) -> str:
    """把 Minecraft 文本组件（死亡/进度信息）渲染成纯文本。"""
    if node is None:
        return ""
    if getattr(node, "text", None):
        return node.text
    parts = [_render_translate(arg) for arg in (getattr(node, "args", None) or [])]
    key = getattr(node, "key", None) or ""
    # 没有服务端译文时退化为「翻译键 + 参数」，至少不丢信息
    return f"{key} {' '.join(p for p in parts if p)}".strip()


def _get_qq_bot() -> QQBot | None:
    for bot in get_bots().values():
        if isinstance(bot, QQBot):
            return bot
    return None


async def _notify_groups(entry: dict, text: str) -> None:
    qq_bot = _get_qq_bot()
    if qq_bot is None:
        logger.warning("mc_bridge: 没有已连接的 QQ Bot，消息已丢弃")
        return
    for group_id in entry.get("groups", []):
        try:
            await qq_bot.send_group_msg(group_id=group_id, message=text)
        except Exception as e:
            logger.warning(f"mc_bridge: 转发到群 {group_id} 失败: {e}")


async def _to_qq(event, kind: str, message: str = "") -> None:
    """把 MC 侧事件转发到该服务器绑定的所有 QQ 群。"""
    entry = _server_map.get(event.server_name)
    if entry is None or not entry["mc_to_qq"].get(kind, False):
        return
    text = _fmt(entry, kind, server=event.server_name, player=event.player.nickname, message=message)
    await _notify_groups(entry, text)


# ---------- MC -> QQ ----------

mc_chat = on_message(priority=10, block=False)
# 加入/退出/死亡/进度在适配器里是 notice 类事件
mc_join = on_notice(priority=10, block=False)
mc_quit = on_notice(priority=10, block=False)
mc_death = on_notice(priority=10, block=False)
mc_achievement = on_notice(priority=10, block=False)


@mc_chat.handle()
async def _(event: PlayerChatEvent):
    await _to_qq(event, "chat", event.message.extract_plain_text().strip())


@mc_join.handle()
async def _(event: PlayerJoinEvent):
    await _to_qq(event, "join")


@mc_quit.handle()
async def _(event: PlayerQuitEvent):
    await _to_qq(event, "quit")


@mc_death.handle()
async def _(event: PlayerDeathEvent):
    await _to_qq(event, "death", _render_translate(event.death))


@mc_achievement.handle()
async def _(event: PlayerAchievementEvent):
    achievement = event.achievement
    display = getattr(achievement, "display", None)
    title = _render_translate(getattr(display, "title", None)) if display else ""
    await _to_qq(event, "achievement", title or (achievement.key or ""))


# ---------- QQ -> MC ----------

# 控制字符会破坏聊天组件结构，一律替换为空格
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def _sanitize(text: str) -> str:
    text = _CONTROL_CHARS.sub(" ", text).strip()
    if len(text) > config.mc_msg_max_length:
        text = text[: config.mc_msg_max_length] + "…"
    return text


def _servers_in_group(group_id: int) -> list[str]:
    """某个群绑定的全部服务器（不限 qq_to_mc 开关，用于 /mcstatus 等查询类命令）。"""
    return [
        name
        for name, entry in _server_map.items()
        if group_id in entry.get("groups", [])
    ]


async def _in_bound_group(event: GroupMessageEvent) -> bool:
    return event.group_id in _qq_to_mc_group_map


mc_say = on_command("mc", rule=_in_bound_group, priority=5, block=True)
mc_status = on_command(
    "mcstatus", aliases={"服务器"}, rule=_in_bound_group, priority=5, block=True
)


@mc_say.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    text = _sanitize(args.extract_plain_text())
    if not text:
        await mc_say.finish("用法：/mc <要发到服务器的消息>")
    sender = event.sender.card or event.sender.nickname or str(event.sender.user_id)
    sent = []
    for server_name in _qq_to_mc_group_map.get(event.group_id, []):
        entry = _server_map[server_name]
        try:
            mc_bot = get_bot(server_name)
        except KeyError:
            continue
        if not isinstance(mc_bot, MCBot):
            continue
        # 作为聊天文本组件下发（而非 RCON 命令），内容不会被服务端当作指令执行
        try:
            await mc_bot.send_msg(
                MCSegment.text(_fmt(entry, "qq_to_mc", sender=sender, message=text))
            )
            sent.append(server_name)
        except Exception as e:
            logger.warning(f"mc_bridge: 发送到服务器 {server_name} 失败: {e}")
    if sent:
        await mc_say.finish(f"已发送到 {'、'.join(sent)} 喵！")
    await mc_say.finish("没有已连接的服务器，发送失败喵。")


@mc_status.handle()
async def _(event: GroupMessageEvent):
    names = _servers_in_group(event.group_id)
    if not names:
        await mc_status.finish("本群没有绑定任何服务器喵。")
    lines = []
    for server_name in names:
        try:
            mc_bot = get_bot(server_name)
            status = await mc_bot.get_status()
        except KeyError:
            lines.append(f"{server_name}: 未连接")
            continue
        except Exception as e:
            lines.append(f"{server_name}: 查询失败（{e}）")
            continue
        players = status.server_list_ping.players
        if players is None:
            lines.append(f"{server_name}: 已连接（无在线人数信息）")
        else:
            lines.append(
                f"{server_name}: 在线 {players.online}/{players.max} | {status.server_version}"
            )
    await mc_status.finish("\n".join(lines))


# ---------- 管理命令 ----------

mc_rcon = on_command("rcon", rule=to_me(), priority=5)
reload_servers = on_command(
    "reload_mc", aliases={"重载互通"}, rule=to_me(), permission=SUPERUSER, priority=5
)


@mc_rcon.handle()
async def _(bot: QQBot, event: MessageEvent, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    server_name, _, command = text.partition(" ")
    command = command.strip()
    if not server_name or not command:
        await mc_rcon.finish("用法：/rcon <服务器名> <命令>")
    entry = _server_map.get(server_name)
    if entry is None:
        await mc_rcon.finish(f"未知服务器：{server_name}")

    is_superuser = await SUPERUSER(bot, event)
    if not is_superuser:
        in_bound_group = (
            isinstance(event, GroupMessageEvent)
            and event.group_id in entry.get("groups", [])
        )
        if not in_bound_group:
            await mc_rcon.finish("你没有权限对这个服务器执行指令喵。")
        if not entry.get("allow_command", False):
            await mc_rcon.finish("该服务器未开启指令权限，仅管理员可用喵。")

    try:
        mc_bot = get_bot(server_name)
        result = await mc_bot.send_rcon_command(command)
    except KeyError:
        await mc_rcon.finish(f"服务器 {server_name} 未连接。")
    except Exception as e:
        await mc_rcon.finish(f"执行失败：{e}")
    await mc_rcon.finish(result or "（无输出）")


@reload_servers.handle()
async def _():
    try:
        count = load_servers()
    except (OSError, json.JSONDecodeError) as e:
        await reload_servers.finish(f"重载失败喵：{e}")
    await reload_servers.finish(f"已重载 {count} 个服务器配置喵！")
