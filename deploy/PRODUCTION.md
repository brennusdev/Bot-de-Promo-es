# Deploy pronto para produção (Vercel-only)

> **Fonte de verdade da arquitetura de produção.** Dois serviços, nada mais.

## 1) Estrutura

- **Vercel** — API FastAPI (`api/index.py`) + dashboard (`/dashboard`) + worker serverless (`/cron/monitor` disparado pelo cron do `vercel.json`)
- **PostgreSQL externo** — Neon ou Supabase (tier free serverless-friendly)

Não há API nem worker em Render/Railway nesse cenário. O `docker-compose.yml`
continua válido como forma de rodar localmente com Postgres (e como plano B
se a base de produtos crescer além do que o serverless suporta).

## 2) Variáveis de ambiente

Configure no painel da Vercel (Settings → Environment Variables).
Use `production.env.example` como base.

### Obrigatórias
- `APP_ENV=production`
- `DATABASE_URL` — string de conexão PostgreSQL (Neon/Supabase)

### Recomendadas
- `CRON_SECRET` — token forte. O Vercel Cron envia automaticamente
  `Authorization: Bearer $CRON_SECRET`; agendadores externos podem usar
  o header `x-cron-secret` com o mesmo valor.
- `ADMIN_PASSWORD` — protege as rotas de escrita (POST/DELETE).

### Opcionais
- `RATE_LIMIT_MAX_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS` (padrão: 10/60s,
  persistido no banco)
- `PRICE_RETENTION_DAYS` — retenção do histórico (padrão: 90)
- `REQUEST_DELAY_SECONDS` — pausa entre coletas (padrão: 1)
- `SMTP_*` / `ALERT_EMAIL_*` — alertas por e-mail
- `LOG_TO_FILE` — deixe VAZIO na Vercel (filesystem somente leitura)

## 3) Vercel

1. Conecte o repositório (Root Directory = raiz, Framework Preset = **Other**)
2. Build Command e Output Directory vazios — o `vercel.json` cuida de tudo
3. Configure as variáveis acima
4. O cron definido no `vercel.json` (`*/30 * * * *`) dispara `GET /cron/monitor`
   - **Plano Pro:** roda a cada 30 min
   - **Plano Hobby:** mínimo 1x/dia — para intervalos menores, use um
     agendador externo gratuito (cron-job.org, Upstash QStash) chamando
     `GET /cron/monitor` com o header `x-cron-secret`

## 4) PostgreSQL (Neon/Supabase)

1. Crie o banco e copie a connection string para `DATABASE_URL`
2. As tabelas são criadas automaticamente no primeiro acesso (`init_db`)
3. Backup: `pg_dump $DATABASE_URL > backup.sql` (o script `scripts/backup_db.py`
   é exclusivo para SQLite/local)

## 5) Checklist de validação

- [ ] `GET /health` → `{"status": "ok", "database": {"ok": true}}`
- [ ] `GET /dashboard` → HTML do dashboard
- [ ] `GET /cron/monitor` com Bearer → resumo do ciclo (`processed`)
- [ ] Runtime Logs da Vercel sem tracebacks
- [ ] Backup do Postgres programado

## 6) Limites do serverless (quando migrar)

A arquitetura Vercel-only atende bem até ~40-50 produtos (60s por invocação).
Migre a API/worker para Render/Railway/VPS se:

- a base passar desse porte (ou divida o ciclo em lotes)
- os e-commerces bloquearem o IP da Vercel (IP de datacenter)

Nesse cenário híbrido, o worker volta a ser o loop infinito
(`python -m app.workers.price_worker`) fora da Vercel.

## 7) Importante

NUNCA comitar `.env` real em repositório público.
Use variáveis de ambiente do provedor e secrets do serviço.
