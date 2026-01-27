# 📱 Tutorial Telegram - AgentFirst2

Guia completo para usar o AgentFirst2 no Telegram de forma eficiente.

## 🚀 **Primeiros Passos**

### **1. Encontrar o Bot**
1. **Abra o Telegram** no seu celular ou computador
2. **Busque por**: `@AgentFirst2Bot` ou clique [aqui](https://t.me/AgentFirst2Bot)
3. **Clique em "Iniciar"** ou envie `/start`

### **2. Primeiro Contato**
```
🤖 Bot: 👋 Olá! Bem-vindo ao AgentFirst!

        🍔 Sou seu assistente para gerenciar pedidos do iFood.

        Para começar, preciso do seu email para identificá-lo 
        em todos os canais.

        📧 Por favor, envie seu email:

👤 Você: joao@pizzariaboa.com

🤖 Bot: 🎉 Cadastro realizado com sucesso!

        📧 Email: joao@pizzariaboa.com
        🎯 Tier: Gratuito (100 mensagens/mês)

        🍔 Agora você pode gerenciar seus pedidos do iFood!

        Experimente:
        • "Quantos pedidos tenho?"
        • "Qual meu faturamento hoje?"
        • "Feche a loja por 30 minutos"
```

---

## 💬 **Como Conversar com o Bot**

### **✅ Linguagem Natural - Funciona!**

#### **Gestão de Pedidos**
```
👤 Você: Quantos pedidos tenho?
🤖 Bot: 📦 Você tem 3 pedidos no iFood:
        • Pedido #12345 - R$ 45,50 (Pendente)
        • Pedido #12346 - R$ 67,80 (Confirmado)
        • Pedido #12347 - R$ 125,00 (Pronto)

👤 Você: Confirme o primeiro
🤖 Bot: ✅ Pedido #12345 confirmado com sucesso!
        ⏰ Tempo estimado: 25 minutos

👤 Você: Feche a loja por 30 minutos
🤖 Bot: 🔒 Loja fechada por 30 minutos.
        🕐 Reabrirá automaticamente às 15:30
```

#### **Controle Financeiro**
```
👤 Você: Qual foi meu faturamento hoje?
🤖 Bot: 💰 Faturamento de hoje: R$ 1.247,50
        📊 23 pedidos • Ticket médio: R$ 54,24
        📈 +15% vs ontem

👤 Você: E esta semana?
🤖 Bot: 📅 Faturamento da semana: R$ 8.932,40
        📦 156 pedidos • 📈 +8% vs semana passada
```

#### **Analytics**
```
👤 Você: Quais meus itens mais vendidos?
🤖 Bot: 🏆 Top 5 itens mais vendidos hoje:
        1. 🍔 Hambúrguer Clássico (12 vendas)
        2. 🍟 Batata Frita (10 vendas)
        3. 🥤 Refrigerante (8 vendas)
        4. 🍕 Pizza Margherita (6 vendas)
        5. 🌭 Hot Dog (5 vendas)
```

### **❌ O que NÃO funciona**
```
❌ /pedidos
❌ GET_ORDERS
❌ pedidos()
❌ listar-pedidos
❌ cmd:orders
```

**💡 Dica**: Fale como você falaria com uma pessoa! O bot entende português natural.

---

## 🔔 **Notificações Automáticas**

### **Novos Pedidos**
```
🤖 Bot: 📦 NOVO PEDIDO!
        
        🆔 Pedido: #12348
        💰 Valor: R$ 89,50
        👤 Cliente: Maria S.
        📍 Entrega: Rua das Flores, 123
        ⏰ Prazo: 35-45 min
        
        💳 Pagamento: Cartão Visa ****1234
        
        🍔 Itens:
        • 2x Hambúrguer Especial
        • 1x Batata Grande
        • 2x Refrigerante
        
        📝 Obs: "Sem cebola no hambúrguer"
        
        Responda: "Confirmar" ou "Rejeitar"

👤 Você: Confirmar
🤖 Bot: ✅ Pedido #12348 confirmado!
```

### **Alertas Importantes**
```
🤖 Bot: ⚠️ ATENÇÃO!
        
        🔴 Pedido #12340 está atrasado
        ⏰ Prazo original: 30 min (há 45 min)
        👤 Cliente: João P.
        
        Ações sugeridas:
        • "Atualizar tempo de entrega"
        • "Entrar em contato com cliente"
        • "Cancelar pedido"

👤 Você: Atualizar tempo para mais 15 minutos
🤖 Bot: ✅ Tempo atualizado! Cliente notificado.
        🕐 Nova previsão: 15 minutos
```

---

## 🤖 **Supervisão Humana (H.I.T.L.)**

### **Quando Acontece**
O sistema pode solicitar sua aprovação para decisões importantes:

```
👤 Você: Cancele o pedido de R$ 1.500

🤖 Bot: 🔍 Sua solicitação requer supervisão humana.

        📋 ID da escalação: esc_abc123
        💰 Valor: R$ 1.500,00
        ⚠️ Motivo: Valor alto para cancelamento
        
        ⏰ Aguarde análise ou aprove você mesmo:
        
        ✅ /approve esc_abc123
        ❌ /reject esc_abc123 [motivo]

👤 Você: /approve esc_abc123

🤖 Bot: ✅ Decisão aprovada!
        🔄 Cancelando pedido #12349...
        ✅ Pedido cancelado com sucesso!
```

### **Comandos de Supervisão**
```
/approve esc_abc123                    # Aprovar
/reject esc_abc123 Valor muito alto    # Rejeitar com motivo
```

---

## 📊 **Monitoramento de Uso**

### **Verificar Limite**
```
👤 Você: Quantas mensagens usei este mês?

🤖 Bot: 📊 USO MENSAL
        
        💬 Mensagens: 67/100 (67%)
        📅 Renovação: 01/02/2024 (em 8 dias)
        🎯 Tier: Gratuito
        
        💡 Dica: Considere upgrade para Pro se precisar 
        de mais mensagens!

👤 Você: Como fazer upgrade?

🤖 Bot: 💎 UPGRADE PARA PRO
        
        ✨ Benefícios:
        • 10.000 mensagens/mês
        • Todos os canais (WhatsApp, Web, App)
        • Suporte prioritário
        • Analytics avançado
        
        💰 Preço: R$ 99/mês
        
        🔗 Link personalizado:
        https://agentfirst.com/upgrade?email=joao@pizzariaboa.com
```

### **Alertas de Limite**
```
🤖 Bot: ⚠️ ALERTA DE USO
        
        📊 Você usou 80% das suas mensagens mensais
        💬 Restam: 20 mensagens
        📅 Renovação: 01/02/2024
        
        💎 Considere fazer upgrade para continuar usando:
        🔗 https://agentfirst.com/upgrade
        
        Ou aguarde a renovação automática.
```

---

## ⚙️ **Configurações**

### **Preferências de Notificação**
```
👤 Você: Configurar notificações

🤖 Bot: ⚙️ CONFIGURAÇÕES DE NOTIFICAÇÃO
        
        Escolha o que deseja receber:
        
        🔔 Novos pedidos: ✅ Ativo
        ⏰ Pedidos atrasados: ✅ Ativo
        💰 Relatório diário: ❌ Inativo
        📊 Relatório semanal: ✅ Ativo
        
        Para alterar, diga:
        "Desativar relatório diário"
        "Ativar todas as notificações"

👤 Você: Quero receber notificações apenas de pedidos acima de R$ 100

🤖 Bot: ✅ Configuração salva!
        
        🔔 Notificações ativas para:
        • Pedidos ≥ R$ 100,00
        • Pedidos atrasados (qualquer valor)
        • Relatório semanal
```

### **Horários de Funcionamento**
```
👤 Você: Configurar horário de funcionamento

🤖 Bot: 🕐 HORÁRIOS DE FUNCIONAMENTO
        
        📅 Segunda a Sexta: 11:00 - 22:00
        📅 Sábado: 11:00 - 23:00
        📅 Domingo: 18:00 - 22:00
        
        Para alterar:
        "Horário segunda a sexta 10h às 23h"
        "Domingo fechado"
        "Sábado 12h às 22h"

👤 Você: Segunda a sexta 10h às 23h, sábado 11h às 24h, domingo fechado

🤖 Bot: ✅ Horários atualizados!
        
        📅 Segunda a Sexta: 10:00 - 23:00
        📅 Sábado: 11:00 - 00:00
        📅 Domingo: Fechado
        
        🔄 Sincronizando com iFood...
        ✅ iFood atualizado!
```

---

## 🔧 **Comandos Especiais**

### **Comandos de Sistema**
```
/start          # Iniciar/reiniciar bot
/help           # Ajuda e comandos
/status         # Status da conta
/settings       # Configurações
```

### **Comandos de Supervisão** (Para supervisores)
```
/approve [id]   # Aprovar escalação
/reject [id]    # Rejeitar escalação
```

### **Comandos de Debug** (Para desenvolvedores)
```
/debug          # Informações de debug
/logs           # Últimos logs
/health         # Status do sistema
```

---

## 🎯 **Dicas de Uso Eficiente**

### **✅ Boas Práticas**

1. **Seja Natural**: Fale como falaria com uma pessoa
   ```
   ✅ "Quantos pedidos tenho hoje?"
   ❌ "GET_ORDERS_TODAY"
   ```

2. **Use Contexto**: O bot lembra da conversa
   ```
   Você: "Quantos pedidos tenho?"
   Bot: "3 pedidos"
   Você: "Confirme o primeiro"  ← Bot entende qual é o primeiro
   ```

3. **Seja Específico**: Quando necessário
   ```
   ✅ "Cancele o pedido 12345"
   ❌ "Cancele" (qual pedido?)
   ```

4. **Use Confirmações**: Para ações importantes
   ```
   Você: "Feche a loja"
   Bot: "Tem certeza? Isso impedirá novos pedidos."
   Você: "Sim, feche por 1 hora"
   ```

### **⚡ Atalhos Úteis**

```
"Status"           → Status geral da loja
"Pedidos"          → Lista de pedidos
"Faturamento"      → Faturamento do dia
"Relatório"        → Relatório completo
"Configurações"    → Menu de configurações
"Ajuda"            → Lista de comandos
```

### **🚫 Evite**

1. **Comandos de outros bots**: `/weather`, `/news`
2. **Linguagem técnica**: SQL, JSON, códigos
3. **Múltiplas perguntas**: Uma pergunta por mensagem
4. **Spam**: Aguarde a resposta antes da próxima pergunta

---

## 🆘 **Resolução de Problemas**

### **Bot não responde**
1. **Verifique conexão**: Internet funcionando?
2. **Reinicie**: Envie `/start`
3. **Bot correto**: [@AgentFirst2Bot](https://t.me/AgentFirst2Bot)
4. **Aguarde**: Máximo 30 segundos
5. **Contate suporte**: support@agentfirst.com

### **Resposta estranha**
1. **Reformule**: Tente perguntar de outra forma
2. **Seja específico**: Adicione mais detalhes
3. **Use contexto**: "Sobre o pedido anterior..."
4. **Reporte**: Se persistir, nos informe

### **Limite atingido**
```
🤖 Bot: ❌ Limite de mensagens atingido (100/100)
        
        📅 Renovação: 01/02/2024
        
        Opções:
        💎 Upgrade para Pro: 10.000 mensagens/mês
        ⏰ Aguardar renovação: Automática todo dia 1º
        
        🔗 Upgrade: https://agentfirst.com/upgrade
```

### **Erro de integração iFood**
```
🤖 Bot: ❌ Erro ao conectar com iFood
        
        Possíveis causas:
        • Credenciais OAuth expiradas
        • iFood fora do ar
        • Conta suspensa
        
        Soluções:
        1. "Testar conexão iFood"
        2. "Reconfigurar iFood"
        3. Contatar suporte: support@agentfirst.com
```

---

## 📱 **Recursos Avançados**

### **Notificações Push**
- **Ative**: Configurações do Telegram > Notificações
- **Personalize**: Sons diferentes para tipos de alerta
- **Silencie**: Modo "Não perturbe" em horários específicos

### **Mensagens Fixadas**
- **Fixe**: Mensagens importantes (relatórios, configurações)
- **Acesso rápido**: Toque na mensagem fixada

### **Histórico**
- **Busca**: Use a busca do Telegram para encontrar conversas antigas
- **Contexto**: Bot lembra das últimas 10 interações

### **Compartilhamento**
- **Relatórios**: Compartilhe relatórios com sua equipe
- **Screenshots**: Capture telas para documentação

---

## 🎓 **Exemplos Práticos**

### **Cenário 1: Manhã de Segunda**
```
👤 Você: Bom dia! Como foi o fim de semana?

🤖 Bot: 🌅 Bom dia! Aqui está o resumo do fim de semana:

        📅 SÁBADO (13/01)
        💰 Faturamento: R$ 2.847,50 (45 pedidos)
        ⭐ Avaliação média: 4.8/5
        
        📅 DOMINGO (14/01)
        💰 Faturamento: R$ 1.923,40 (28 pedidos)
        ⭐ Avaliação média: 4.9/5
        
        📊 TOTAL FIM DE SEMANA: R$ 4.770,90
        📈 +12% vs fim de semana anterior
        
        🏆 Item mais vendido: Hambúrguer Especial (23x)

👤 Você: Ótimo! Abra a loja para hoje

🤖 Bot: ✅ Loja aberta para segunda-feira!
        🕐 Horário: 11:00 - 22:00
        📦 Pronto para receber pedidos
```

### **Cenário 2: Pico de Movimento**
```
🤖 Bot: 🔥 PICO DE MOVIMENTO DETECTADO!
        
        📊 15 pedidos nos últimos 30 minutos
        ⏰ Tempo médio de preparo: 35 min
        📈 +200% vs horário normal
        
        💡 Sugestões:
        • Aumentar tempo de preparo
        • Pausar pedidos temporariamente
        • Ativar modo "rush"

👤 Você: Ativar modo rush

🤖 Bot: 🚀 MODO RUSH ATIVADO!
        
        ⚡ Tempo de preparo: 25 → 35 min
        📱 Equipe notificada
        🔔 Alertas de atraso desabilitados
        ⏰ Duração: 2 horas (até 20:30)
        
        💪 Vamos lá, equipe!
```

### **Cenário 3: Final do Dia**
```
👤 Você: Feche a loja e me dê o relatório do dia

🤖 Bot: 🔒 Loja fechada para novos pedidos.
        ⏳ Finalizando pedidos pendentes...
        
        📊 RELATÓRIO DO DIA (15/01/2024)
        
        💰 FINANCEIRO
        • Faturamento: R$ 3.247,80
        • Pedidos: 52
        • Ticket médio: R$ 62,46
        • Meta do dia: R$ 3.000 ✅ (+8%)
        
        📦 OPERACIONAL
        • Tempo médio preparo: 28 min
        • Taxa de cancelamento: 2,3%
        • Avaliação média: 4.7/5
        • Itens mais vendidos: Hambúrguer (18), Pizza (12)
        
        📈 COMPARATIVO
        • Ontem: +15% faturamento
        • Semana passada: +8% pedidos
        • Mês passado: +22% ticket médio
        
        🎯 METAS
        • Faturamento mensal: 67% (no prazo)
        • Avaliação: 4.7/5 (meta: 4.5) ✅
        
        👏 Excelente dia! Até amanhã!
```

---

**🎉 Agora você é um expert no Telegram do AgentFirst2!**

**Dúvidas?** 
- 📧 Email: support@agentfirst.com
- 💬 Telegram: @AgentFirstSupport
- 📚 Documentação: https://docs.agentfirst.com