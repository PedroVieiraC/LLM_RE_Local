@echo off
pushd "%~dp0"
python -m llm %*
set RC=%ERRORLEVEL%
popd
exit /b %RC%
