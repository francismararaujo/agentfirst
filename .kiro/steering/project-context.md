---
inclusion: always
---

# AgentFirst2 - Project Context

## O QUE É O PROJETO

**AgentFirst2** é uma plataforma enterprise omnichannel de agentes especializados organizados por **domínios de negócio independentes** que compartilham um **kernel central** de inteligência.

**Objetivo**: Criar um assistente de IA omnichannel que gerencia operações de negócio em múltiplos domínios, funcionando em qualquer canal (Telegram, WhatsApp, Web, Email, SMS, Voice, App) com contexto unificado por email do usuário.

**3 Pilares Fundamentais**:
1. **Supervisor H.I.T.L.** - Decisões autônomas com intervenção humana quando necessário
2. **Auditoria Nativa** - Logs imutáveis de TUDO para compliance
3. **Memória Compartilhada** - Contexto persistente entre agentes para aprendizado contínuo

---

## ESTRUTURA DE DIRETÓRIOS

```
agentfirst/
├── .kiro/specs/                       # Specs do projeto
│   ├── core/app/                      # Core app specs
│   ├── core/strands-domain-pattern/   # Strands pattern specs
│   └── integration/ifood/             # iFood integration specs
│
├── app/                               # Código da aplicação
│   ├── config/                        # Configurações
│   │   ├── settings.py
│   │   ├── secrets_manager.py         # AWS Secrets Manager
│   │   └── __init__.py
│   │
│   ├── core/                          # Kernel Central
│   │   ├── brain.py                   # Orquestrador Claude 3.5 Sonnet
│   │   ├── memory.py                  # DynamoDB Memory Interface
│   │   ├── auditor.py                 # Compliance & Auditoria
│   │   ├── supervisor.py              # H.I.T.L. Controller
│   │   ├── event_bus.py               # SNS/SQS Event Bus
│   │   ├── monitoring.py              # CloudWatch Monitoring
│   │   ├── observability.py           # X-Ray Tracing
│   │   ├── self_learning.py           # ML Learning Engine
│   │   └── __init__.py
│   │
│   ├── omnichannel/                   # Interface Universal
│   │   ├── interface.py               # Omnichannel Universal
│   │   ├── nlp_universal.py           # NLP Universal
│   │   ├── authentication/            # Email-based Auth
│   │   ├── channel_adapters/          # Telegram, WhatsApp, Web, etc
│   │   ├── email_service/             # Gmail SMTP
│   │   ├── database/                  # DynamoDB Repositories
│   │   ├── integrations/              # Channel Integrations
│   │   └── __init__.py
│   │
│   ├── domains/                       # 9 Domínios de Negócio
│   │   ├── retail/                    # Varejo (iFood, 99food, Shoppe, Amazon)
│   │   ├── tax/                       # Impostos (Receita Federal)
│   │   ├── finance/                   # Finanças
│   │   ├── sales/                     # Vendas
│   │   ├── hr/                        # RH
│   │   ├── marketing/                 # Marketing
│   │   ├── health/                    # Saúde
│   │   ├── legal/                     # Legal
│   │   ├── education/                 # Educação
│   │   └── __init__.py
│   │
│   ├── shared/                        # Utilities Compartilhadas
│   │   ├── connectors/                # Base connectors
│   │   ├── processors/                # Document, OCR, STT, TTS
│   │   ├── engines/                   # Shared engines
│   │   └── utils/                     # Helpers
│   │
│   ├── lambda_handler.py              # AWS Lambda Entry Point
│   ├── main.py                        # FastAPI Gateway (local dev)
│   ├── requirements.txt
│   └── tests/                         # 500+ testes
│
├── infra/                             # Infraestrutura AWS
│   ├── cdk/                           # AWS CDK (Python)
│   │   ├── app.py                     # CDK App
│   │   ├── stacks/
│   │   │   ├── core_stack.py          # DynamoDB, SNS, SQS
│   │   │   ├── lambda_stack.py        # Lambda, API Gateway
│   │   │   ├── strands_stack.py       # Strands Domain Pattern
│   │   │   └── deployment_stack.py    # Blue-Green Deployment
│   │   └── requirements.txt
│   │
│   └── ops/                           # Operações
│       ├── cicd/                      # GitHub Actions
│       ├── monitoring/                # CloudWatch, X-Ray
│       ├── multi_region/              # Multi-region setup
│       └── scaling/                   # Auto-scaling
│
├── .github/
│   └── workflows/
│       └── deploy.yml                 # GitHub Actions CI/CD
│
└── README.md
```

