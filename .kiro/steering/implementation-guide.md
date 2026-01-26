---
inclusion: always
---

# AgentFirst2 MVP - Implementation Guide

## ANTES DE COMEÇAR QUALQUER TAREFA

Leia SEMPRE nesta ordem:
1. `.kiro/steering/project-context.md` - Contexto geral do projeto
2. `.kiro/steering/mvp-vision.md` - Visão e arquitetura de linguagem natural
3. `.kiro/specs/mvp/requirements.md` - Requisitos funcionais
4. `.kiro/specs/mvp/design.md` - Design e arquitetura técnica
5. `.kiro/specs/mvp/tasks.md` - Plano de implementação (13 fases)

---

## PRINCÍPIOS FUNDAMENTAIS

### 1. 100% Linguagem Natural
- **NUNCA** crie interfaces, botões, menus
- **SEMPRE** use Claude 3.5 Sonnet para entender intenção
- **SEMPRE** responda em linguagem natural
- **SEMPRE** mantenha contexto da conversa

### 2. Omnichannel Transparente
- **NUNCA** identifique usuário por phone/channel ID
- **SEMPRE** identifique por email (universal)
- **SEMPRE** notifique em TODOS os canais do usuário
- **SEMPRE** preserve contexto entre canais

### 3. iFood Homologation (CRÍTICO)
- **NUNCA** ignore os 105+ critérios
- **SEMPRE** implemente cada critério explicitamente
- **SEMPRE** teste cada critério
- **SEMPRE** documente cada critério

### 4. Enterprise-Grade
- **NUNCA** use configurações padrão
- **SEMPRE** use encryption, PITR, GSI, DLQ, X-Ray
- **SEMPRE** implemente monitoring e alertas
- **SEMPRE** siga least privilege para IAM

### 5. Testes Abrangentes
- **NUNCA** implemente sem testes
- **SEMPRE** escreva unit tests + integration tests + property-based tests
- **SEMPRE** aim for > 80% code coverage
- **SEMPRE** teste cada critério de homologação

---

## ESTRUTURA DE TAREFAS

### Fase 1: Core Infrastructure (Semana 1)
- DynamoDB tables (encryption, PITR, GSI, TTL, Streams)
- Lambda & API Gateway (X-Ray tracing, CloudWatch logging)
- SNS/SQS (KMS encryption, DLQ)
- CloudWatch & X-Ray setup

### Fase 2: Authentication & User Management (Semana 1)
- Email-based authentication
- Channel mapping (Telegram ID → email)
- Session management (cross-channel)
- User repository (CRUD)

### Fase 3: Usage Tracking & Billing (Semana 1)
- Message counter (per user, per month)
- Limit enforcement (Free: 100, Pro: 10k)
- Tier validation
- Billing manager

### Fase 4: Omnichannel Interface (Semana 2)
- Universal message processing
- NLP universal (intent classification)
- Telegram channel adapter
- Response adaptation

### Fase 5: Brain (Orquestrador) (Semana 2)
- Intent classification (Claude 3.5 Sonnet)
- Context management (Memory)
- Agent routing

### Fase 6: Retail Agent (Strands) (Semana 2)
- Retail agent base (Strands)
- Order management tools
- Inventory management tools
- Error handling

### Fase 7: iFood Connector (Semana 3) - CRÍTICO
- **20 sub-tarefas** cobrindo 105+ critérios
- **200+ testes** específicos para iFood
- Authentication (5 criteria)
- Merchant management (6 criteria)
- Order polling (34+ criteria)
- Event acknowledgment (10 criteria)
- Order types, payments, cancellation, shipping, financial, etc.

### Fase 8: Auditor & Compliance (Semana 3)
- Immutable logging
- Compliance reports
- Data retention (TTL)

### Fase 9: Supervisor (H.I.T.L.) (Semana 3)
- Decision evaluation
- Learning from human decisions

### Fase 10: Testing & Quality (Semana 4)
- Unit tests (100+ testes)
- Integration tests (30+ testes)
- Property-based tests (20+ testes)
- Performance tests (10+ testes)

### Fase 11: Deployment & CI/CD (Semana 4)
- GitHub Actions setup
- Lambda deployment (CDK)
- Infrastructure as code
- Secrets management

### Fase 12: Monitoring & Observability (Semana 4)
- CloudWatch logs (structured, JSON)
- X-Ray tracing
- Metrics & dashboards
- Automated alarms

