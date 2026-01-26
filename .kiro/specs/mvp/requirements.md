# AgentFirst2 MVP - Requirements

## Overview

MVP focado em **Retail + iFood + Telegram** com modelo de cobrança Freemium integrado desde o início.

Objetivo: Criar um produto mínimo viável que possa ser cobrado e evoluído incrementalmente, utilizando infraestrutura enterprise-grade com best practices de mercado.

---

## Escopo do MVP

### Domínio
- **Retail** (Restaurantes, Grocery, Petshop, Pharmacy, Market)

### Conector
- **iFood** (105+ critérios de homologação)

### Canal
- **Telegram** (webhook)

### Core Services
- Brain (Claude 3.5 Sonnet via Bedrock)
- Memory (DynamoDB por email com GSI para queries por domínio)
- Auditor (logs imutáveis com ponto-in-time recovery)
- Supervisor (H.I.T.L. com escalação)
- Event Bus (SNS/SQS com DLQ)
- Observability (CloudWatch + X-Ray com alarmes automáticos)
- Usage Tracking (Freemium billing integrado)

### Modelo de Cobrança
- **Free Tier**: 100 mensagens/mês, 1 domínio, 1 canal
- **Pro Tier**: 10.000 mensagens/mês, todos os domínios, todos os canais
- **Enterprise**: Custom (ilimitado)

### Infraestrutura AWS (Enterprise-Grade)
- **DynamoDB**: Encryption, Point-in-Time Recovery, GSI, TTL, Streams
- **Lambda**: 512MB, 30s timeout, X-Ray tracing, CloudWatch logs
- **API Gateway**: Regional endpoint, CloudWatch logging
- **SNS/SQS**: Dead Letter Queue, KMS encryption, message retention
- **CloudWatch**: Alarmes automáticos, dashboards, métricas customizadas
- **X-Ray**: Distributed tracing, service map
- **Secrets Manager**: Credentials seguros
- **IAM**: Least privilege, role-based access

---

## Requisitos Funcionais

### 1. Autenticação & Onboarding

**1.1 Email-Based Authentication**
- Usuário fornece email
- Sistema verifica se existe
- Se novo: criar conta + tier Free
- Se existente: recuperar perfil
- Criar sessão cross-channel

**1.2 Tier Assignment**
- Novo usuário = Free Tier
- Armazenar tier no DynamoDB
- Aplicar limites baseado em tier

**1.3 Upgrade Flow**
- Usuário atinge limite
- Sistema oferece upgrade
- Link para página de pagamento
- Atualizar tier após pagamento

### 2. Retail Agent (Strands)

**2.1 Order Management**
- Polling de pedidos (30s)
- Confirmação de pedidos
- Cancelamento com motivo
- Atualização de status

**2.2 Inventory Management**
- Atualizar estoque
- Prever demanda
- Sugerir reposição

**2.3 iFood Connector (105+ Homologation Criteria)**
- OAuth 2.0 authentication (5 criteria)
- Merchant management (6 criteria)
- Order polling every 30 seconds (34+ criteria)
- Event acknowledgment for ALL events (10 criteria)
- Order types: DELIVERY (IMMEDIATE + SCHEDULED), TAKEOUT (34+ criteria)
- Payment methods: Card, Cash, PIX, Digital Wallet, Vouchers (9 criteria)
- Cancellation with valid reasons (6 criteria)
- Duplicate detection & deduplication (MANDATORY)
- Status sync from other apps
- Shipping support (22+ criteria)
- Financial integration (7 criteria)
- Item/Catalog management (6 criteria)
- Promotion management (6 criteria)
- Picking operations (9 criteria)
- Rate limiting & error handling
- Performance SLAs (< 5s polling, < 2s confirmation, < 1s processing)
- Security & compliance (HTTPS, HMAC-SHA256, Secrets Manager)
- Omnichannel integration (5 criteria)
- **Total: 105+ criteria for iFood homologation**

### 3. Telegram Channel

**3.1 Webhook Handler**
- Receber mensagens do Telegram
- Processar via Omnichannel Interface
- Enviar resposta adaptada

