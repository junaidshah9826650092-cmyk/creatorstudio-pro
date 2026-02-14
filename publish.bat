@echo off
echo.
echo [1/3] Adding changes...
git add .

echo [2/3] Committing changes...
set msg=Update: %date% %time%
git commit -m "%msg%"

echo [3/3] Pushing to GitHub/Render...
git push origin main

echo.
echo ========================================
echo Done! Your website is now updating on Render.
echo Wait 2-3 minutes for the changes to go live.
echo ========================================
pause
