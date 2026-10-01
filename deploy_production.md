# Deploy pronto para produção

## 1) Estrutura sugerida

- Frontend: Vercel
- API: Render ou Railway
- Worker: Render/Railway ou VPS
- PostgreSQL: serviço externo
- Redis: serviço externo

## 2) Variáveis de ambiente

Use o arquivo `deploy-production.env.example` como base.

### Obrigatórias
- `APP_ENV=production`
- `DATABASE_URL`
- `WHATSAPP_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_WEBHOOK_VERIFY_TOKEN`

### Opcionais / condicionais
- `REDIS_URL` — só é OBRIGATÓRIA se você quiser exigir Redis no healthcheck.
  Nesse caso, defina também `REDIS_REQUIRED=true`.
  Comportamento do `/health` (REVISÃO):
  - Banco fora            -> 503 (crítico)
  - Redis fora, sem REDIS_REQUIRED -> 200 com status "degraded"
  - Redis fora, com REDIS_REQUIRED -> 503

## 3) Serviços

### Vercel
- publicar o frontend/dashboard
- usar `vercel.json`

### Render/Railway API
- build command: `pip install -r requirements.txt`
- start command: `uvicorn app.api:app --host 0.0.0.0 --port 8000`

### Render/Railway Worker
- build command: `pip install -r requirements.txt`
- start command: `python -m app.workers.price_worker`

## 4) Checklist de validação

- [ ] API responde em `/health`
- [ ] Dashboard responde em `/dashboard`
- [ ] Banco PostgreSQL conectado
- [ ] Redis conectado
- [ ] Worker processando itens
- [ ] Webhook HTTPS validado
- [ ] Logs funcionando
- [ ] Backup programado

## 5) Importante

NUNCA comitar `.env` real em repositório público.
Use variáveis de ambiente do provedor e secrets do serviço.
