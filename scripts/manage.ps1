<#
  manage.ps1
  Wrapper para ejecutar manage.py usando el Python del venv sin necesidad de activar el entorno.
  Uso:
    .\scripts\manage.ps1 migrate
    .\scripts\manage.ps1 runserver 0.0.0.0:8000
#>

$venv = ".venv"
$python = Join-Path $venv "Scripts\python.exe"
if (-Not (Test-Path $python)) {
    Write-Error "No se detectó el intérprete del venv. Ejecuta .\scripts\setup.ps1 primero."
    exit 1
}

# Ejecuta manage.py con los argumentos pasados
& $python manage.py $args