**3.2 Natural Language**
- Entender intenção em português
- Responder em linguagem natural
- Adaptar tom para Telegram

### 4. Usage Tracking & Limits

**4.1 Message Counter**
- Contar mensagens por usuário
- Armazenar em DynamoDB
- Reset mensal automático

**4.2 Limit Enforcement**
- Verificar limite antes de processar
- Retornar erro amigável se atingido
- Oferecer upgrade

**4.3 Tier Validation**
- Free: 100 mensagens/mês
- Pro: 10.000 mensagens/mês
- Enterprise: ilimitado

### 5. Omnichannel Interface (MVP) - 100% Linguagem Natural

**5.1 Message Processing**
- Receber mensagem do canal (Telegram, futuro: WhatsApp, Web, App)
- Autenticar por email (universal, não por phone/channel ID)
- Recuperar contexto completo (histórico, preferências, estado)
- Processar via Brain (Claude 3.5 Sonnet)
- Adaptar resposta para canal (emojis, caracteres, formato)
- **Tudo em linguagem natural - sem interfaces, sem botões, sem menus**

**5.2 Natural Language Understanding**
- Entender intenção em português natural
- Classificar ação (check_orders, confirm_order, close_store, get_revenue, etc)
- Extrair entidades (order_id, connector, duration, date, etc)
- Manter contexto da conversa (saber do que o usuário está falando)
- Suportar perguntas de acompanhamento ("E qual foi o mais caro?")

**5.3 Context Management**
- Armazenar contexto por email (não por channel)
- Recuperar histórico completo (cross-channel)
- Manter estado da conversa (qual connector, qual pedido, etc)
- Sincronizar contexto entre canais (Telegram → WhatsApp → Web)
- Permitir mudança de canal sem perder contexto

**5.4 Multi-Channel Notifications**
- Novo pedido chega no iFood → notifica em TODOS os canais do usuário
- Se conectado no Telegram → envia no Telegram
- Se conectado no WhatsApp → envia no WhatsApp
- Se conectado na Web → notificação na Web
- Se offline → armazena para quando voltar online
- Resposta em linguagem natural adaptada para cada canal

**5.5 Response Adaptation**
- Adaptar resposta para Telegram (emojis, limite de caracteres)
- Adaptar resposta para WhatsApp (formatação, links)
- Adaptar resposta para Web (HTML, interatividade)
- Adaptar resposta para App (push notifications, deep links)
- Manter significado e contexto em todas as adaptações

### 6. Brain (Orquestrador) - 100% Linguagem Natural

**6.1 Intent Classification**
- Usar Claude 3.5 Sonnet via Bedrock
- Classificar intenção do usuário em linguagem natural
- Extrair entidades (connector, order_id, duration, date, etc)
- Entender contexto (qual connector o usuário está falando)
- Rotear para domínio apropriado (retail, tax, finance, etc)
- **Exemplos:**
  - "Quantos pedidos tenho?" → domain=retail, intent=check_orders, connector=ifood
  - "Feche a loja por 30 minutos" → domain=retail, intent=close_store, connector=ifood, duration=30_minutes
  - "Qual foi meu faturamento hoje?" → domain=retail, intent=get_revenue, connector=ifood, date=today
  - "Confirme o primeiro pedido" → domain=retail, intent=confirm_order, connector=ifood, order_id=first

**6.2 Context Management**
- Recuperar contexto de Memory (por email)
- Fornecer histórico relevante ao Claude
- Manter estado da conversa (qual connector, qual pedido, etc)
- Permitir perguntas de acompanhamento ("E qual foi o mais caro?")
- Sincronizar contexto entre canais

**6.3 Agent Routing**
- Rotear para Retail Agent (MVP)
- Passar contexto e intenção
- Recuperar resposta
- Formatar resposta em linguagem natural
- Adaptar para canal do usuário

### 7. Auditor (Compliance)

**7.1 Immutable Logging**
- Registrar todas as operações
- Timestamp, agente, ação, entrada, saída
- Armazenar em DynamoDB
- TTL de 1 ano

