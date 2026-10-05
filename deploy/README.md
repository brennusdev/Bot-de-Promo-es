# 🚀 Deploy — Bot de Promoções

> **Fonte única de verdade para tudo relacionado a deploy.**
> Este diretório centraliza documentação, scripts e exemplos de configuração.
> Na raiz do projeto fica apenas o código e o README principal.

## 📁 Estrutura

| Arquivo                                            | Para que serve                                           |
| -------------------------------------------------- | -------------------------------------------------------- |
| [`README.md`](README.md)                           | Este índice (você está aqui)                             |
| [`CHECKLIST.md`](CHECKLIST.md)                     | Checklist passo a passo de validação para produção       |
| [`PRODUCTION.md`](PRODUCTION.md)                   | Guia de deploy em provedores (Vercel + Render/Railway)   |
| [`production.env.example`](production.env.example) | Modelo das variáveis de ambiente de produção             |
| [`deploy_local.ps1`](deploy_local.ps1)             | Script completo local: instala deps, testa e sobe Docker |
| [`run_local.ps1`](run_local.ps1)                   | Script rápido: sobe só a API local com reload            |

## 🧭 Qual usar? (roteiro rápido)

**Quero rodar no meu PC (Windows):**

```powershell
.\deploy\deploy_local.ps1    # completo (deps + testes + Docker)
# ou
.\deploy\run_local.ps1       # só a API, sem Docker
```

**Quero publicar na internet:**

1. Leia [`PRODUCTION.md`](PRODUCTION.md) — arquitetura e passos por provedor.
2. Copie [`production.env.example`](production.env.example) para o painel do provedor.
3. Valide item por item com [`CHECKLIST.md`](CHECKLIST.md).

**Estou subindo pela primeira vez e com medo de esquecer algo:**
→ siga o [`CHECKLIST.md`](CHECKLIST.md) do começo ao fim, sem pular itens.

## 🔗 Arquivos fora desta pasta (mas ligados ao deploy)

- `Dockerfile` e `docker-compose.yml` (raiz) — imagem e stack local com PostgreSQL.
- `vercel.json` e `api/index.py` (raiz) — entrypoint da Vercel.
- `runtime.txt` (raiz) — versão Python usada por provedores como Render/Railway.
- `requirements.txt` (raiz) — dependências.
- `.env.example` (raiz) — modelo de variáveis para desenvolvimento local.
