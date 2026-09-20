@echo off
echo ===================================================
echo   MapBike - Uruchamianie serwera i aplikacji Web
echo ===================================================
echo.

cd /d "%~dp0backend"

if not exist ".venv\Scripts\activate.bat" (
    echo [BLAD] Nie znaleziono srodowiska .venv!
    echo Proske najpierw uruchomic plik install.bat
    echo.
    pause
    exit /b 1
)

echo Aktywacja srodowiska .venv...
call .venv\Scripts\activate.bat

echo.
echo Uruchamianie serwera MapBike pod adresem:
echo http://localhost:8000
echo.
echo (Nacisnij Ctrl+C, aby zatrzymac serwer)
echo.

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

pause
