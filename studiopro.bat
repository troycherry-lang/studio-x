@echo off
REM Studio Pro v3.0 Launcher

cd /d "C:\Users\troyc\Documents\kimi\workspace\StudioPro-v3"
if errorlevel 1 (
    echo [ERROR] Cannot find StudioPro-v3 folder
    pause
    exit /b 1
)

echo ============================================
echo  Studio Pro v3.0
echo ============================================
echo.

REM Check if backend is already running
curl -s http://127.0.0.1:7875/api/health >nul 2>&1
if %errorlevel%==0 (
    echo  [OK] Studio Pro is already running.
    echo  Opening browser...
    start http://127.0.0.1:7875
    timeout /t 3 /nobreak >nul
    exit /b 0
)

REM Check if ComfyUI is running
curl -s http://127.0.0.1:8188/system_stats >nul 2>&1
if %errorlevel%==0 (
    echo  [OK] ComfyUI already running.
    goto :start_backend
)

echo  [..] Starting ComfyUI...
start "ComfyUI" /min cmd /c "cd /d C:\Users\troyc\Documents\kimi\workspace\ComfyUI && venv\Scripts\python.exe main.py --listen 127.0.0.1 --port 8188"

set /a count=0
:wait_comfyui
set /a count+=1
if %count% gtr 60 goto :timeout
curl -s http://127.0.0.1:8188/system_stats >nul 2>&1
if %errorlevel%==0 goto :start_backend
timeout /t 1 /nobreak >nul
goto :wait_comfyui

:timeout
echo  [ERROR] ComfyUI did not start within 60 seconds.
echo  Close all Python windows and try again.
pause
exit /b 1

:start_backend
echo  [OK] ComfyUI ready.
echo.
echo  [..] Starting Studio Pro backend...
echo  URL: http://127.0.0.1:7875
echo.
echo  --------------------------------------------
echo  Opening browser: http://127.0.0.1:7875
echo  Press Ctrl+C then Y to stop.
echo  --------------------------------------------
echo.

cd backend
start http://127.0.0.1:7875
"C:\Program Files\Python310\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 7875 --log-level info

pause
