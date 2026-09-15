# mc_bridge

QQ 群 ↔ Minecraft 服务器消息互通，支持同时对接多个服务器，每个服务器分别绑定到
指定的群聊。

链路：**MC 服务端（鹊桥 QueQiao 插件/Mod）↔ nonebot-adapter-minecraft ↔ 本插件 ↔ OneBot v11（NapCat）↔ QQ 群**

## 服务端准备

每个要互通的服务器都装一份 [鹊桥 QueQiao](https://www.curseforge.com/minecraft/mc-mods/queqiao)
（支持 Spigot / Fabric / Forge / NeoForge / Velocity），编辑其 `config.yml`：

- `server_name` 要和下面 `servers.json` 里该服务器条目的 `server_name` **完全一致**，
  多个服务器分别起不同的名字；
- `access_token` 与 `.env.*` 的 `MINECRAFT_ACCESS_TOKEN` 一致（多个服务器可以共用
  同一个 token，也可以给每个服务器单独配置，取决于鹊桥版本支持）；
- 推荐用**反向连接**：让鹊桥作为客户端连 `ws://<bot地址>:1927/minecraft/ws`
  （请求头 `x-self-name` 由鹊桥自动带上，就是靠这个区分不同服务器）。

若改为**正向连接**（bot 主动连鹊桥），在 `.env.*` 里给每个服务器名配一条 URL：
`MINECRAFT_WS_URLS={"服务器名A": ["ws://ip1:8080/minecraft/ws"], "服务器名B": [...]}`。

## 配置：assets/mc_bridge/servers.json

```json
{
  "servers": [
    {
      "server_name": "survival",
      "groups": [657148784],
      "mc_to_qq": { "chat": true, "join": true, "quit": true,
                    "death": true, "achievement": true },
      "qq_to_mc": true,
      "allow_command": false,
      "formats": { "chat": "[{server}] <{player}> {message}" }
    },
    {
      "server_name": "creative",
      "groups": [657148784, 111222333],
      "allow_command": true
    }
  ]
}
```

- `server_name`：服务器标识，需与鹊桥 `server_name` 一致。
- `groups`：与该服务器互通的 QQ 群号，可以有多个；同一个群也可以出现在多个服务器
  条目里（一个群同时对接多个服务器）。
- `mc_to_qq`：逐类事件开关（聊天 / 进服 / 退服 / 死亡 / 成就），缺省为全开。
- `qq_to_mc`：是否把这个服务器纳入 `/mc` 广播目标，缺省 `true`。
- `allow_command`：**是否允许绑定群里的普通成员通过 `/rcon` 对该服务器执行指令，
  默认 `false`**。关闭时只有 SUPERUSER 能执行；开启后，绑定该服务器的群里任何人
  都可以执行（仍需 @ 机器人）。这个开关只影响 `/rcon`，不影响 `/mc`——`/mc` 发送
  的内容任何时候都只是聊天文本，从不会被服务端当作指令执行（见下方说明）。
- `formats`：可选，缺省时用插件内置模板。占位符 `{server}` `{player}` `{message}`
  `{sender}`。

改完配置后 SUPERUSER 发 `/reload_mc`（别名 `/重载互通`）热重载，不用重启进程。

## 命令

| 命令 | 权限 | 说明 |
|---|---|---|
| `/mc <消息>` | 互通群内所有人 | 广播到本群绑定的所有服务器（`qq_to_mc` 开启的） |
| `/mcstatus`（别名 `/服务器`） | 互通群内所有人 | 查看本群绑定的所有服务器在线人数与版本 |
| `@bot /rcon <服务器名> <命令>` | SUPERUSER，或该服务器 `allow_command=true` 时绑定群内任何人 | 通过 RCON 执行命令 |
| `@bot /reload_mc`（别名 `/重载互通`） | SUPERUSER | 热重载 servers.json |

## 关于指令注入

`/mc` 的内容通过 `send_msg` 以**聊天文本组件**下发，不经过 RCON，服务端不会将其
当作命令执行；即便有人发 `/mc /op xxx`，进游戏后也只是一行聊天文本。内容还会被
去除控制字符并按 `MC_MSG_MAX_LENGTH` 截断。

真正能执行命令的只有 `/rcon`，默认仅 SUPERUSER 可用；某个服务器把
`allow_command` 打开后，该服务器绑定群里的成员也能用，但仅限对**自己群绑定的
服务器**下指令——即使知道别的服务器名字，没在那个服务器的绑定群里也无法执行。
