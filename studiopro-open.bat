@echo off
REM Studio Pro v3.0 — Open Browser Only
REM Use this if the server is already running and you just want the web UI.

start http://127.0.0.1:7875
echo Opening Studio Pro at http://127.0.0.1:7875 ...
timeout /t 2 /nobreak >nul
