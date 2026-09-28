# Checklist final de deploy

## 1) Preparação do ambiente
- [ ] Criar conta no Vercel
- [ ] Conectar este repositório
- [ ] Configurar variável `APP_ENV=production`
- [ ] Configurar `DATABASE_URL` em PostgreSQL externo
- [ ] Configurar `REDIS_URL` em serviço externo
- [ ] Definir `WHATSAPP_TOKEN` e demais chaves reais

## 2) Build e deploy
- [ ] Fazer push para GitHub
- [ ] Importar o projeto no Vercel
- [ ] Validar build do backend Python
- [ ] Validar endpoint `/health`
- [ ] Validar endpoint `/dashboard`
- [ ] Validar `/products`

## 3) Infra e produção
- [ ] Usar PostgreSQL externo em vez do SQLite
- [ ] Usar Redis externo em vez do local
- [ ] Ajustar worker para serviço separado
- [ ] Habilitar logs e monitoramento
- [ ] Validar webhook do WhatsApp em HTTPS

## 4) Segurança
- [ ] Não commitar `.env`
- [ ] Usar variáveis de ambiente do provedor
- [ ] Restringir acesso às chaves
- [ ] Habilitar HTTPS e domínio próprio

## 5) Validação final
- [ ] API online
- [ ] Dashboard acessível
- [ ] Banco funcionando
- [ ] Worker funcionando
- [ ] Alertas operando
- [ ] Backup configurado
