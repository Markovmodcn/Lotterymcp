@echo off
setlocal
if not exist "%~dp0results" mkdir "%~dp0results"
python "%~dp0main.py" --periods 200 --output "%~dp0results\pl3_analysis_program.json"
endlocal