---

## SERVIÇOS AWS UTILIZADOS

### Computação
- **AWS Lambda**: Execução de funções serverless (512MB, 30s timeout, X-Ray tracing, VPC)
- **API Gateway**: Gateway HTTP regional com CloudWatch logging e rate limiting

### Armazenamento & Banco de Dados
- **DynamoDB** (Enterprise-Grade):
  - Encryption at rest (AWS managed)
  - Point-in-Time Recovery (PITR) habilitado
  - Global Secondary Indexes (GSI) para queries eficientes
  - TTL para expiração automática
  - DynamoDB Streams para event sourcing
  - Tables:
    - Users (por email)
    - Sessions (cross-channel, TTL 24h)
    - Memory (contexto persistente, GSI por domain, TTL 30 dias)
    - Audit Logs (imutáveis, TTL 1 ano, PITR)
    - Usage (rastreamento mensal)
    - Escalation (H.I.T.L., GSI por user)

### Mensageria & Eventos
- **SNS (Simple Notification Service)**: Publicação de eventos com delivery policy
- **SQS (Simple Queue Service)**: Fila de processamento assíncrono com:
  - KMS encryption
  - Dead Letter Queue (DLQ) com retention 14 dias
  - Message retention 4 dias
  - Visibility timeout 5 minutos

### IA & Machine Learning
- **Bedrock**: Claude 3.5 Sonnet para Brain (orquestração central)

### Segurança & Configuração
- **Secrets Manager**: Armazenamento seguro com rotation policies:
  - Telegram Bot Token
  - iFood OAuth credentials
  - Gmail SMTP credentials
  - Receita Federal API keys
  - Database credentials

### Monitoramento & Observabilidade
- **CloudWatch**:
  - Structured logging (JSON format)
  - Log groups por componente
  - Log retention policies
  - Custom metrics (business + technical)
  - Automated dashboards
- **X-Ray**: 
  - Distributed tracing habilitado
  - Service map visualization
  - Performance insights
- **CloudWatch Alarms** (Automáticos):
  - Lambda errors > 5
  - Lambda duration > 30s
  - DynamoDB throttling
  - SQS queue depth
  - API Gateway 5xx errors

### CI/CD & Deployment
- **GitHub Actions**: Pipeline de deployment com:
  - Unit tests + Property-based tests
  - Docker build e push para ECR
  - CDK deployment com rollback automático
  - Smoke tests pós-deploy
- **AWS CDK** (Python): Infrastructure as Code com:
  - Core Stack (DynamoDB, SNS, SQS)
  - Lambda Stack (Lambda, API Gateway, IAM)
  - Strands Stack (Advanced setup com GSI, PITR, encryption)
- **Blue-Green Deployment**: Zero-downtime updates

---

## COMPONENTES PRINCIPAIS

### Core (Kernel Compartilhado)

**Brain** (Orquestrador Central)
- Classifica intent do usuário
- Roteia para domínio apropriado
- Coordena entre agentes
- Usa Claude 3.5 Sonnet via Bedrock

**Memory Interface** (DynamoDB)
- Armazena contexto por email do usuário
- Histórico cross-channel
- Preferências e padrões
- TTL configurável

