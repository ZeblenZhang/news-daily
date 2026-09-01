@echo off
chcp 65001 >nul
echo ============================================
echo   新闻日报一键更新脚本
echo ============================================
echo.

set "PROJECT_DIR=C:\Users\admin\WorkBuddy\2026-09-01-09-46-41\news-daily"
set "PYTHON=C:\Users\admin\.workbuddy\binaries\python\envs\default\Scripts\python.exe"

cd /d "%PROJECT_DIR%"
if errorlevel 1 (
    echo [错误] 无法进入项目目录: %PROJECT_DIR%
    pause
    exit /b 1
)

echo [1/4] 抓取最新新闻...
"%PYTHON%" build.py
if errorlevel 1 (
    echo [错误] 抓取或构建失败
    pause
    exit /b 1
)
echo.

echo [2/4] 添加改动到提交清单...
git add .
if errorlevel 1 (
    echo [错误] git add 失败
    pause
    exit /b 1
)

echo [3/4] 提交改动...
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (set mytime=%%a:%%b)
git commit -m "自动更新 %mydate% %mytime%"
if errorlevel 1 (
    echo [提示] 没有新改动需要提交，继续推送...
)

echo [4/4] 推送到 GitHub...
git push origin main
if errorlevel 1 (
    echo [错误] 推送失败，请检查网络或 token 是否过期
    pause
    exit /b 1
)

echo.
echo ============================================
echo   更新完成！
echo   1~2 分钟后访问:
echo   https://ZeblenZhang.github.io/news-daily/
echo ============================================
pause
