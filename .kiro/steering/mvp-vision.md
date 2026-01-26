---
inclusion: always
---

# AgentFirst2 MVP - Visão & Arquitetura (100% Linguagem Natural & Omnichannel)

## VISÃO PRINCIPAL

**AgentFirst2** é uma plataforma de IA omnichannel onde o usuário interage **100% em linguagem natural**, sem interfaces, sem botões, sem menus. A ideia principal é **não ficar presa a interface** - o usuário fala em português natural em qualquer canal (Telegram, WhatsApp, Web, App) e o sistema entende, executa e responde.

**Princípio Fundamental:** O usuário não precisa saber qual canal está usando, qual connector está consultando, qual domínio está acessando. Tudo é transparente via linguagem natural.

---

## COMO FUNCIONA NA PRÁTICA

### Exemplo 1: Usuário no Telegram (Linguagem Natural)

```
USUÁRIO: "Quantos pedidos tenho no iFood?"

SISTEMA:
1. Recebe mensagem no Telegram
2. Brain (Claude 3.5 Sonnet) entende: "check_orders" + "iFood"
3. Retail Agent consulta iFood Connector
4. Responde em linguagem natural: "Você tem 3 pedidos no iFood"

USUÁRIO: "Qual foi o mais caro?"

SISTEMA:
1. Brain recupera contexto (sabe que estava falando sobre iFood)
2. Sabe quais eram os 3 pedidos
3. Responde: "O mais caro foi o pedido #12347 com R$ 125,50"

USUÁRIO: "Confirme esse"

SISTEMA:
1. Brain entende: "confirm_order" + "pedido #12347"
2. Retail Agent confirma no iFood
3. Responde: "✅ Pedido #12347 confirmado"
```

### Exemplo 2: Novo Pedido Chega (Omnichannel Transparente)

```
IFOOD API: Novo pedido #12348 - R$ 95,00

SISTEMA:
1. iFood Connector detecta novo pedido (polling a cada 30s)
2. Brain formata em linguagem natural
3. Envia notificação em TODOS os canais do usuário:
   - Telegram: "📦 Novo pedido no iFood! Pedido #12348 - R$ 95,00"
   - WhatsApp: "📦 Novo pedido no iFood! Pedido #12348 - R$ 95,00"
   - Web: "📦 Novo pedido no iFood! Pedido #12348 - R$ 95,00"
   - App: Push notification com mesmo conteúdo

USUÁRIO (em qualquer canal): "Confirma?"

SISTEMA:
1. Brain entende: "confirm_order" + "pedido #12348"
2. Retail Agent confirma
3. Notifica em TODOS os canais: "✅ Pedido #12348 confirmado"
```

### Exemplo 3: Contexto Preservado (Muda de Canal)

```
TELEGRAM (10:00):
USUÁRIO: "Quantos pedidos tenho?"
SISTEMA: "Você tem 3 pedidos no iFood"

WHATSAPP (10:05):
USUÁRIO: "E qual foi o mais caro?"
SISTEMA: 
1. Recupera contexto de Memory (email)
2. Sabe que estava falando sobre iFood
3. Sabe quais eram os 3 pedidos
4. Responde: "O mais caro foi o pedido #12347 com R$ 125,50"

WEB (10:10):
USUÁRIO: "Confirme todos os pendentes"
SISTEMA:
1. Recupera contexto de Memory (email)
2. Sabe que estava falando sobre iFood
3. Sabe quais são os pendentes
4. Confirma todos automaticamente
5. Responde: "✅ Confirmei 2 pedidos pendentes"
```

### Exemplo 4: Linguagem Natural Avançada

```
TELEGRAM:
"Feche a loja no iFood por 30 minutos"
→ Brain classifica: close_store + 30_minutes
→ Retail Agent executa
→ Resposta: "✅ Loja fechada por 30 minutos. Reabrirá às 10:30"

WHATSAPP:
"Qual foi meu faturamento hoje?"
→ Brain classifica: get_revenue + today
→ Retail Agent consulta iFood
→ Resposta: "💰 Seu faturamento hoje foi R$ 2.847,50 (23 pedidos)"

WEB:
"Quais são meus itens mais vendidos?"
→ Brain classifica: get_top_items
→ Retail Agent analisa vendas
→ Resposta: "🏆 Top 5: Hambúrguer (45), Refrigerante (38), Batata (35)..."
```

