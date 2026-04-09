@echo off
setlocal
if "%NEUXSBOT_API_BASE_URL%"=="" set "NEUXSBOT_API_BASE_URL=https://www.neuxsbot.com"
if "%~1"=="" (
  set PERIODS=120
) else (
  set PERIODS=%~1
)
if "%~2"=="" (
  set OUTPUT=%~dp0analysis_result.json
) else (
  set OUTPUT=%~2
)
python "%~dp0main.py" --periods %PERIODS% --output "%OUTPUT%"
endlocal