**Auditor** (Compliance)
- Logs imutáveis de TUDO
- Timestamp, agente, ação, entrada, saída, contexto
- Pronto para LGPD, HIPAA, compliance fiscal
- Rastreabilidade completa

**Supervisor** (H.I.T.L.)
- Avalia se decisão requer intervenção humana
- Notifica via Telegram com contexto
- Aprende com decisões humanas
- Mantém logs de decisões

**Event Bus** (SNS/SQS)
- Publica eventos assíncronos
- Garante entrega confiável
- Dead letter queue para falhas
- Comunicação inter-agentes

**Observability** (CloudWatch + X-Ray)
- Coleta métricas, traces, logs
- Dashboards em tempo real
- Alertas automáticos
- Drill-down completo

**Self-Learning** (ML)
- Captura padrões de decisão humana
- Ajusta modelos de classificação
- Sugere novos agentes
- Identifica oportunidades de otimização

### Omnichannel (Interface Universal)

**Omnichannel Interface**
- Agnóstica a canais
- Funciona igual em Telegram, WhatsApp, Web, Email, SMS, Voice, App
- Mantém contexto unificado por email

**Channel Adapters**
- Telegram (implementado)
- WhatsApp (futuro)
- Web (futuro)
- Email (futuro)
- SMS (futuro)
- Voice (futuro)
- App (futuro)

**Universal Authentication**
- Email-based (não phone/channel ID)
- OTP via email
- Cross-channel sessions
- 24-hour expiry

**NLP Universal**
- Entende intenção em linguagem natural
- Agnóstico a canal
- Faz perguntas clarificadoras
- Adapta tom e estilo

### Domínios (9 Agentes Especializados)

**Retail** (iFood, 99food, Shoppe, Amazon)
- Gerenciamento de pedidos
- Gerenciamento de estoque
- Previsão de demanda
- Otimização de preços

**Tax** (Receita Federal)
- Processamento de documentos fiscais
- Cálculo de impostos
- Compliance fiscal
- LGPD compliance

**Finance**
- Gestão financeira
- Análise de investimentos
- Planejamento
- Detecção de anomalias

**Sales**
- Pipeline de vendas
- Qualificação de leads
- Geração de propostas
- Negociação

**HR**
- Gerenciamento de funcionários
- Recrutamento
- Performance
- Retenção

**Marketing**
- Campanhas
- Segmentação
- Analytics
- ROI

**Health**
- Monitoramento de saúde
- Análise de riscos
- Recomendações
- Alertas de emergência

**Legal**
- Consultoria jurídica
- Geração de documentos
- Rastreamento de prazos
- Referência de especialistas

**Education**
- Personalização de aprendizado
- Rastreamento de progresso
- Validação de competências
- Preparação para certificações

---

## FLUXO DE DADOS (User Journey Completo)

```
1. Usuário envia mensagem em QUALQUER canal
   └─ Telegram: "Recebi um novo pedido?"

2. Channel Adapter recebe
   └─ Telegram Adapter converte para UniversalMessage

3. Omnichannel Interface processa
   ├─ Autentica por email (universal)
   ├─ Recupera sessão cross-channel
   ├─ Processa conteúdo
   └─ Entende intenção via NLP

4. Brain orquestra
   ├─ Avalia complexidade
   ├─ Classifica intent: domain=retail, intent=check_orders
   ├─ Recupera contexto de Memory
   └─ Determina se requer supervisão

5. Supervisor avalia
   ├─ Requer intervenção humana? NÃO
   └─ Roteia para Agent Retail

6. Agent Retail executa
   ├─ Consulta iFood Connector
   ├─ Faz polling de pedidos
   ├─ Retorna 3 pedidos pendentes
   └─ Publica evento: retail.orders_checked

7. Event Bus coordena
   ├─ Auditor registra transação
   ├─ Memory atualiza contexto
   ├─ Self-Learning captura padrão
   └─ Observability coleta métricas

8. Resposta adaptada para canal
   └─ Telegram: "📦 Você tem 3 pedidos pendentes"

9. Usuário muda para WhatsApp
   ├─ Mesmo email
   ├─ Mesma sessão
   ├─ Mesmo contexto
   └─ Mesmo histórico

10. Usuário: "Confirme o primeiro"
    ├─ Brain classifica: intent=confirm_order
    ├─ Agent Retail executa via iFood Connector
    ├─ iFood API confirma pedido
    ├─ Event Bus publica: order_confirmed
    └─ WhatsApp: "✅ Pedido confirmado"
```

