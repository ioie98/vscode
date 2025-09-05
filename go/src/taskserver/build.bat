@echo off
set APP_NAME=taskserver
set BUILD_DIR=bin

if not exist %BUILD_DIR% mkdir %BUILD_DIR%

echo 正在编译 %APP_NAME% ...
go build -o %BUILD_DIR%\%APP_NAME%.exe .

if %ERRORLEVEL%==0 (
    echo 编译成功: %BUILD_DIR%\%APP_NAME%.exe
) else (
    echo 编译失败
)
pause
