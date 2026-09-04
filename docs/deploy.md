# 生产部署（裸机版，暂不使用 Docker）

消息链路：**NTQQ ←(NapCat 劫持)→ OneBot v11 反向 WebSocket → NoneBot（本项目，监听 1927）**

## 1. 启动 bot（生产配置）

```powershell
# Windows
.\start.ps1 prod
```

```bash
# Linux
./start.sh prod
```

脚本会把系统环境变量 `ENVIRONMENT` 设为 `prod`（优先级高于 `.env` 文件），从而加载
`.env.prod`。守护循环会在异常退出或群里 `/reboot` 后 3 秒自动拉起进程。

上线前把 `.env.prod` 里剩下的空项填完：`SUPERUSERS`、`ADMIN`、`BLOCKLIST`、`QUOTE_PATH`。

## 2. 安装并配置 NapCat

本仓库根目录下的 `napcat/`（已 gitignore，不随仓库分发）是已经准备好的
NapCat Shell 终端版运行目录，详见 [`napcat/README.md`](../napcat/README.md)。
换机器部署时该目录不会跟着 git 走，需要按该 README 重新下载/配置一份，步骤概要：

1. 从 <https://github.com/NapNeko/NapCatQQ/releases> 下载与本机 QQNT 版本匹配的
   `NapCat.Shell.zip`（要求机器上已装好官方 QQNT 客户端），解压到 `napcat/` 目录。
2. 运行 `napcat/launcher-user.bat`（终端内运行，无需管理员权限），首次启动会打印
   二维码，用 bot 的 QQ 账号扫码登录。
3. 登录后在 `napcat/config/` 下会生成 `onebot11_<QQ号>.json`；也可以直接复制
   `napcat/config/onebot11.json.template` 改名使用，模板里的反向 WS 地址已经
   指向 `ws://127.0.0.1:1927/onebot/v11/ws`。把 `token` 改成与 `.env.prod` 中
   `ONEBOT_ACCESS_TOKEN` 相同的值，消息格式保持 `array`。
4. 也可以不改配置文件，直接打开 NapCat WebUI（默认 <http://127.0.0.1:6099/webui>）
   在 **网络配置** 中新增反向 WebSocket 客户端，效果相同。

NapCat 与 bot 不在同一台机器时：`.env.prod` 的 `HOST` 改为 `0.0.0.0`，
NapCat 侧 URL 改为 `ws://<bot机器IP>:1927/onebot/v11/ws`，并确保防火墙放行 1927
端口。此时 **必须** 使用 access token 鉴权。

## 3. 验证

1. bot 日志中出现 OneBot v11 `Bot <QQ号> connected` 即连接成功。
2. 群里 @bot 发送 `/ping`，回复 `pong!` 即链路打通。
3. SUPERUSER @bot 发送 `/reboot`，bot 回复后进程退出并被守护脚本拉起，
   NapCat 侧会按 `reconnectInterval` 自动重连。

## 4. Docker 封装（TODO，最后再做）

现有 `Dockerfile` / `docker-compose.yml` 尚不可用（镜像内没有 Python，挂载的是
Windows 虚拟环境）。封装时需要：换 `python:3.13-slim` 基底、容器内安装 requirements、
把 NapCat 作为同网络的 service 编入 compose，并将 `HOST` 设为 `0.0.0.0`。
