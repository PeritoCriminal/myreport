@echo off
SETLOCAL

:: 1. Caminhos baseados na sua estrutura real
SET ROOT_DIR=C:\Users\capri\Desktop\render
SET PROJECT_DIR=%ROOT_DIR%\myreport
SET VENV_PATH=%ROOT_DIR%\.venv\Scripts\activate

echo [1/3] Acessando pasta do projeto...
cd /d "%PROJECT_DIR%"

echo [2/3] Ativando ambiente virtual...
call "%VENV_PATH%"

echo [3/3] Garantindo o commit 8b37773...
git checkout 8b37773 --quiet

echo.
echo === Iniciando Servidor Django ===
echo Local: %CD%
echo Commit: 8b37773
echo.

:: O comando padrão do Django para rodar localmente
python manage.py runserver

pause