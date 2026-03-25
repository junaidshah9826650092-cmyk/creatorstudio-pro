@echo off
echo =======================================================
echo          Vitox Daily Instagram Automation Bot
echo =======================================================
echo.
echo [1/2] Generating Daily Video using AI...
python video_generator.py
if %errorlevel% neq 0 (
    echo [ERROR] Video generation failed! Exiting.
    pause
    exit /b %errorlevel%
)
echo.
echo [2/2] Uploading Video to Instagram...
python instagram_poster.py
if %errorlevel% neq 0 (
    echo [ERROR] Instagram upload failed! Exiting.
    pause
    exit /b %errorlevel%
)

echo.
echo [3/3] Distributing QR codes to public image hosts...
python free_image_uploader.py
if %errorlevel% neq 0 (
    echo [WARNING] Image distribution failed, but continuing...
)

echo.
echo =======================================================
echo Successfully completed daily run!
echo =======================================================
:: Remove pause in production so it can close automatically
:: pause
