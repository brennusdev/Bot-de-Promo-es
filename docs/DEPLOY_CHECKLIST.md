# Checklist de deploy em máquina real

## 1. Preparação do ambiente

- [ ] Confirmar que Python 3.12+ está instalado
- [ ] Confirmar que Docker e Docker Compose estão instalados
- [ ] Confirmar que o diretório do projeto está acessível
- [ ] Criar o arquivo .env a partir de .env.example
- [ ] Ajustar valores reais de banco de dados

## 2. Configuração de ambiente

- [ ] Definir DATABASE_URL para o banco real
- [ ] Ajustar CHECK_INTERVAL_MINUTES

## 3. Validação local

- [ ] Instalar dependências com pip
- [ ] Executar pytest -q
- [ ] Confirmar import da aplicação
- [ ] Testar /health
- [ ] Testar /dashboard
- [ ] Testar /products

## 4. Subida com Docker

- [ ] Rodar docker compose build
- [ ] Rodar docker compose up -d
- [ ] Verificar containers ativos
- [ ] Verificar logs do worker
- [ ] Verificar logs da API
- [ ] Confirmar conectividade com PostgreSQL

## 5. Operação real

- [ ] Validar notificações de alerta
- [ ] Validar monitoramento periódico do worker
- [ ] Configurar rotina de backup do banco
- [ ] Configurar observabilidade e logs
- [ ] Configurar alertas de infraestrutura

## 6. Segurança

- [ ] NUNCA deixar credenciais em repositório público
- [ ] Usar arquivo .env em servidor real sem versionar
- [ ] Usar TLS/HTTPS em produção
- [ ] Restringir portas e acessos

## 7. Checklist final

- [ ] API respondendo em produção
- [ ] Worker rodando sem erro
- [ ] PostgreSQL estável
- [ ] Dashboard acessível
- [ ] Alertas funcionando
- [ ] Backups configurados
- [ ] Documentação final atualizada