---

## SERVIÇOS AWS QUE VOCÊ PRECISA

### Já Tem (Configurado)
- ✅ AWS Account (373527788609)
- ✅ Region: us-east-1
- ✅ Lambda (para webhook handlers)
- ✅ API Gateway (para webhooks)
- ✅ DynamoDB (para dados)
- ✅ Bedrock (para Claude 3.5 Sonnet)
- ✅ Secrets Manager (para credentials)
- ✅ CloudWatch (para logs)

### Precisa Configurar (MVP)
- ⚠️ SNS (para Event Bus com delivery policy)
- ⚠️ SQS (para fila com DLQ e KMS encryption)
- ⚠️ X-Ray (para distributed tracing)
- ⚠️ CloudWatch Alarms (automáticos)
- ⚠️ IAM Roles & Policies (least privilege)
- ⚠️ DynamoDB PITR (Point-in-Time Recovery)
- ⚠️ DynamoDB GSI (Global Secondary Indexes)
- ⚠️ DynamoDB Streams (event sourcing)
- ⚠️ KMS encryption (SNS/SQS)

### Opcional (Futuro)
- 🔄 CodeDeploy (para blue-green deployment avançado)
- 🔄 Lambda Layers (para shared code)
- 🔄 EventBridge (para event routing avançado)
- 🔄 Step Functions (para workflows complexos)
- 🔄 Multi-region deployment

---

## TECNOLOGIAS UTILIZADAS

**Backend**
- Python 3.11+
- FastAPI (gateway local)
- AWS Lambda (serverless)
- Bedrock (Claude 3.5 Sonnet)

**Banco de Dados**
- DynamoDB (NoSQL)
- TTL para expiração automática

**Mensageria**
- SNS (publicação de eventos)
- SQS (fila assíncrona)

**Infraestrutura**
- AWS CDK (Python)
- GitHub Actions (CI/CD)

**Monitoramento**
- CloudWatch (logs, métricas)
- X-Ray (distributed tracing)

**Testes**
- pytest (unit tests)
- hypothesis (property-based tests)
- 500+ testes total

---

## ESTRATÉGIA DE IMPLEMENTAÇÃO (Incremental)

### MVP 1: Retail + iFood + Telegram (5 semanas)
**Foco**: Produto mínimo viável com modelo de cobrança

**Incluído**:
- ✅ Retail Agent (Strands)
- ✅ iFood Connector (105+ critérios)
- ✅ Telegram Channel Adapter
- ✅ Core Services (Brain, Memory, Auditor, Supervisor, Event Bus)
- ✅ Omnichannel Interface (básico)
- ✅ **Freemium Billing** (Free: 100 msg/mês, Pro: 10k msg/mês, Enterprise: custom)
- ✅ Usage Tracking & Limits
- ✅ GitHub Actions CI/CD
- ✅ 400+ testes
- ✅ Pronto para cobrar

**Specs**: `.kiro/specs/mvp/`
- requirements.md
- design.md
- tasks.md

### MVP 2: Adicionar Conectores Retail (2 semanas)
- 🔄 99food Connector
- 🔄 Amazon Connector
- 🔄 Shoppe Connector

### MVP 3: Adicionar Canais (3 semanas)
- 🔄 WhatsApp Channel Adapter
- 🔄 WeChat Channel Adapter
- 🔄 Web Channel Adapter
- 🔄 App Channel Adapter

