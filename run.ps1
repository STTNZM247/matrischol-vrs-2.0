param(
    [string]$Host = "127.0.0.1:8000"
)

Write-Host "Iniciando servidor en $Host (usando venv)"
.\scripts\manage.ps1 runserver $Host
