@echo off
cd /d %~dp0
if not exist .venv (
  echo Membuat virtual environment...
  py -m venv .venv
)
call .venv\Scripts\activate
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Instalasi dependency gagal. Pastikan Python dan internet tersedia.
  pause
  exit /b 1
)
start http://127.0.0.1:5000
python app.py
pause
