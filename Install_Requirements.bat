@echo off
echo Starting Disease Outbreak Prediction System Requirements Installer...
echo.

:: Run the PowerShell script with bypass execution policy
powershell -ExecutionPolicy Bypass -File "%~dp0one_click_install.ps1"

echo.
if %ERRORLEVEL% NEQ 0 (
    echo Installation encountered an error. Please check the output above.
    pause
    exit /b %ERRORLEVEL%
)

echo Installation completed successfully!
pause 