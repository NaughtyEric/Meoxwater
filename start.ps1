# 守护循环（Windows）：进程正常退出(0)则停止，异常退出/主动 reboot 则 3 秒后拉起
# 用法：.\start.ps1          -> 按 .env 里的 ENVIRONMENT 运行（默认 dev）
#       .\start.ps1 prod    -> 以生产配置(.env.prod)运行
param([string]$Environment = "")

Set-Location $PSScriptRoot
if ($Environment -ne "") {
    # 系统环境变量优先级高于 .env 文件
    $env:ENVIRONMENT = $Environment
}

while ($true) {
    & "$PSScriptRoot\.venv\Scripts\nb.exe" run
    $code = $LASTEXITCODE
    if ($code -eq 0) {
        Write-Host "bot 正常退出，停止守护。"
        break
    }
    Write-Host "bot 退出（code=$code），3 秒后重启……"
    Start-Sleep -Seconds 3
}