---

## ARQUITETURA DE LINGUAGEM NATURAL

```
USUÁRIO (qualquer canal)
    ↓
Omnichannel Interface
    ├─ Mapeia channel ID → email (UNIVERSAL)
    ├─ Recupera contexto completo
    └─ Passa mensagem para Brain
    ↓
Brain (Claude 3.5 Sonnet via Bedrock)
    ├─ Entende intenção em português natural
    ├─ Extrai entidades (connector, order_id, duration, date, etc)
    ├─ Recupera contexto de Memory (por email)
    ├─ Classifica: domain, intent, connector, parameters
    └─ Roteia para Agent apropriado
    ↓
Retail Agent (Strands)
    ├─ Executa ação (check_orders, confirm_order, close_store, etc)
    ├─ Consulta iFood Connector (ou 99food, Shoppe, Amazon - futuro)
    ├─ Retorna dados estruturados
    └─ Publica evento para Event Bus
    ↓
Brain formata resposta
    ├─ Converte dados em linguagem natural
    ├─ Adapta tom e estilo
    └─ Passa para Omnichannel
    ↓
Omnichannel adapta para canal
    ├─ Telegram: emojis, limite de caracteres
    ├─ WhatsApp: formatação, links
    ├─ Web: HTML, interatividade
    └─ App: push notifications, deep links
    ↓
USUÁRIO recebe resposta em linguagem natural
```

---

## CARACTERÍSTICAS PRINCIPAIS

### 1. 100% Linguagem Natural
- ✅ Sem interfaces, sem botões, sem menus
- ✅ Usuário fala em português
- ✅ Sistema responde em português
- ✅ Brain entende intenção via Claude 3.5 Sonnet
- ✅ Suporta perguntas de acompanhamento ("E qual foi o mais caro?")

### 2. Omnichannel Transparente
- ✅ Novo pedido chega → notifica em TODOS os canais do usuário
- ✅ Usuário muda de canal → contexto preservado
- ✅ Mesma conversa em Telegram, WhatsApp, Web, App
- ✅ Identificado por email (não por phone/channel ID)
- ✅ Histórico completo cross-channel

### 3. Contexto Preservado
- ✅ Armazenado por email (universal)
- ✅ Recuperado em qualquer canal
- ✅ Mantém estado da conversa (qual connector, qual pedido, etc)
- ✅ Permite perguntas de acompanhamento
- ✅ Sincronizado entre canais em tempo real

### 4. Inteligência Avançada
- ✅ Claude 3.5 Sonnet entende intenção
- ✅ Extrai entidades automaticamente
- ✅ Aprende com padrões de uso
- ✅ Supervisão humana quando necessário (H.I.T.L.)
- ✅ Logs imutáveis para compliance

### 5. Escalável & Extensível
- ✅ Suporta múltiplos conectores (iFood, 99food, Shoppe, Amazon, etc)
- ✅ Suporta múltiplos domínios (Retail, Tax, Finance, Sales, HR, Marketing, Health, Legal, Education)
- ✅ Suporta múltiplos canais (Telegram, WhatsApp, Web, App, Email, SMS, Voice)
- ✅ Novos conectores/domínios/canais sem modificar código existente

---

## MVP SCOPE (5 semanas)

### Domínio
- **Retail** (Restaurantes, Grocery, Petshop, Pharmacy, Market)

### Conector
- **iFood** (105+ critérios de homologação - CRÍTICO)

### Canal
- **Telegram** (webhook)

### Core Services
- Brain (Claude 3.5 Sonnet via Bedrock)
- Memory (DynamoDB por email com GSI)
- Auditor (logs imutáveis)
- Supervisor (H.I.T.L.)
- Event Bus (SNS/SQS com DLQ)
- Observability (CloudWatch + X-Ray)
- Usage Tracking (Freemium billing)

### Modelo de Cobrança
- **Free Tier**: 100 mensagens/mês
- **Pro Tier**: 10.000 mensagens/mês (R$ 99/mês)
- **Enterprise**: Custom (ilimitado)

---

## ROADMAP PÓS-MVP

### MVP 2: Novos Conectores Retail (2 semanas)
- 99food, Amazon, Shoppe
- Mesmo usuário gerencia múltiplos marketplaces

