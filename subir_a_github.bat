@echo off
chcp 65001 > nul
echo =======================================================================
echo    SISTEMA PERFIL EMPRENDEDOR USTA - SUBIR A GITHUB PARA RENDER
echo =======================================================================
echo.
echo 1. Abre https://github.com/new en tu navegador.
echo 2. Nombra tu repositorio (ej: perfil-emprendedor-usta).
echo 3. Déjalo en Público y pulsa "Create repository".
echo 4. Copia la URL del repositorio que te da GitHub.
echo.
set /p REPO_URL="Pega aquí la URL de tu repositorio de GitHub: "

if "%REPO_URL%"=="" (
    echo [ERROR] No ingresaste ninguna URL.
    pause
    exit /b
)

echo.
echo Configurando remoto y subiendo código...
cd /d "%~dp0"
.\mingit\cmd\git.exe remote remove origin 2>nul
.\mingit\cmd\git.exe remote add origin %REPO_URL%
.\mingit\cmd\git.exe branch -M main
.\mingit\cmd\git.exe push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =======================================================================
    echo   [ÉXITO] ¡Código subido a GitHub correctamente!
    echo =======================================================================
    echo Ahora en tu pestaña de Render:
    echo 1. Selecciona "New +" -^> "Web Service".
    echo 2. Pega la URL de tu repositorio: %REPO_URL%
    echo 3. Render detectará automáticamente el archivo render.yaml y lo desplegará.
    echo =======================================================================
) else (
    echo.
    echo [AVISO] Si te solicitó usuario y contraseña, recuerda que GitHub requiere un Personal Access Token o que inicies sesión en Git Credential Manager.
)

pause
