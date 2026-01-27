"""
Brain (Orquestrador Central) - Usa Claude 3.5 Sonnet via Bedrock

Responsabilidades:
1. Classificar intenção do usuário em linguagem natural
2. Rotear para domínio apropriado (Retail, Tax, Finance, etc)
3. Recuperar contexto de Memory
4. Coordenar execução de agentes
5. Formatar resposta em linguagem natural
"""

import json
import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from app.omnichannel.models import ChannelType
from app.core.auditor import Auditor, AuditCategory, AuditLevel
from app.core.supervisor import Supervisor

logger = logging.getLogger(__name__)


@dataclass
class Intent:
    """Classificação de intenção do usuário"""
    domain: str  # retail, tax, finance, sales, hr, marketing, health, legal, education
    action: str  # check_orders, confirm_order, cancel_order, etc
    connector: Optional[str] = None  # ifood, 99food, shoppe, amazon, etc
    confidence: float = 0.0  # 0-1
    entities: Dict[str, Any] = None  # order_id, duration, date, etc
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = {}


@dataclass
class Context:
    """Contexto da conversa"""
    email: str
    channel: ChannelType
    session_id: str
    history: list = None  # Histórico de mensagens
    user_profile: Dict[str, Any] = None  # Preferências, tier, etc
    memory: Dict[str, Any] = None  # Contexto persistente
    
    def __post_init__(self):
        if self.history is None:
            self.history = []
        if self.user_profile is None:
            self.user_profile = {}
        if self.memory is None:
            self.memory = {}


class Brain:
    """Orquestrador central usando Claude 3.5 Sonnet"""

    def __init__(self):
        """Initialize Brain with Bedrock client"""
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    async def classify_intent(self, message: str, user_email: str) -> Intent:
        """
        Classifica intenção do usuário usando Claude 3.5 Sonnet

        Args:
            message: Mensagem do usuário
            user_email: Email do usuário para contexto

        Returns:
            Intent classificado
        """
        try:
            # Preparar prompt para Claude
            prompt = self._build_classification_prompt(message, user_email)
            
            # Chamar Claude 3.5 Sonnet
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )

            # Parse response
            response_body = json.loads(response['body'].read())
            claude_response = response_body['content'][0]['text']
            
            # Parse Claude's JSON response
            try:
                classification_data = json.loads(claude_response)
            except json.JSONDecodeError:
                # Fallback se Claude não retornar JSON válido
                classification_data = {
                    "domain": "general",
                    "action": "unknown",
                    "confidence": 0.5
                }
            
            intent = Intent(
                domain=classification_data.get('domain', 'general'),
                action=classification_data.get('action', 'unknown'),
                connector=classification_data.get('connector'),
                confidence=classification_data.get('confidence', 0.5),
                entities=classification_data.get('entities', {})
            )

            logger.info(f"Intent classified: {intent.domain}.{intent.action} (confidence: {intent.confidence})")
            return intent

        except Exception as e:
            logger.error(f"Error classifying intent: {str(e)}")
            # Fallback classification
            return Intent(
                domain="general",
                action="unknown",
                confidence=0.0
            )

    def _build_classification_prompt(self, message: str, user_email: str) -> str:
        """Build prompt for intent classification"""
        
        return f"""
Você é o Brain do AgentFirst2, um sistema de IA omnichannel para restaurantes.

Sua tarefa é classificar a intenção do usuário e extrair entidades relevantes.

DOMÍNIOS DISPONÍVEIS:
- retail: Operações de restaurante (pedidos, vendas, estoque, faturamento)
- general: Conversas gerais, saudações, dúvidas sobre o sistema

AÇÕES PARA RETAIL:
- check_orders: Verificar pedidos (pendentes, confirmados, etc)
- confirm_order: Confirmar um pedido específico
- cancel_order: Cancelar um pedido
- check_revenue: Verificar faturamento/vendas
- manage_store: Abrir/fechar loja, pausar pedidos
- check_inventory: Verificar estoque
- get_analytics: Relatórios e análises

AÇÕES PARA GENERAL:
- greeting: Saudações, cumprimentos
- help: Pedidos de ajuda
- unknown: Não conseguiu classificar

USUÁRIO: {user_email}
MENSAGEM: "{message}"

Responda APENAS com um JSON válido no seguinte formato:
{{
    "domain": "retail|general",
    "action": "nome_da_acao",
    "connector": "ifood|99food|shoppe|amazon|null",
    "entities": {{
        "order_id": "número_do_pedido_se_mencionado",
        "time_period": "período_se_mencionado",
        "amount": "valor_se_mencionado"
    }},
    "confidence": 0.0-1.0
}}

EXEMPLOS:
- "Quantos pedidos tenho?" → {{"domain": "retail", "action": "check_orders", "connector": "ifood", "confidence": 0.9}}
- "Confirme o pedido 123" → {{"domain": "retail", "action": "confirm_order", "entities": {{"order_id": "123"}}, "confidence": 0.95}}
- "Qual foi meu faturamento hoje?" → {{"domain": "retail", "action": "check_revenue", "entities": {{"time_period": "today"}}, "confidence": 0.9}}
- "Oi" → {{"domain": "general", "action": "greeting", "confidence": 0.8}}
"""