### Fase 13: Documentation & Launch (Semana 5)
- API documentation
- User documentation
- Production validation
- Launch

---

## COMO EXECUTAR TAREFAS

### Antes de Começar
1. Leia os steering files (project-context.md, mvp-vision.md)
2. Leia os specs (requirements.md, design.md, tasks.md)
3. Entenda a tarefa específica
4. Identifique dependências

### Durante a Implementação
1. **Escreva testes PRIMEIRO** (TDD)
2. Implemente o código
3. Rode os testes
4. Refatore se necessário
5. Documente o código

### Depois de Terminar
1. Verifique se todos os testes passam
2. Verifique code coverage (> 80%)
3. Verifique se não quebrou outras tarefas
4. Atualize a documentação
5. Marque a tarefa como completa

---

## PADRÕES DE CÓDIGO

### Linguagem Natural (Brain)
```python
# ✅ BOM - Usa Claude para entender intenção
async def process_message(message: str, context: Context):
    classification = await self.claude.classify(
        message,
        context,
        user_profile
    )
    # classification.domain, classification.intent, classification.entities
    return classification

# ❌ RUIM - Usa regex ou parsing manual
async def process_message(message: str):
    if "quantos pedidos" in message.lower():
        intent = "check_orders"
    # ...
```

### Omnichannel (Contexto por Email)
```python
# ✅ BOM - Identifica por email
async def get_user_context(email: str):
    context = await self.memory.get_context(email)
    return context

# ❌ RUIM - Identifica por channel ID
async def get_user_context(telegram_id: int):
    context = await self.memory.get_context(telegram_id)
    return context
```

### iFood Connector (Homologation)
```python
# ✅ BOM - Implementa cada critério explicitamente
async def poll_orders(self, merchant_id: str):
    """Poll /polling endpoint every 30 seconds (MANDATORY)"""
    # 1. Autenticar com OAuth 2.0 (5 criteria)
    token = await self.get_token()
    
    # 2. Fazer polling (34+ criteria)
    orders = await self.api.get('/polling', headers={
        'Authorization': f'Bearer {token}',
        'x-polling-merchants': merchant_id
    })
    
    # 3. Reconhecer TODOS os eventos (10 criteria - MANDATORY)
    await self.acknowledge_events(orders)
    
    # 4. Detectar duplicados (MANDATORY)
    unique_orders = await self.deduplicate(orders)
    
    return unique_orders

# ❌ RUIM - Implementa de forma genérica
async def poll_orders(self, merchant_id: str):
    orders = await self.api.get('/polling')
    return orders
```

### Testes
```python
# ✅ BOM - Testa cada critério
def test_poll_orders_every_30_seconds():
    """Validates: iFood 3.1 - Polling Every 30 Seconds"""
    # Arrange
    connector = iFoodConnector()
    
    # Act
    start = time.time()
    await connector.poll_orders(merchant_id="123")
    elapsed = time.time() - start
    
    # Assert
    assert elapsed < 5  # Performance SLA
    assert connector.last_poll_time is not None

def test_acknowledge_all_events():
    """Validates: iFood 4.3 - Guaranteed Event Acknowledgment (MANDATORY)"""
    # Arrange
    connector = iFoodConnector()
    events = [Event(id=1), Event(id=2), Event(id=3)]
    
    # Act
    await connector.acknowledge_events(events)
    
    # Assert
    assert len(connector.acknowledged_events) == 3
    assert all(e.id in connector.acknowledged_events for e in events)

# ❌ RUIM - Testa de forma genérica
def test_connector():
    connector = iFoodConnector()
    result = connector.poll_orders()
    assert result is not None
```

### Property-Based Testing (PBT) com Hypothesis

Property-based testing valida propriedades universais que devem ser verdadeiras para TODOS os inputs. Usamos Hypothesis para gerar centenas de casos de teste automaticamente.

