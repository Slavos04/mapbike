@echo off
echo ===================================================
echo   MapBike - Instalacja srodowiska i zaleznosci
echo ===================================================
echo.

cd /d "%~dp0backend"

if not exist ".venv" (
    echo Tworzenie srodowiska wirtualnego .venv...
    python -m venv .venv
) else (
    echo Srodowisko .venv juz istnieje.
)

echo.
echo Aktywacja srodowiska wirtualnego...
call .venv\Scripts\activate.bat

echo.
echo Aktualizacja pip...
python -m pip install --upgrade pip

echo.
echo Instalacja pakietow z requirements.txt...
pip install -r requirements.txt

echo.
echo ===================================================
echo   Instalacja zakonczona sukcesem!
echo   Uruchom plik run.bat, aby wystartowac aplikacje.
echo ===================================================
pause