**7.2 Compliance Reports**
- Gerar relatórios de auditoria
- Rastreabilidade completa
- Pronto para LGPD

### 8. Supervisor (H.I.T.L.)

**8.1 Decision Evaluation**
- Avaliar se decisão requer intervenção
- Notificar via Telegram
- Aguardar resposta humana

**8.2 Learning**
- Capturar padrões de decisão
- Melhorar classificação
- Atualizar modelos

---

## Requisitos Não-Funcionais

### Performance
- Processamento de mensagem: < 2 segundos
- Polling de pedidos: < 5 segundos
- Resposta do Brain: < 1 segundo

### Confiabilidade
- 99.9% uptime
- Retry automático com exponential backoff
- Graceful degradation

### Segurança
- OAuth 2.0 para iFood
- HMAC-SHA256 para webhooks
- Secrets Manager para credentials
- Rate limiting por usuário

### Escalabilidade
- Suportar 1.000+ usuários simultâneos
- Auto-scaling de Lambda
- DynamoDB on-demand

### Monitoramento
- CloudWatch logs
- X-Ray tracing
- Alertas automáticos
- Dashboard de métricas

---

## Dados & Modelos

### User
```
PK: email
SK: USER

- email (string, PK)
- tier (string) - free, pro, enterprise
- created_at (timestamp)
- updated_at (timestamp)
- telegram_id (number)
- usage_month (number) - mensagens este mês
- usage_total (number) - mensagens totais
- payment_status (string) - active, inactive, trial
- trial_ends_at (timestamp)
```

### Usage
```
PK: email
SK: USAGE#{year}#{month}

- email (string, PK)
- year (number)
- month (number)
- message_count (number)
- tier (string)
- reset_at (timestamp)
```

### Session
```
PK: email
SK: SESSION

- email (string, PK)
- session_id (string)
- authenticated (boolean)
- created_at (timestamp)
- expires_at (timestamp)
- active_channels (list)
- TTL: 86400 (24 horas)
```

### Memory
```
PK: email
SK: CONTEXT#{domain}

- email (string, PK)
- domain (string)
- context (map)
- updated_at (timestamp)
- TTL: 2592000 (30 dias)
```

### Audit Log
```
PK: email
SK: AUDIT#{timestamp}#{action_id}

- email (string, PK)
- timestamp (timestamp)
- action_id (string)
- agent (string)
- action (string)
- input (map)
- output (map)
- context (map)
- status (string)
- TTL: 31536000 (1 ano)
```

---

## Deployment

### GitHub Actions
- Trigger: push para main
- Build: Docker image
- Test: pytest + hypothesis
- Deploy: Lambda via SAM/CDK
- Rollback automático se falhar

### Infrastructure
- Lambda (webhook handler)
- API Gateway (Telegram webhook)
- DynamoDB (dados)
- SNS/SQS (eventos)
- Bedrock (Claude)
- Secrets Manager (credentials)
- CloudWatch (logs)
- X-Ray (tracing)

---

## Success Criteria

- ✅ Usuário pode se registrar com email
- ✅ Receber mensagens do Telegram
- ✅ Processar pedidos do iFood
- ✅ Responder em linguagem natural
- ✅ Rastrear uso e aplicar limites
- ✅ Oferecer upgrade quando limite atingido
- ✅ Logs imutáveis para compliance
- ✅ 100+ testes passando
- ✅ Deploy automático via GitHub Actions
- ✅ Pronto para cobrar por uso

---

## Roadmap Pós-MVP

### MVP 2: Novos Conectores Retail
- 99food
- Amazon
- Shoppe

### MVP 3: Novos Canais
- WhatsApp
- WeChat
- Web
- App

### MVP 4: Novos Domínios
- Tax (Receita Federal)
- Finance
- Sales
- HR
- Marketing
- Health
- Legal
- Education

### MVP 5: Infraestrutura Avançada
- Multi-region deployment
- Advanced monitoring (ML)
- Auto-scaling inteligente
- Blue-green deployment