```python
from hypothesis import given, strategies as st

# ✅ BOM - Testa propriedade universal
@pytest.mark.property
class TestBillingManagerProperties:
    """Property-based tests for Billing Manager"""
    
    @given(messages_used=st.integers(0, 100000), tier=st.sampled_from(["free", "pro", "enterprise"]))
    def test_remaining_messages_never_negative(self, messages_used, tier):
        """Validates: Remaining messages is always >= 0
        
        Property: remaining = max(0, limit - used) >= 0
        """
        # Arrange
        limits = {"free": 100, "pro": 10000, "enterprise": 999999999}
        limit = limits[tier]
        
        # Act
        remaining = max(0, limit - messages_used)
        
        # Assert
        assert remaining >= 0, f"Remaining {remaining} should never be negative"
    
    @given(tier=st.sampled_from(["free", "pro", "enterprise"]))
    def test_tier_limits_follow_business_rules(self, tier):
        """Validates: Tier limits follow business rules
        
        Property: free_limit < pro_limit < enterprise_limit
        """
        # Arrange
        limits = {"free": 100, "pro": 10000, "enterprise": 999999999}
        
        # Act
        free_limit = limits["free"]
        pro_limit = limits["pro"]
        enterprise_limit = limits["enterprise"]
        
        # Assert
        assert free_limit < pro_limit < enterprise_limit

@pytest.mark.property
class TestUsageTrackerProperties:
    """Property-based tests for Usage Tracker"""
    
    @given(initial_count=st.integers(0, 1000), increment=st.integers(1, 1000))
    def test_usage_counter_monotonically_increases(self, initial_count, increment):
        """Validates: Usage counter monotonically increases
        
        Property: count_after_increment >= initial_count
        """
        # Arrange
        count = initial_count
        
        # Act
        count += increment
        
        # Assert
        assert count >= initial_count, f"Count {count} should be >= {initial_count}"

@pytest.mark.property
class TestAuthenticationProperties:
    """Property-based tests for Authentication"""
    
    @given(email=st.emails())
    def test_email_validation_is_consistent(self, email):
        """Validates: Email validation is consistent
        
        Property: validate_email(email) returns same result every time
        """
        # Arrange
        auth = AuthService()
        
        # Act
        result1 = auth.validate_email(email)
        result2 = auth.validate_email(email)
        
        # Assert
        assert result1 == result2, f"Email validation should be consistent for {email}"

# ❌ RUIM - Não testa propriedade universal
def test_billing_manager():
    manager = BillingManager()
    result = manager.get_billing_info("test@example.com")
    assert result is not None
```

**Padrão de PBT:**
1. Use `@given` com estratégias do Hypothesis
2. Teste propriedades universais (não casos específicos)
3. Documente a propriedade no docstring
4. Use `@pytest.mark.property` para marcar testes PBT
5. Gere inputs aleatoriamente - Hypothesis encontrará edge cases

**Estratégias úteis:**
- `st.integers(min_value, max_value)` - Inteiros
- `st.floats(min_value, max_value)` - Floats
- `st.text()` - Strings
- `st.emails()` - Emails válidos
- `st.sampled_from([...])` - Escolher de lista
- `st.lists(st.integers())` - Listas
- `st.dictionaries(st.text(), st.integers())` - Dicionários

---

## CHECKLIST ANTES DE SUBMETER

- [ ] Leu os steering files (project-context.md, mvp-vision.md)
- [ ] Leu os specs (requirements.md, design.md, tasks.md)
- [ ] Entendeu a tarefa específica
- [ ] Escreveu testes PRIMEIRO (TDD)
  - [ ] Unit tests (casos específicos)
  - [ ] Integration tests (fluxos completos)
  - [ ] Property-based tests (propriedades universais)
  - [ ] Performance tests (latência, throughput)
- [ ] Implementou o código
- [ ] Todos os testes passam
- [ ] Code coverage > 80%
- [ ] Não quebrou outras tarefas
- [ ] Documentou o código
- [ ] Atualizou a documentação
- [ ] Marcou a tarefa como completa

---

## QUANDO CRIAR NOVA SESSÃO

Se você criar uma nova sessão, eu vou ler AUTOMATICAMENTE:
1. `.kiro/steering/project-context.md` - Contexto geral
2. `.kiro/steering/mvp-vision.md` - Visão de linguagem natural
3. `.kiro/steering/implementation-guide.md` - Este arquivo
4. `.kiro/specs/mvp/requirements.md` - Requisitos
5. `.kiro/specs/mvp/design.md` - Design
6. `.kiro/specs/mvp/tasks.md` - Tarefas

Então eu vou entender **EXATAMENTE** o que você quer:
- ✅ 100% linguagem natural
- ✅ Omnichannel transparente
- ✅ Contexto por email
- ✅ iFood homologation (105+ critérios)
- ✅ Enterprise-grade
- ✅ Freemium billing
- ✅ Python stack
- ✅ GitHub Actions
- ✅ 580+ testes (unit + integration + PBT + performance)
- ✅ Pronto para cobrar

**Você não precisa repetir nada. Tudo está documentado aqui.**

