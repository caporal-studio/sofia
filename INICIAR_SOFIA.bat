@echo off
setlocal
cls
echo =======================================
echo Starting SOFIA...
echo =======================================

if not exist "venv\Scripts\activate.bat" (
    echo ERROR - Virtual environment not found.
    echo Run INSTALADOR.bat before starting SOFIA.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

python -m streamlit run app/Home.py

pause
