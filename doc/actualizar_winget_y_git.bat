@echo off
echo =========================================
echo   ACTUALIZADOR DE GIT Y WINGET (CMD)
echo =========================================

REM Paso 1: Actualizar AppInstaller (winget)
echo.
echo Verificando si hay una nueva version de winget...
winget upgrade --id Microsoft.AppInstaller -e --accept-package-agreements --accept-source-agreements

REM Paso 2: Actualizar Git
echo.
echo Verificando si hay una nueva version de Git...
winget upgrade --id Git.Git -e --accept-package-agreements --accept-source-agreements

REM Paso 3: Mostrar la version actual de Git
echo.
echo Version actual de Git instalada:
git --version

echo.
echo ===========================
echo   PROCESO COMPLETADO
echo ===========================
pause