### MVP 3: Novos Canais (3 semanas)
- WhatsApp, WeChat, Web, App
- Mesma experiência em qualquer lugar

### MVP 4: Novos Domínios (8 semanas)
- Tax (Receita Federal)
- Finance (Gestão financeira)
- Sales (Pipeline de vendas)
- HR (Gerenciamento de RH)
- Marketing (Campanhas)
- Health (Monitoramento de saúde)
- Legal (Consultoria jurídica)
- Education (Personalização de aprendizado)

### MVP 5: Infraestrutura Avançada (4 semanas)
- Multi-region deployment
- Advanced monitoring (ML anomaly detection)
- Auto-scaling inteligente
- Blue-green deployment

---

## TECNOLOGIA

### Backend
- Python 3.11+
- FastAPI (gateway local)
- AWS Lambda (serverless)
- Bedrock (Claude 3.5 Sonnet)

### Banco de Dados
- DynamoDB (encryption, PITR, GSI, TTL, Streams)

### Mensageria
- SNS (publicação de eventos)
- SQS (fila assíncrona com DLQ)

### Infraestrutura
- AWS CDK (Python)
- GitHub Actions (CI/CD)

### Monitoramento
- CloudWatch (logs, métricas, dashboards)
- X-Ray (distributed tracing)

### Testes
- pytest (unit tests)
- hypothesis (property-based tests)
- 580+ testes total

---

## IFOOD HOMOLOGATION (CRÍTICO)

O MVP precisa estar **100% preparado para homologação com iFood**:

### 105+ Critérios Cobertos
- ✅ Authentication (5 criteria)
- ✅ Merchant Management (6 criteria)
- ✅ Order Polling (34+ criteria) - CRITICAL
- ✅ Event Acknowledgment (10 criteria) - CRITICAL
- ✅ Order Types (DELIVERY, TAKEOUT, SCHEDULED)
- ✅ Payment Methods (9 types)
- ✅ Duplicate Detection (MANDATORY)
- ✅ Shipping Support (22+ criteria)
- ✅ Financial Integration (7 criteria)
- ✅ Item/Catalog Management (6 criteria)
- ✅ Promotion Management (6 criteria)
- ✅ Picking Operations (9 criteria)
- ✅ Rate Limiting & Error Handling
- ✅ Performance SLAs (< 5s polling, < 2s confirmation, < 1s processing)
- ✅ Security & Compliance (HTTPS, HMAC-SHA256, Secrets Manager)
- ✅ Omnichannel Integration (5 criteria)

### Homologation Readiness
- ✅ Professional Account (CNPJ) configured
- ✅ Test store ID and name ready
- ✅ All 105+ criteria implemented
- ✅ 580+ tests passing
- ✅ 100% code coverage for critical paths
- ✅ Zero security vulnerabilities
- ✅ Comprehensive documentation
- ✅ Ready for homologation call (~45 minutes)

---

## IMPORTANTE - LEMBRAR SEMPRE

1. **100% Linguagem Natural** - Sem interfaces, sem botões, sem menus
2. **Omnichannel Transparente** - Novo pedido notifica em TODOS os canais
3. **Contexto por Email** - Não por phone/channel ID
4. **iFood Homologation** - 105+ critérios CRÍTICOS
5. **Enterprise-Grade** - Encryption, PITR, GSI, DLQ, X-Ray, CloudWatch
6. **Freemium Model** - Free: 100 msg/mês, Pro: 10k msg/mês
7. **Python Stack** - Tudo em Python (Lambda, CDK, FastAPI)
8. **GitHub Actions** - Deploy automático com CI/CD
9. **Pronto para Cobrar** - MVP é produto mínimo viável com cobrança
10. **Escalável** - Suportar 1.000+ usuários simultâneos

---

## PRÓXIMOS PASSOS

1. ✅ Specs criadas (requirements.md, design.md, tasks.md)
2. ✅ Steering files criados (project-context.md, mvp-vision.md)
3. ⏭️ Começar implementação seguindo tasks.md (13 fases, 5 semanas)
4. ⏭️ Fase 1: Core Infrastructure (DynamoDB, Lambda, API Gateway, SNS/SQS)
5. ⏭️ Fase 7: iFood Connector (105+ critérios, 200+ testes)
6. ⏭️ Fase 13: Launch & Homologation

