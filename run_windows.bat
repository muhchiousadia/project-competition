@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3.11 -m venv .venv
        if errorlevel 1 py -m venv .venv
    ) else (
        where python >nul 2>nul
        if errorlevel 1 (
            echo Python 3.11 or newer is required. Install Python and enable the Python launcher or add python.exe to PATH.
            pause
            exit /b 1
        )
        python -m venv .venv
    )
    if errorlevel 1 (
        echo Could not create the project virtual environment.
        pause
        exit /b 1
    )
)

".venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 (
    echo Python 3.11 or newer is required. Recreate .venv with an installed Python 3.11 or newer interpreter.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Dependency installation failed. Check your internet connection and requirements.txt.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m streamlit run app.py
if errorlevel 1 (
    echo Streamlit exited with an error. Review the output above.
    pause
    exit /b 1
)
