@echo off
REM PA Agent 启动脚本 — 用 pythonw.exe 启动，无 cmd 黑窗口
REM 双击此文件启动，或右键 → 发送到 → 桌面快捷方式
cd /d "%~dp0"
start "" pythonw run.pyw
