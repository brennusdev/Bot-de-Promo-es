$ErrorActionPreference = 'Stop'

# ESTUDO (portabilidade): resolve a raiz pela localização do script —
# funciona em qualquer máquina, sem caminho absoluto fixo.
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

if (-not (Test-Path '.env')) {
    Copy-Item '.env.example' '.env'
}

Write-Host 'Instalando dependências do projeto...'
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host 'Validando testes...'
python -m pytest -q

Write-Host 'Iniciando stack com Docker Compose...'
docker compose up --build -d

Write-Host 'Aplicação iniciada.'
Write-Host 'Acesse:'
Write-Host '  - http://localhost:8000/'
Write-Host '  - http://localhost:8000/dashboard'
Write-Host '  - http://localhost:8000/health'
