$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\Win10\OneDrive\Documentos\Estudos e Projetos Ideias\Bot\Bot de Promoções'
python -m uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