### MVP 4: Adicionar Domínios (8 semanas)
- 🔄 Tax Agent (Receita Federal)
- 🔄 Finance Agent
- 🔄 Sales Agent
- 🔄 HR Agent
- 🔄 Marketing Agent
- 🔄 Health Agent
- 🔄 Legal Agent
- 🔄 Education Agent

### MVP 5: Infraestrutura Avançada (4 semanas)
- 🔄 Multi-Region Deployment
- 🔄 Advanced Monitoring (ML anomaly detection)
- 🔄 Auto-Scaling Inteligente
- 🔄 Blue-Green Deployment

---

## MODELO DE COBRANÇA (Freemium)

### Free Tier
- 100 mensagens/mês
- 1 domínio (Retail)
- 1 canal (Telegram)
- Suporte básico
- **Objetivo**: Usuário testa sem risco

### Pro Tier (R$ 99/mês)
- 10.000 mensagens/mês
- Todos os domínios (Retail, Tax, Finance, etc)
- Todos os canais (Telegram, WhatsApp, Web, etc)
- Suporte prioritário
- Analytics básico
- **Objetivo**: Usuário paga quando precisa de mais

### Enterprise (Custom)
- Mensagens ilimitadas
- Deployment dedicado
- SLA garantido (99.9% uptime)
- Suporte 24/7
- Custom integrations
- **Objetivo**: Grandes clientes com necessidades específicas

### Implementação
- Usage Tracker conta mensagens por usuário
- Verificação de limite antes de processar
- Erro amigável quando limite atingido
- Link para upgrade na resposta
- Atualização automática de tier após pagamento

---

## IMPORTANTE

- **Usuário identificado por EMAIL** (não phone/channel ID)
- **Contexto unificado cross-channel** por email
- **100% LINGUAGEM NATURAL** - Sem interfaces, sem botões, sem menus
  - Usuário fala em português natural
  - Brain entende intenção via Claude 3.5 Sonnet
  - Resposta em linguagem natural adaptada para canal
  - Exemplos: "Quantos pedidos tenho?", "Feche a loja por 30 minutos", "Qual foi meu faturamento?"
- **Omnichannel Transparente** - Usuário não precisa saber qual canal está usando
  - Novo pedido chega → notifica em TODOS os canais do usuário
  - Usuário muda de canal → contexto preservado
  - Mesma conversa em Telegram, WhatsApp, Web, App
- **Logs imutáveis** para compliance (LGPD-ready)
- **Decisões autônomas** com supervisão humana (H.I.T.L.)
- **Aprendizado contínuo** de padrões
- **Extensível** - novos domínios sem modificar código existente
- **Strands Framework** - Cada domain agent é um Strands Agent com tools específicas
- **Implementação Incremental** - MVP 1 (Retail + iFood + Telegram), depois expandir
- **GitHub Actions** - Deploy automático de Lambdas com CI/CD
- **Freemium Model** - Cobrar por uso incremental (Free: 100 msg/mês, Pro: 10k msg/mês)
- **Foco em MVP** - 5 semanas para produto mínimo viável com cobrança
- **Enterprise-Grade from Day 1** - Best practices de mercado:
  - Encryption at rest (DynamoDB, SNS/SQS)
  - Point-in-Time Recovery (PITR) para disaster recovery
  - Global Secondary Indexes (GSI) para queries eficientes
  - Dead Letter Queues (DLQ) para reliable messaging
  - X-Ray distributed tracing para observability
  - CloudWatch alarms automáticos para proactive monitoring
  - Blue-green deployment para zero-downtime updates
  - Least privilege IAM roles para security
  - Structured logging (JSON) para compliance
  - Custom metrics para business intelligence
- **Python Stack** - Entire project em Python (Lambda, CDK, FastAPI)
- **Pronto para Escalar** - Suportar 1.000+ usuários simultâneos com auto-scaling
