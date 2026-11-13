@echo off
rem One-time setup for Windows: installs everything, then asks for your settings.
rem Usage: double-click setup.bat, or run "setup.bat" in Command Prompt / PowerShell.
setlocal
cd /d "%~dp0"

set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>&1 && set "PY=py -3"
if not defined PY (
  python -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>&1 && set "PY=python"
)
if not defined PY (
  echo Python 3.9 or newer is required.
  echo Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH", then run this again.
  pause
  exit /b 1
)

echo == Installing dependencies (this can take a minute) ==
if not exist .venv (
  %PY% -m venv .venv || goto :error
)
.venv\Scripts\python -m pip install --quiet --upgrade pip || goto :error
.venv\Scripts\python -m pip install --quiet -r requirements.txt || goto :error
.venv\Scripts\python -m playwright install chromium || goto :error

.venv\Scripts\python configure.py
pause
exit /b %errorlevel%

:error
echo.
echo Setup failed. See the error above.
pause
exit /b 1
