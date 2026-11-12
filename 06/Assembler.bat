@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

rem Make Python use UTF-8 for console input/output
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

rem Locate a Python 3 interpreter
set "PY="
py -3 --version >nul 2>nul && set "PY=py -3"
if not defined PY (
    python --version >nul 2>nul && set "PY=python"
)
if not defined PY (
    echo [ERROR] Python 3 was not found. Install it and add it to PATH.
    goto :fail
)

rem No arguments: interactive mode (for double-click use)
if "%~1"=="" goto :interactive

%PY% "%~dp0assembler.py" %*
if errorlevel 1 goto :fail
goto :done

:interactive
echo ============================================
echo  Hack Assembler (nand2tetris Project 6)
echo ============================================
echo.
echo Drag and drop .asm files here, or type a path.
echo A folder path will assemble every .asm inside it.
echo.
set "TARGET="
set /p "TARGET=Path: "
if not defined TARGET goto :done

%PY% "%~dp0assembler.py" "%TARGET%"
if errorlevel 1 goto :fail

:done
echo.
echo Done.
pause
exit /b 0

:fail
echo.
echo Assembly failed. Check the message above.
pause
exit /b 1
