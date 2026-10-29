@echo off
chcp 65001 > nul
title Instalador de Acceso Directo - Sistema UCC
echo ==============================================================================
echo        UNIVERSIDAD COOPERATIVA DE COLOMBIA - SISTEMA ACADÉMICO
echo                Instalador de Acceso Directo de Escritorio
echo ==============================================================================
echo.
echo Creando acceso directo en tu Escritorio con el logotipo oficial...

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $desk = [System.Environment]::GetFolderPath('Desktop'); $lnk = $ws.CreateShortcut(\"$desk\Sistema Universitario UCC.lnk\"); $lnk.TargetPath = 'pythonw.exe'; $lnk.Arguments = '\"%~dp0main.py\"'; $lnk.WorkingDirectory = '%~dp0'; $lnk.IconLocation = '%~dp0logo_ucc.ico, 0'; $lnk.Description = 'Sistema Universitario UCC - Versión Escritorio'; $lnk.Save(); Write-Host 'Acceso directo creado correctamente.' -ForegroundColor Green"

echo.
echo ==============================================================================
echo  Listo! Busca en tu Escritorio el icono "Sistema Universitario UCC".
echo  Puedes hacer doble clic sobre él para abrir la aplicación de inmediato.
echo ==============================================================================
echo.
pause
