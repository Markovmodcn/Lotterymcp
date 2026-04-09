@echo off
setlocal
if "%NEUXSBOT_API_BASE_URL%"=="" set "NEUXSBOT_API_BASE_URL=https://www.neuxsbot.com"
if "%NEUXSBOT_PERIODS%"=="" set "NEUXSBOT_PERIODS=120"
python "%~dp0main.py" --periods %NEUXSBOT_PERIODS% --output "%~dp0analysis_result.json"
endlocal
