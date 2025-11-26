<#
  setup.ps1
  Crea el entorno virtual (.venv) e instala las dependencias desde requirements.txt
  Uso: ejecutar en PowerShell desde la raíz del proyecto:
    .\scripts\setup.ps1
#>

$venv = ".venv"
if (-Not (Test-Path $venv)) {
    python -m venv $venv
    Write-Host "Entorno virtual creado en $venv"
} else {
    Write-Host "Entorno virtual ya existe en $venv"
}

$pip = Join-Path $venv "Scripts\pip.exe"
if (-Not (Test-Path $pip)) {
    Write-Error "No se encontró pip en el venv. Asegúrate de que Python esté instalado correctamente."
    exit 1
}

& $pip install --upgrade pip
& $pip install -r requirements.txt

Write-Host "Dependencias instaladas. Para ejecutar comandos sin activar el venv usa: .\scripts\manage.ps1 <comando>"
Write-Host "Ejemplo: .\scripts\manage.ps1 migrate"
