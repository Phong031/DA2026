@echo off
echo ============================================
echo Setting up Data Analytics Project
echo ============================================

echo.
echo Creating virtual environment...
python -m venv venv

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo To run the pipeline:
echo python scripts\upload_pilelog.py
echo.
pause