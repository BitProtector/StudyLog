@echo off
set /p venv_name=Bitte Venv-Name angeben. z.B. [venv]
set "PYTHON_EXE=.\%venv_name%\Scripts\python.exe"
set "SCRIPT_PATH=.\main.py"

REM Aufruf von PyInstaller als Modul über den Python-Interpreter
"%PYTHON_EXE%" -m PyInstaller --noconfirm --onefile --console "%SCRIPT_PATH%"

pause >nul
