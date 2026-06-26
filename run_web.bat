@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Нет .venv. Создайте: py -3.12 -m venv .venv
    pause
    exit /b 1
)
call .venv\Scripts\activate.bat
pip install streamlit -q
echo.
echo Веб-интерфейс: http://localhost:8501
echo Закройте это окно чтобы остановить сервер.
echo.
streamlit run app.py
