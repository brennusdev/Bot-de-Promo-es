# Bot de Promoções

Sistema de monitoramento de preços e alertas de promoção para produtos de marketplace.

## Visão geral

- coleta de produtos por URL
- registro de histórico de preços
- cálculo de promoção e score
- alertas por queda percentual (log + e-mail)
- API FastAPI para integração
- dashboard web: cadastro por URL, filtro por categoria, paginação,
  popup de novas ofertas, gráfico interativo de histórico (ECharts)
- login administrativo opcional e rate limit no cadastro

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

   Ou use os launchers do projeto (agora centralizados em `deploy/`):

   ```powershell
   .\deploy\run_local.ps1       # só a API
   .\deploy\deploy_local.ps1    # deps + testes + Docker
   ```

## Endpoints importantes

- http://localhost:8000/
- http://localhost:8000/health
- http://localhost:8000/dashboard
- http://localhost:8000/products
- http://localhost:8000/categories
- http://localhost:8000/offers/new
- http://localhost:8000/products/view?id=1 (detalhe + gráfico)
- http://localhost:8000/users
- http://localhost:8000/docs (documentação interativa da API)

## Arquitetura de produção (Vercel-only)

A produção roda em DOIS serviços, nada mais:

- **Vercel** — API FastAPI + dashboard + worker serverless (via cron)
- **PostgreSQL externo** — Neon ou Supabase (tier free serve)

Fluxo:

1. Vercel hospeda a API (`api/index.py`) e o dashboard (`/dashboard`)
2. O cron do `vercel.json` dispara `GET /cron/monitor` (a cada 30 min no
   plano Pro; 1x/dia no Hobby)
3. O PostgreSQL fica externo e persiste os dados (o filesystem do
   serverless é somente leitura — nada de SQLite em produção)
4. Monitoramento: `/health` + Runtime Logs da Vercel

### Variáveis de ambiente (painel da Vercel)

- `DATABASE_URL` — string de conexão PostgreSQL (obrigatória)
- `APP_ENV=production` — obrigatória
- `CRON_SECRET` — o Vercel envia `Authorization: Bearer $CRON_SECRET`
  automaticamente no cron; agendadores externos podem usar o header
  `x-cron-secret` com o mesmo valor
- Opcionais: `ADMIN_PASSWORD`, `RATE_LIMIT_*`, `SMTP_*`, `LOG_TO_FILE`

### Intervalo de coleta

- **Plano Pro:** o cron do `vercel.json` já roda a cada 30 min
- **Plano Hobby:** o cron da Vercel roda no mínimo 1x/dia. Para intervalos
  menores, use um agendador externo gratuito (cron-job.org, Upstash QStash)
  chamando `GET /cron/monitor` com o header `x-cron-secret`

### Quando migrar para arquitetura híbrida

A arquitetura Vercel-only atende bem até ~40-50 produtos (limite de 60s
por invocação). Migre a API/worker para Render/Railway/VPS se:

- a base passar desse porte (ou divida o ciclo em lotes)
- os e-commerces bloquearem o IP da Vercel (IP de datacenter)

O `docker-compose.yml` continua sendo a forma correta de rodar localmente
com PostgreSQL (API + worker com loop infinito), e serve de plano B.

> Nota: o Redis foi removido da stack — nenhum código o utilizava. Se adicionar
> cache no futuro, reintroduza `REDIS_URL` no settings e no docker-compose.

> Nota: a integração via WhatsApp (webhook da Meta) foi removida — o projeto
> passou a ser acessado pelo cliente via página web (dashboard). O histórico
> dessa integração permanece no git.

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
- configure `DATABASE_URL`, `APP_ENV=production`
- publique o worker como service worker separado com comando:

```bash
python -m app.workers.price_worker
```

## Deploy local em Windows

Use o script de implantação:

```powershell
.\deploy\deploy_local.ps1
```

## Checklist de execução em máquina real

> **Toda a documentação e scripts de deploy estão centralizados na pasta
> [`deploy/`](deploy/README.md)** — guia de produção ([PRODUCTION.md](deploy/PRODUCTION.md)),
> checklist de validação ([CHECKLIST.md](deploy/CHECKLIST.md)) e modelo de
> variáveis de ambiente ([production.env.example](deploy/production.env.example)).

Consulte [deploy/CHECKLIST.md](deploy/CHECKLIST.md) para a sequência completa de validação e operação em produção.

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

- cadastro de produtos pelo dashboard
- histórico de preços com gráfico interativo (ECharts)
- categorias (Notebook, Tablet, Monitor, Fone, Mouse, Teclado)
- alertas com e-mail opcional (SMTP)
- popup de novas ofertas
- login administrativo opcional + rate limit
- dashboard web com paginação e filtros
- testes automatizados passando (40+)
- monitoramento de saúde
- backup do banco
- logs rotativos
