@echo off
chcp 65001 >nul
echo ========================================
echo   LeetCode 刷题提醒 - 定时任务设置
echo ========================================
echo.
echo 请选择要设置的任务：
echo.
echo 1. 测试发送消息
echo 2. 发送当前进度提醒
echo 3. 设置每天早上9点提醒
echo 4. 设置每天晚上9点提醒
echo 5. 设置每天早晚提醒
echo 6. 删除所有定时任务
echo 7. 查看当前定时任务
echo.
set /p choice="请输入选项 (1-7): "

if "%choice%"=="1" (
    python "%~dp0remind.py" test
    pause
    exit /b
)

if "%choice%"=="2" (
    python "%~dp0remind.py" now
    pause
    exit /b
)

if "%choice%"=="3" (
    schtasks /create /tn "LeetCode早间提醒" /tr "python %~dp0remind.py morning" /sc daily /st 09:00 /f
    echo 已设置每天早上9点提醒
    pause
    exit /b
)

if "%choice%"=="4" (
    schtasks /create /tn "LeetCode晚间提醒" /tr "python %~dp0remind.py evening" /sc daily /st 21:00 /f
    echo 已设置每天晚上9点提醒
    pause
    exit /b
)

if "%choice%"=="5" (
    schtasks /create /tn "LeetCode早间提醒" /tr "python %~dp0remind.py morning" /sc daily /st 09:00 /f
    schtasks /create /tn "LeetCode晚间提醒" /tr "python %~dp0remind.py evening" /sc daily /st 21:00 /f
    echo 已设置每天早上9点和晚上9点提醒
    pause
    exit /b
)

if "%choice%"=="6" (
    schtasks /delete /tn "LeetCode早间提醒" /f 2>nul
    schtasks /delete /tn "LeetCode晚间提醒" /f 2>nul
    echo 已删除所有定时任务
    pause
    exit /b
)

if "%choice%"=="7" (
    schtasks /query /tn "LeetCode早间提醒" 2>nul
    schtasks /query /tn "LeetCode晚间提醒" 2>nul
    pause
    exit /b
)

echo 无效选项
pause
