@echo off
chcp 65001 > nul
title Sistema de Análisis y Seguimiento del Perfil Emprendedor - USTA Villavicencio

echo =========================================================================
echo   UNIVERSIDAD SANTO TOMÁS - SECCIONAL VILLAVICENCIO
echo   Dirección de Proyección Social
echo   Sistema de Análisis y Seguimiento del Perfil Emprendedor
echo =========================================================================
echo.

cd /d "%~dp0"

REM Verificar instalación de dependencias
python -c "import fastapi, uvicorn, openpyxl, reportlab, sqlalchemy" 2>nul
if %errorlevel% neq 0 (
    echo Instalando dependencias necesarias...
    pip install -r requirements.txt
)

REM Inicializar base de datos si no existe
if not exist "data\usta_perfil.db" (
    echo Inicializando base de datos institucional...
    python scripts\seed_data.py
)

echo.
echo Iniciando servidor web institucional en http://localhost:8000
echo Acceda desde cualquier navegador en: http://localhost:8000
echo.
echo Credenciales por defecto:
echo   - Administrador: admin@usta.edu.co / AdminUsta2026*
echo   - Consulta:      consulta@usta.edu.co / Consulta2026*
echo.
echo Presione Ctrl + C para detener el servidor.
echo =========================================================================
echo.

start "" http://localhost:8000
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
