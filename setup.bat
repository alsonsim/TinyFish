@echo off
echo Creating TinyFish Financial Agent directory structure...

mkdir src 2>nul
mkdir src\agent 2>nul
mkdir src\sources 2>nul
mkdir src\sentiment 2>nul
mkdir src\data 2>nul
mkdir src\trading 2>nul
mkdir src\utils 2>nul
mkdir tests 2>nul
mkdir scripts 2>nul

echo.
echo Directory structure created!
echo.
echo Now run: python create_files.py
echo.
pause
