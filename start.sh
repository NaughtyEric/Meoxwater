#!/usr/bin/env bash
# 守护循环：进程正常退出(0)则停止，异常退出/主动 reboot 则 3 秒后拉起
# 用法：./start.sh        -> 按 .env 里的 ENVIRONMENT 运行（默认 dev）
#       ./start.sh prod   -> 以生产配置(.env.prod)运行
cd "$(dirname "$0")" || exit 1

if [ -n "$1" ]; then
    # 系统环境变量优先级高于 .env 文件
    export ENVIRONMENT="$1"
fi

while true; do
    nb run
    code=$?
    if [ "$code" -eq 0 ]; then
        echo "bot 正常退出，停止守护。"
        break
    fi
    echo "bot 退出（code=$code），3 秒后重启……"
    sleep 3
done
