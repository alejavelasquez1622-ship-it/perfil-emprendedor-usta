# Script PowerShell para iniciar el Sistema Institucional USTA Villavicencio
$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "USTA - Sistema Perfil Emprendedor"

Write-Host "=========================================================================" -ForegroundColor DarkBlue
Write-Host "  UNIVERSIDAD SANTO TOMÁS - SECCIONAL VILLAVICENCIO" -ForegroundColor Yellow
Write-Host "  Dirección de Proyección Social" -ForegroundColor White
Write-Host "  Sistema de Análisis y Seguimiento del Perfil Emprendedor" -ForegroundColor Cyan
Write-Host "=========================================================================" -ForegroundColor DarkBlue
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check and install requirements if needed
try {
    python -c "import fastapi, uvicorn, openpyxl, reportlab, sqlalchemy" 2>$null
} catch {
    Write-Host "Instalando paquetes requeridos..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Initialize database if needed
if (-not (Test-Path "$ScriptDir\data\usta_perfil.db")) {
    Write-Host "Inicializando base de datos institucional..." -ForegroundColor Green
    python scripts\seed_data.py
}

Write-Host "Servidor web disponible en: http://localhost:8000" -ForegroundColor Green
Write-Host "Credenciales: admin@usta.edu.co / AdminUsta2026*" -ForegroundColor White
Write-Host ""

Start-Process "http://localhost:8000"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
