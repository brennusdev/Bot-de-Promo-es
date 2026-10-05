$ErrorActionPreference = 'Stop'
# ESTUDO (portabilidade): raiz resolvida pela localização do script.
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
python -m uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
