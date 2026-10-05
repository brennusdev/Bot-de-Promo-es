# Bot de Promoções

Sistema de monitoramento de preços e alertas de promoção para produtos de marketplace.

## Visão geral

- coleta de produtos por URL
- registro de histórico de preços
- cálculo de promoção e score
- alertas por queda percentual
- API FastAPI para integração
- dashboard simples para visualização
- webhook do WhatsApp para interação

## Requisitos

- Python 3.12+
- pip
- Docker e Docker Compose (opcional, para infraestrutura)

## Instalação local

1. Entre na pasta do projeto:

   PowerShell:
   ```powershell
   Set-Location "C:\Users\Win10\OneDrive\Documentos\Estudos e Projetos Ideias\Bot\Bot de Promoções"
   ```

2. Crie e ative um ambiente virtual:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Instale as dependências:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. Rode a suíte de testes:

   ```powershell
   python -m pytest -q
   ```

5. Inicie a API:

   ```powershell
   python -m uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
   ```

   Ou use o launcher do projeto:

   ```powershell
   .\run_local.ps1
   ```

## Endpoints importantes

- http://localhost:8000/
- http://localhost:8000/health
- http://localhost:8000/dashboard
- http://localhost:8000/products
- http://localhost:8000/users
- http://localhost:8000/webhooks/whatsapp

## Arquitetura de produção

A estrutura recomendada para produção é:

- Frontend: Vercel
- API: Render ou Railway
- Worker: serviço separado em Render/Railway ou VPS
- Banco: PostgreSQL externo
- Monitoramento: health checks + logs

Fluxo recomendado:

1. Vercel hospeda o dashboard e frontend
2. Render/Railway hospeda a API FastAPI
3. worker roda em outro serviço e executa a checagem periódica de preços
4. PostgreSQL fica externo e seguro
5. WhatsApp usa HTTPS e webhook público válido

> Nota: o Redis foi removido da stack — nenhum código o utilizava. Se adicionar
> cache no futuro, reintroduza `REDIS_URL` no settings e no docker-compose.

## Docker Compose completo

O projeto inclui stack com PostgreSQL, API e worker (o Redis foi removido por
não ser usado). Para subir em ambiente local:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

## Deploy em Vercel + Render/Railway

### Vercel
- Conecte o repositório ao Vercel
- use o arquivo [vercel.json](vercel.json)
- configure as variáveis de ambiente em produção
- a interface do dashboard pode ser servida aqui

### Render/Railway
- publique a API FastAPI como service web
- use `uvicorn app.api:app --host 0.0.0.0 --port 10000`
- configure `DATABASE_URL`, `REDIS_URL`, `APP_ENV=production`
- publique o worker como service worker separado com comando:

```bash
python -m app.workers.price_worker
```

## Deploy local em Windows

Use o script de implantação:

```powershell
.\deploy_local.ps1
```

## Checklist de execução em máquina real

Consulte [docs/DEPLOY_CHECKLIST.md](docs/DEPLOY_CHECKLIST.md) para a sequência completa de validação e operação em produção.

## Observação importante sobre Windows / PowerShell

O problema clássico do ambiente Windows é o uso de caminhos com barras invertidas e espaços, que geram escape indevido em comandos Python. Quando necessário, prefira:

```powershell
Set-Location "C:\Users\Win10\OneDrive\Documentos\Estudos e Projetos Ideias\Bot\Bot de Promoções"
python -m pytest -q
```

ou o uso de caminhos com barra em vez de `\` dentro de strings Python.

## Monitoramento e operação

O projeto inclui monitoramento básico de saúde e logs rotativos.

### Health check

- http://localhost:8000/health
- http://localhost:8000/ready

### Logs

Os logs são gravados em `logs/pricebot.log` com rotação diária.

### Backup do banco

Use o script de backup:

```powershell
python scripts\backup_db.py
```

### Verificação de saúde remota

```powershell
python scripts\health_check.py
```

## Estado atual

A base funcional foi validada com sucesso:

- cadastro de produtos
- histórico de preços
- alertas
- webhook do WhatsApp
- dashboard básico
- testes automatizados passando
- monitoramento de saúde
- backup do banco
- logs rotativos
