# Docker 一键部署

两个容器，通过 `docker compose` 编排在同一网络里：

- **bot**：本仓库自身，`Dockerfile` 用 `python:3.13-slim` 构建，监听容器内 `0.0.0.0:1927`。
- **napcat**：官方 [`mlikiowa/napcat-docker`](https://github.com/NapNeko/NapCat-Docker) 镜像，
  Linux 版无头 QQNT + NapCat，通过容器网络内的服务名 `bot` 反向连接到本项目。

> 这是一套独立于仓库根目录 `napcat/`（Windows 本地 Shell 版）的全新部署，两者
> **不共享登录状态**——用 Docker 方式跑，需要重新扫码登录一次机器人的 QQ 账号。
> 如果你只是本机开发调试，继续用 `napcat/` + `.\start.ps1` 更轻量；Docker 方案
> 适合"钦定"一台机器长期跑、一条命令起停的场景。

## 前置条件

- 装好 Docker Desktop（Windows 上用 WSL2 后端）且**引擎已启动**——任务栏图标常驻、
  `docker version` 不报错再继续。
- 复制 `.env.example` 为 `.env.docker`，除了正常字段外，**`HOST` 必须填
  `0.0.0.0`**（容器内的 `127.0.0.1` 只指向自己，napcat 容器连不进来）。

## 启动

```powershell
docker compose up -d --build
```

以后改代码后只需 `docker compose up -d --build` 重新构建 bot 镜像；日常起停用
`docker compose up -d` / `docker compose down`（不加 `-v` 不会清掉 napcat 的登录态）。

## 首次登录 NapCat

```powershell
docker compose logs -f napcat
```

日志里会出现二维码，用机器人的 QQ 账号扫码登录（这一步必须人工完成）。登录成功后
NapCat 会在 `docker/napcat/config/` 下生成 `onebot11_<QQ号>.json`（该目录已挂载
持久化卷，重启容器不会丢登录态）。

## 配置反向 WebSocket

1. 把仓库里的 `docker/onebot11.json.template` 复制到
   `docker/napcat/config/onebot11_<机器人QQ号>.json`（文件名里的 QQ 号来自上一步
   登录日志，或 WebUI 网络配置页确认）；
2. 模板里的地址已经写好 `ws://bot:1927/onebot/v11/ws`（`bot` 是 compose 里的服务名，
   走容器内网 DNS，不用改成 IP）；如果 `.env.docker` 的 `ONEBOT_ACCESS_TOKEN` 非空，
   把模板里的 `token` 改成一致的值；
3. `docker compose restart napcat` 让配置生效，或直接打开 WebUI
   （<http://127.0.0.1:6099/webui>，登录 token 见 `docker compose logs napcat`）
   在网络配置页手动加一样的反向 WS 客户端。

## 验证

`docker compose logs -f bot`，出现 `Bot <QQ号> connected` 即连接成功；群里
`@bot /ping` 应回复 `pong!`。Minecraft 服务器侧的鹊桥则直接连
`ws://<宿主机IP>:1927/minecraft/ws`（bot 的 1927 端口已经映射到宿主机）。

## 目录说明

- `docker/onebot11.json.template`：跟随仓库分发的配置模板，改名使用；
- `docker/napcat/config/`、`docker/napcat/qq-data/`：容器运行时生成/写入的真实
  配置和 QQ 登录数据，已加入 `.gitignore`，不会被提交。
