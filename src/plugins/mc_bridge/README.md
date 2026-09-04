# mc_bridge

QQ 群 ↔ Minecraft 服务器消息互通（单服务器）。

链路：**MC 服务端（鹊桥 QueQiao 插件/Mod）↔ nonebot-adapter-minecraft ↔ 本插件 ↔ OneBot v11（NapCat）↔ QQ 群**

## 服务端准备

1. 给 MC 服务端装 [鹊桥 QueQiao](https://www.curseforge.com/minecraft/mc-mods/queqiao)（支持 Spigot / Fabric / Forge / NeoForge / Velocity）。
2. 编辑鹊桥 `config.yml`：
   - `server_name` 要与 `.env.*` 的 `MC_SERVER_NAME` **完全一致**；
   - `access_token` 与 `.env.*` 的 `MINECRAFT_ACCESS_TOKEN` 一致；
   - 推荐用**反向连接**：让鹊桥作为客户端连 `ws://<bot地址>:1927/minecraft/ws`
     （请求头 `x-self-name` 由鹊桥自动带上）。
3. 若改为**正向连接**（bot 主动连鹊桥），则开启鹊桥的 websocket_server，
   并在 `.env.*` 填 `MINECRAFT_WS_URLS={"服务器名": ["ws://ip:8080/minecraft/ws"]}`。

## 配置（.env.*）

| 配置项 | 说明 |
|---|---|
| `MC_SERVER_NAME` | 服务器名，需与鹊桥 `server_name` 一致 |
| `MC_GROUPS` | 互通的 QQ 群号列表，如 `[657148784]` |
| `MC_SYNC_CHAT` / `JOIN` / `QUIT` / `DEATH` / `ACHIEVEMENT` | MC → QQ 各类事件开关 |
| `MC_MSG_MAX_LENGTH` | QQ → MC 单条消息最大长度，超出截断 |

消息格式模板写在 `__init__.py` 的 `FORMATS` 里，需要改文案直接改常量。

## 命令

| 命令 | 权限 | 说明 |
|---|---|---|
| `/mc <消息>` | 互通群内所有人 | 把消息发到服务器聊天栏 |
| `/mcstatus`（别名 `/服务器`） | 互通群内所有人 | 查看在线人数与服务端版本 |
| `@bot /rcon <命令>` | SUPERUSER | 通过 RCON 在服务端执行命令 |

## 关于指令注入

`/mc` 的内容通过 `send_msg` 以**聊天文本组件**下发，不经过 RCON，服务端不会将其
当作命令执行；即便玩家发 `/mc /op xxx`，进游戏后也只是一行聊天文本。此外内容会被
去除控制字符并按 `MC_MSG_MAX_LENGTH` 截断。真正能执行命令的只有 `/rcon`，且限
SUPERUSER 并需 @ 机器人。
