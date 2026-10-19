@echo off
setlocal
cd /d "%~dp0"

py -3.12 --version >nul 2>&1
if not errorlevel 1 goto python312

py --version >nul 2>&1
if not errorlevel 1 goto python

echo Python was not found.
echo Install Python 3.12 from https://www.python.org/downloads/windows/
pause
exit /b 1

:python312
set "PYTHON=py -3.12"
goto check_audio

:python
set "PYTHON=py"

:check_audio
%PYTHON% -c "import numpy, sounddevice" >nul 2>&1
if not errorlevel 1 goto launch

echo Microphone recording needs NumPy and sounddevice.
choice /c YN /m "Install the required packages now from requirements.txt"
if errorlevel 2 goto launch
%PYTHON% -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
	echo Could not install microphone requirements. Read the error above.
	pause
	exit /b 1
)

:launch
%PYTHON% "%~dp0voice_changer_v2.py"
if errorlevel 1 (
	echo.
	echo Local Voice Studio V2 exited with an error. Read the message above.
	pause
)