class Brain:
    """
    Orquestrador central usando Claude 3.5 Sonnet via Bedrock
    """
    
    def __init__(self, bedrock_client=None, memory_service=None, event_bus=None, auditor=None, supervisor=None):
        """
        Inicializa Brain
        
        Args:
            bedrock_client: Cliente Bedrock para Claude 3.5 Sonnet
            memory_service: Serviço de memória (DynamoDB)
            event_bus: Event bus (SNS/SQS)
            auditor: Serviço de auditoria
            supervisor: Supervisor (H.I.T.L.)
        """
        if bedrock_client is None:
            self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        else:
            self.bedrock = bedrock_client
            
        self.memory = memory_service
        self.event_bus = event_bus
        self.auditor = auditor or Auditor()
        self.supervisor = supervisor or Supervisor(auditor=self.auditor)
        self.agents = {}  # Agentes por domínio
        self.model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    def register_agent(self, domain: str, agent):
        """
        Registra agente para domínio
        
        Args:
            domain: Nome do domínio (retail, tax, etc)
            agent: Instância do agente
        """
        self.agents[domain] = agent
    
    async def process(
        self,
        message: str,
        context: Context
    ) -> str:
        """
        Processa mensagem do usuário
        
        Args:
            message: Mensagem em linguagem natural
            context: Contexto da conversa
        
        Returns:
            Resposta em linguagem natural
        """
        start_time = datetime.now()
        
        try:
            # 1. Registrar início da operação na auditoria
            await self.auditor.log_transaction(
                email=context.email,
                action="brain.process_start",
                input_data={
                    'message': message,
                    'channel': context.channel.value,
                    'session_id': context.session_id
                },
                output_data={},
                agent="brain",
                category=AuditCategory.SYSTEM_OPERATION,
                level=AuditLevel.INFO,
                status="started",
                session_id=context.session_id,
                channel=context.channel.value
            )
            
            # 2. Classificar intenção com Claude
            intent = await self._classify_intent(message, context)
            
            # 3. Registrar classificação na auditoria
            await self.auditor.log_transaction(
                email=context.email,
                action="brain.classify_intent",
                input_data={
                    'message': message,
                    'context_memory': context.memory
                },
                output_data={
                    'domain': intent.domain,
                    'action': intent.action,
                    'connector': intent.connector,
                    'confidence': intent.confidence,
                    'entities': intent.entities
                },
                agent="brain",
                category=AuditCategory.SYSTEM_OPERATION,
                level=AuditLevel.INFO,
                status="success",
                session_id=context.session_id,
                channel=context.channel.value
            )
            
            # 4. Recuperar contexto de Memory
            if self.memory:
                memory_context = await self.memory.get_context(context.email)
                context.memory = memory_context
            
            # 5. Rotear para agente apropriado
            if intent.domain not in self.agents:
                error_message = f"Desculpe, ainda não tenho suporte para o domínio '{intent.domain}'"
                
                # Registrar erro na auditoria
                await self.auditor.log_transaction(
                    email=context.email,
                    action="brain.route_agent",
                    input_data={
                        'domain': intent.domain,
                        'available_domains': list(self.agents.keys())
                    },
                    output_data={'error': error_message},
                    agent="brain",
                    category=AuditCategory.SYSTEM_OPERATION,
                    level=AuditLevel.WARNING,
                    status="error",
                    error_message=error_message,
                    session_id=context.session_id,
                    channel=context.channel.value
                )
                
                return error_message
            
            agent = self.agents[intent.domain]
            
            # 6. Avaliar se requer supervisão humana (H.I.T.L.)
            proposed_decision = {
                "domain": intent.domain,
                "action": intent.action,
                "connector": intent.connector,
                "entities": intent.entities
            }
            
            requires_supervision, escalation_id = await self.supervisor.evaluate_decision(
                user_email=context.email,
                agent=intent.domain,
                action=intent.action,
                proposed_decision=proposed_decision,
                context={
                    "user_profile": context.user_profile,
                    "session_id": context.session_id,
                    "channel": context.channel.value,
                    "memory": context.memory
                },
                confidence=intent.confidence
            )
            
            if requires_supervision:
                # Decisão requer supervisão - retornar mensagem de espera
                supervision_message = (
                    f"🔍 Sua solicitação requer supervisão humana.\n\n"
                    f"📋 ID da escalação: {escalation_id}\n"
                    f"⏰ Aguarde a análise de um supervisor.\n\n"
                    f"Você será notificado quando a decisão for tomada."
                )
                
                # Registrar escalação na auditoria
                await self.auditor.log_transaction(
                    email=context.email,
                    action="brain.escalation_required",
                    input_data={
                        'intent': intent.action,
                        'domain': intent.domain,
                        'confidence': intent.confidence
                    },
                    output_data={
                        'escalation_id': escalation_id,
                        'requires_supervision': True
                    },
                    agent="brain",
                    category=AuditCategory.SYSTEM_OPERATION,
                    level=AuditLevel.WARNING,
                    session_id=context.session_id,
                    channel=context.channel.value
                )
                
                return supervision_message
            
            # 7. Executar via agente (decisão aprovada automaticamente)
            response_data = await agent.execute(intent, context)
            
            # 8. Formatar resposta em linguagem natural
            response = await self._format_response(response_data, intent, context)
            
            # 9. Atualizar memória
            if self.memory:
                await self.memory.update_context(context.email, {
                    'last_intent': intent.action,
                    'last_domain': intent.domain,
                    'last_connector': intent.connector,
                    'last_response': response,
                    'timestamp': datetime.now().isoformat()
                })
            
            # 10. Publicar evento
            if self.event_bus:
                await self.event_bus.publish(
                    topic=f"{intent.domain}.{intent.action}",
                    message={
                        'email': context.email,
                        'intent': intent.action,
                        'connector': intent.connector,
                        'timestamp': datetime.now().isoformat()
                    }
                )
            
            # 11. Calcular duração
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            # 12. Registrar sucesso na auditoria
            await self.auditor.log_transaction(
                email=context.email,
                action="brain.process_complete",
                input_data={
                    'message': message,
                    'intent': intent.action,
                    'domain': intent.domain
                },
                output_data={
                    'response': response,
                    'success': response_data.get('success', True)
                },
                agent="brain",
                category=AuditCategory.BUSINESS_OPERATION,
                level=AuditLevel.INFO,
                status="success",
                duration_ms=duration_ms,
                session_id=context.session_id,
                channel=context.channel.value
            )
            
            return response
            
        except Exception as e:
            # Calcular duração mesmo em caso de erro
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            error_message = f"Desculpe, ocorreu um erro ao processar sua mensagem: {str(e)}"
            
            # Registrar erro na auditoria
            await self.auditor.log_transaction(
                email=context.email,
                action="brain.process_error",
                input_data={'message': message},
                output_data={'error': str(e)},
                agent="brain",
                category=AuditCategory.ERROR_EVENT,
                level=AuditLevel.ERROR,
                status="error",
                error_message=str(e),
                duration_ms=duration_ms,
                session_id=context.session_id,
                channel=context.channel.value
            )
            
            logger.error(f"Error processing message: {str(e)}")
            return error_message
    
    async def _classify_intent(
        self,
        message: str,
        context: Context
    ) -> Intent:
        """
        Classifica intenção usando Claude 3.5 Sonnet
        
        Args:
            message: Mensagem do usuário
            context: Contexto da conversa
        
        Returns:
            Intent classificada
        """
        try:
            # Preparar prompt para Claude
            prompt = self._build_classification_prompt(message, context)
            
            # Chamar Claude via Bedrock
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            claude_response = response_body['content'][0]['text']
            
            # Parse Claude's JSON response
            try:
                # Tentar extrair JSON da resposta
                import re
                json_match = re.search(r'\{.*\}', claude_response, re.DOTALL)
                if json_match:
                    intent_data = json.loads(json_match.group())
                else:
                    intent_data = json.loads(claude_response)
            except json.JSONDecodeError:
                # Fallback: criar intent genérica
                intent_data = {
                    'domain': 'retail',
                    'action': 'unknown',
                    'confidence': 0.5
                }
            
            return Intent(
                domain=intent_data.get('domain', 'retail'),
                action=intent_data.get('action', 'unknown'),
                connector=intent_data.get('connector'),
                confidence=intent_data.get('confidence', 0.5),
                entities=intent_data.get('entities', {})
            )
            
        except Exception as e:
            logger.error(f"Error classifying intent: {str(e)}")
            # Fallback classification
            return Intent(
                domain="retail",
                action="unknown",
                confidence=0.0
            )
    
    def _build_classification_prompt(
        self,
        message: str,
        context: Context
    ) -> str:
        """
        Constrói prompt para classificação de intenção
        
        Args:
            message: Mensagem do usuário
            context: Contexto da conversa
        
        Returns:
            Prompt para Claude
        """
        return f"""
Você é um assistente de IA que classifica intenções de usuários em linguagem natural.

Classifique a seguinte mensagem em JSON com os campos:
- domain: retail, tax, finance, sales, hr, marketing, health, legal, education
- action: ação específica (check_orders, confirm_order, cancel_order, get_revenue, etc)
- connector: conector específico se aplicável (ifood, 99food, shoppe, amazon, etc)
- confidence: confiança da classificação (0-1)
- entities: dicionário com entidades extraídas (order_id, duration, date, etc)

Contexto:
- Email do usuário: {context.email}
- Canal: {context.channel.value}
- Histórico recente: {json.dumps(context.history[-3:] if context.history else [])}
- Memória: {json.dumps(context.memory)}

Mensagem do usuário:
"{message}"

Responda APENAS com JSON válido, sem explicações adicionais.
"""
    
    async def _format_response(
        self,
        response_data: Dict[str, Any],
        intent: Intent,
        context: Context
    ) -> str:
        """
        Formata resposta em linguagem natural
        
        Args:
            response_data: Dados da resposta do agente
            intent: Intenção classificada
            context: Contexto da conversa
        
        Returns:
            Resposta formatada em linguagem natural
        """
        try:
            # Preparar prompt para Claude formatar resposta
            prompt = f"""
Você é um assistente de IA que formata respostas em linguagem natural para restaurantes.

Formate a seguinte resposta de forma clara, concisa e amigável em português:

Domínio: {intent.domain}
Ação: {intent.action}
Dados: {json.dumps(response_data, ensure_ascii=False, indent=2)}

Responda em linguagem natural, sem JSON ou formatação técnica.
Seja conciso e direto.
Use emojis quando apropriado.
Se houver erro, explique de forma amigável.
"""
            
            # Chamar Claude para formatar
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            formatted_response = response_body['content'][0]['text']
            
            return formatted_response.strip()
            
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}")
            
            # Fallback: formatação simples
            if response_data.get('success'):
                if intent.action == 'check_orders':
                    orders = response_data.get('orders', [])
                    return f"📦 Você tem {len(orders)} pedidos"
                elif intent.action == 'confirm_order':
                    order_id = response_data.get('order_id')
                    return f"✅ Pedido {order_id} confirmado"
                elif intent.action == 'check_revenue':
                    revenue = response_data.get('revenue', {})
                    total = revenue.get('total_revenue', 0)
                    return f"💰 Faturamento: R$ {total:.2f}"
                else:
                    return "✅ Operação realizada com sucesso"
            else:
                error = response_data.get('error', 'Erro desconhecido')
                return f"❌ {error}"
    
    async def handle_event(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """
        Processa eventos do Event Bus
        
        Args:
            event_type: Tipo de evento (order_received, order_confirmed, etc)
            event_data: Dados do evento
        """
        # Recuperar contexto do usuário
        email = event_data.get('email')
        if not email:
            return
        
        context = Context(
            email=email,
            channel=ChannelType.TELEGRAM,  # Padrão
            session_id=event_data.get('session_id', ''),
            user_profile=event_data.get('user_profile', {})
        )
        
        # Processar evento
        if event_type == 'order_received':
            message = f"Novo pedido recebido: {event_data.get('order_id')}"
        elif event_type == 'order_confirmed':
            message = f"Pedido confirmado: {event_data.get('order_id')}"
        else:
            message = f"Evento: {event_type}"
        
        # Processar como mensagem
        await self.process(message, context)
    
    async def process_human_decision(
        self,
        escalation_id: str,
        decision: str,
        feedback: str = None,
        supervisor_id: str = None
    ) -> bool:
        """
        Processa decisão humana sobre escalação
        
        Args:
            escalation_id: ID da escalação
            decision: "approve" ou "reject"
            feedback: Feedback opcional do supervisor
            supervisor_id: ID do supervisor que decidiu
        
        Returns:
            True se processado com sucesso
        """
        return await self.supervisor.process_human_decision(
            escalation_id=escalation_id,
            decision=decision,
            feedback=feedback,
            supervisor_id=supervisor_id
        )
    
    def configure_supervisor(
        self,
        supervisor_id: str,
        name: str,
        telegram_chat_id: str,
        specialties: List[str] = None,
        priority_threshold: int = 1
    ):
        """
        Configura um supervisor no sistema H.I.T.L.
        
        Args:
            supervisor_id: ID único do supervisor
            name: Nome do supervisor
            telegram_chat_id: Chat ID do Telegram
            specialties: Especialidades (retail, finance, etc)
            priority_threshold: Prioridade mínima para notificar
        """
        self.supervisor.configure_supervisor(
            supervisor_id=supervisor_id,
            name=name,
            telegram_chat_id=telegram_chat_id,
            specialties=specialties,
            priority_threshold=priority_threshold
        )
