@echo off
setlocal
cls
echo =======================================
echo Preparing SOFIA...
echo =======================================

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR - Python not found.
    echo Install Python 3.11+ from https://www.python.org/downloads/windows/
    echo Enable "Add python.exe to PATH" during installation.
    pause
    exit /b 1
)
echo Python found

python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR - pip not found. Installing pip...
    python -m ensurepip --upgrade
)
echo pip found

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
echo Virtual environment active

echo Installing or updating dependencies...
python -m pip install --upgrade pip
python -m pip install -r app/install/requirements.txt
if %errorlevel% neq 0 (
    echo ERROR - Failed to install dependencies.
    pause
    exit /b 1
)
echo Dependencies updated

echo =======================================
echo Starting local user configuration...
echo =======================================
python app/scripts/setup_inicial.py

echo =======================================
echo Starting SOFIA...
echo =======================================

python -m streamlit run app/Home.py
pause
