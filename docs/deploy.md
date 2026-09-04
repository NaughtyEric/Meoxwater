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

1. 从 <https://github.com/NapNeko/NapCatQQ> 下载安装（需要机器上装有官方 NTQQ，
   NapCat 提供一键安装包/Shell 版，支持无 GUI 运行）。
2. 首次启动后扫码登录 bot 的 QQ 账号。
3. 打开 NapCat WebUI（默认 <http://127.0.0.1:6099/webui>），在 **网络配置** 中新增一个
   **WebSocket 客户端（反向 WS）**：
   - URL：`ws://127.0.0.1:1927/onebot/v11/ws`
   - Token：与 `.env.prod` 中 `ONEBOT_ACCESS_TOKEN` 相同的值
   - 消息格式：`array`

   也可以直接参考本目录下的 `napcat.onebot11.sample.json`（对应 NapCat 的
   `config/onebot11_<QQ号>.json`），把 `token` 与 `.env.prod` 保持一致。

4. NapCat 与 bot 不在同一台机器时：`.env.prod` 的 `HOST` 改为 `0.0.0.0`，
   NapCat 的 URL 改为 `ws://<bot机器IP>:1927/onebot/v11/ws`，并确保防火墙放行 1927 端口。
   此时 **必须** 使用 access token 鉴权。

## 3. 验证

1. bot 日志中出现 OneBot v11 `Bot <QQ号> connected` 即连接成功。
2. 群里 @bot 发送 `/ping`，回复 `pong!` 即链路打通。
3. SUPERUSER @bot 发送 `/reboot`，bot 回复后进程退出并被守护脚本拉起，
   NapCat 侧会按 `reconnectInterval` 自动重连。

## 4. Docker 封装（TODO，最后再做）

现有 `Dockerfile` / `docker-compose.yml` 尚不可用（镜像内没有 Python，挂载的是
Windows 虚拟环境）。封装时需要：换 `python:3.13-slim` 基底、容器内安装 requirements、
把 NapCat 作为同网络的 service 编入 compose，并将 `HOST` 设为 `0.0.0.0`。
