# AgentFirst2 MVP

Plataforma omnichannel de IA para operações de varejo com **100% linguagem natural**.

## 🚀 Deploy Automático

Este projeto usa **GitHub Actions** para deploy automático. Funciona em qualquer dispositivo (Windows, Mac, Linux) sem instalação local.

### Como fazer deploy:

```bash
git add .
git commit -m "feat: nova funcionalidade"
git push origin main
# ↑ Deploy automático acontece!
```

### Monitorar deploy:
- Vá em: [GitHub Actions](https://github.com/seu-usuario/AgentFirst/actions)
- Acompanhe o progresso em tempo real

## 📱 API Endpoints

- **Health**: `https://d7p93u5agk.execute-api.us-east-1.amazonaws.com/prod/health`
- **Telegram**: `https://d7p93u5agk.execute-api.us-east-1.amazonaws.com/prod/webhook/telegram`
- **iFood**: `https://d7p93u5agk.execute-api.us-east-1.amazonaws.com/prod/webhook/ifood`

## 🛠️ Configuração (Uma vez só)

1. **GitHub Secrets** (Settings > Secrets > Actions):
   ```
   AWS_ACCESS_KEY_ID = AKIAVN575XRAXW7IYL7B
   AWS_SECRET_ACCESS_KEY = [sua chave secreta]
   AWS_REGION = us-east-1
   AWS_ACCOUNT_ID = 373527788609
   ```

2. **Push para main** → Deploy automático!

## 📖 Documentação

- [Deployment Guide](DEPLOYMENT.md) - Guia completo de deploy
- [Project Context](.kiro/steering/project-context.md) - Contexto do projeto
- [MVP Vision](.kiro/steering/mvp-vision.md) - Visão e arquitetura

## 🏗️ Arquitetura

- **Backend**: Python 3.11 + FastAPI + AWS Lambda
- **Database**: DynamoDB (NoSQL)
- **AI**: Claude 3.5 Sonnet via Bedrock
- **Deploy**: GitHub Actions + Docker + CDK
- **Monitoring**: CloudWatch + X-Ray

## 🎯 MVP Scope

- **Domínio**: Retail (restaurantes, grocery, etc.)
- **Conector**: iFood (105+ critérios de homologação)
- **Canal**: Telegram
- **Billing**: Freemium (Free: 100 msg/mês, Pro: 10k msg/mês)

## 🔧 Desenvolvimento Local

```bash
# Instalar dependências
pip install -r app/requirements.txt

# Rodar localmente
python app/main.py

# Testar
curl http://localhost:8000/health
```

## 📊 Status

- ✅ Core Infrastructure (DynamoDB, Lambda, API Gateway)
- ✅ Telegram Channel Adapter
- ✅ GitHub Actions CI/CD
- ⏭️ Brain (Claude 3.5 Sonnet)
- ⏭️ iFood Connector
- ⏭️ Billing System

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit: `git commit -m "feat: adicionar nova funcionalidade"`
4. Push: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.