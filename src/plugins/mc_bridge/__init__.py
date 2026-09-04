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
from nonebot.adapters.onebot.v11 import Bot as QQBot, GroupMessageEvent, Message
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me

from .config import Config

config = get_plugin_config(Config)

SERVER = config.mc_server_name
GROUPS = config.mc_groups

FORMATS = {
    "chat": "[MC] <{player}> {message}",
    "join": "[MC] {player} 加入了游戏",
    "quit": "[MC] {player} 离开了游戏",
    "death": "[MC] {message}",
    "achievement": "[MC] {player} 达成了进度 [{message}]",
    "qq_to_mc": "[QQ] <{sender}> {message}",
}

if not SERVER:
    logger.warning("mc_bridge: 未配置 MC_SERVER_NAME，互通功能不会生效")


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


async def _to_qq(event, kind: str, enabled: bool, message: str = "") -> None:
    """把 MC 侧事件转发到配置的 QQ 群。"""
    if not enabled or event.server_name != SERVER:
        return
    qq_bot = _get_qq_bot()
    if qq_bot is None:
        logger.warning("mc_bridge: 没有已连接的 QQ Bot，事件已丢弃")
        return
    text = FORMATS[kind].format(player=event.player.nickname, message=message)
    for group_id in GROUPS:
        try:
            await qq_bot.send_group_msg(group_id=group_id, message=text)
        except Exception as e:
            logger.warning(f"mc_bridge: 转发到群 {group_id} 失败: {e}")


# ---------- MC -> QQ ----------

mc_chat = on_message(priority=10, block=False)
# 加入/退出/死亡/进度在适配器里是 notice 类事件
mc_join = on_notice(priority=10, block=False)
mc_quit = on_notice(priority=10, block=False)
mc_death = on_notice(priority=10, block=False)
mc_achievement = on_notice(priority=10, block=False)


@mc_chat.handle()
async def _(event: PlayerChatEvent):
    await _to_qq(
        event, "chat", config.mc_sync_chat, event.message.extract_plain_text().strip()
    )


@mc_join.handle()
async def _(event: PlayerJoinEvent):
    await _to_qq(event, "join", config.mc_sync_join)


@mc_quit.handle()
async def _(event: PlayerQuitEvent):
    await _to_qq(event, "quit", config.mc_sync_quit)


@mc_death.handle()
async def _(event: PlayerDeathEvent):
    await _to_qq(
        event, "death", config.mc_sync_death, _render_translate(event.death)
    )


@mc_achievement.handle()
async def _(event: PlayerAchievementEvent):
    achievement = event.achievement
    display = getattr(achievement, "display", None)
    title = _render_translate(getattr(display, "title", None)) if display else ""
    await _to_qq(
        event,
        "achievement",
        config.mc_sync_achievement,
        title or (achievement.key or ""),
    )


# ---------- QQ -> MC ----------

# 控制字符会破坏聊天组件结构，一律替换为空格
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def _sanitize(text: str) -> str:
    text = _CONTROL_CHARS.sub(" ", text).strip()
    if len(text) > config.mc_msg_max_length:
        text = text[: config.mc_msg_max_length] + "…"
    return text


async def _in_bound_group(event: GroupMessageEvent) -> bool:
    return event.group_id in GROUPS


mc_say = on_command("mc", rule=_in_bound_group, priority=5, block=True)
mc_status = on_command(
    "mcstatus", aliases={"服务器"}, rule=_in_bound_group, priority=5, block=True
)


@mc_say.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    text = _sanitize(args.extract_plain_text())
    if not text:
        await mc_say.finish("用法：/mc <要发到服务器的消息>")
    if not SERVER:
        await mc_say.finish("尚未配置互通服务器喵。")
    try:
        mc_bot = get_bot(SERVER)
    except KeyError:
        await mc_say.finish("服务器未连接喵。")
    if not isinstance(mc_bot, MCBot):
        await mc_say.finish("服务器未连接喵。")
    sender = event.sender.card or event.sender.nickname or str(event.sender.user_id)
    # 作为聊天文本组件下发（而非 RCON 命令），内容不会被服务端当作指令执行
    try:
        await mc_bot.send_msg(
            MCSegment.text(FORMATS["qq_to_mc"].format(sender=sender, message=text))
        )
    except Exception as e:
        logger.warning(f"mc_bridge: 发送到服务器失败: {e}")
        await mc_say.finish("发送失败喵。")
    await mc_say.finish("已发送喵！")


@mc_status.handle()
async def _():
    if not SERVER:
        await mc_status.finish("尚未配置互通服务器喵。")
    try:
        mc_bot = get_bot(SERVER)
        status = await mc_bot.get_status()
    except KeyError:
        await mc_status.finish(f"{SERVER}: 未连接")
    except Exception as e:
        await mc_status.finish(f"{SERVER}: 查询失败（{e}）")
    players = status.server_list_ping.players
    if players is None:
        await mc_status.finish(f"{SERVER}: 已连接（无在线人数信息）")
    await mc_status.finish(
        f"{SERVER}: 在线 {players.online}/{players.max} | {status.server_version}"
    )


# ---------- 管理命令 ----------

mc_rcon = on_command("rcon", rule=to_me(), permission=SUPERUSER, priority=5)


@mc_rcon.handle()
async def _(args: Message = CommandArg()):
    command = args.extract_plain_text().strip()
    if not command:
        await mc_rcon.finish("用法：/rcon <命令>")
    if not SERVER:
        await mc_rcon.finish("尚未配置互通服务器喵。")
    try:
        mc_bot = get_bot(SERVER)
        result = await mc_bot.send_rcon_command(command)
    except KeyError:
        await mc_rcon.finish("服务器未连接喵。")
    except Exception as e:
        await mc_rcon.finish(f"执行失败：{e}")
    await mc_rcon.finish(result or "（无输出）")
