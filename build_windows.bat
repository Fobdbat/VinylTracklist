@echo off
REM ================================================================
REM  VinylTracklist - genera dist\VinylTracklist.exe (Windows 7, 8, 10 i 11)
REM
REM  Requisit (nomes a l'ordinador on es genera l'exe):
REM    Python 3.8.10 de 32 bits  ->  "Windows installer (32-bit)"
REM    https://www.python.org/downloads/release/python-3810/
REM    Marqueu "Add Python to PATH" i deixeu el "py launcher".
REM ================================================================
setlocal
cd /d "%~dp0"

py -3.8-32 --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  No s'ha trobat Python 3.8 de 32 bits.
    echo  Instal.la "Windows installer (32-bit)" de Python 3.8.10 i torna-ho a provar.
    echo.
    pause
    exit /b 1
)

if not exist ".venv38-32\Scripts\python.exe" (
    echo Creant l'entorn de compilacio...
    py -3.8-32 -m venv .venv38-32
)
call ".venv38-32\Scripts\activate.bat"

python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
if errorlevel 1 goto :error

python -m unittest discover -s tests -p "test_*.py"
if errorlevel 1 goto :error

pyinstaller --noconfirm --clean VinylTracklist.spec
if errorlevel 1 goto :error

echo.
echo  FET: dist\VinylTracklist.exe
echo  Aquest fitxer es pot copiar a qualsevol ordinador amb Windows 7 o posterior.
echo.
pause
exit /b 0

:error
echo.
echo  S'ha produit un error. Revisa els missatges de sobre.
pause
exit /b 1
