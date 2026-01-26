"""
Brain (Orquestrador Central) - Usa Claude 3.5 Sonnet via Bedrock

Responsabilidades:
1. Classificar intenção do usuário em linguagem natural
2. Rotear para domínio apropriado (Retail, Tax, Finance, etc)
3. Recuperar contexto de Memory
4. Coordenar execução de agentes
5. Formatar resposta em linguagem natural
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json

from app.omnichannel.models import ChannelType


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
    """
    Orquestrador central usando Claude 3.5 Sonnet via Bedrock
    """
    
    def __init__(self, bedrock_client, memory_service, event_bus, auditor):
        """
        Inicializa Brain
        
        Args:
            bedrock_client: Cliente Bedrock para Claude 3.5 Sonnet
            memory_service: Serviço de memória (DynamoDB)
            event_bus: Event bus (SNS/SQS)
            auditor: Serviço de auditoria
        """
        self.bedrock = bedrock_client
        self.memory = memory_service
        self.event_bus = event_bus
        self.auditor = auditor
        self.agents = {}  # Agentes por domínio
    
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
        try:
            # 1. Classificar intenção com Claude
            intent = await self._classify_intent(message, context)
            
            # 2. Recuperar contexto de Memory
            memory_context = await self.memory.get_context(context.email)
            context.memory = memory_context
            
            # 3. Rotear para agente apropriado
            if intent.domain not in self.agents:
                return f"Desculpe, ainda não tenho suporte para o domínio '{intent.domain}'"
            
            agent = self.agents[intent.domain]
            response_data = await agent.execute(intent, context)
            
            # 4. Formatar resposta em linguagem natural
            response = await self._format_response(response_data, intent, context)
            
            # 5. Atualizar memória
            await self.memory.update_context(context.email, {
                'last_intent': intent.action,
                'last_domain': intent.domain,
                'last_connector': intent.connector,
                'last_response': response,
                'timestamp': datetime.now().isoformat()
            })
            
            # 6. Registrar na auditoria
            await self.auditor.log_transaction(
                email=context.email,
                action=f"{intent.domain}.{intent.action}",
                input_data={'message': message, 'intent': intent.action},
                output_data={'response': response}
            )
            
            # 7. Publicar evento
            await self.event_bus.publish(
                topic=f"{intent.domain}.{intent.action}",
                message={
                    'email': context.email,
                    'intent': intent.action,
                    'connector': intent.connector,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            return response
            
        except Exception as e:
            await self.auditor.log_transaction(
                email=context.email,
                action="error",
                input_data={'message': message},
                output_data={'error': str(e)}
            )
            return f"Desculpe, ocorreu um erro ao processar sua mensagem: {str(e)}"
    
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
        # Preparar prompt para Claude
        prompt = self._build_classification_prompt(message, context)
        
        # Chamar Claude via Bedrock
        response = await self.bedrock.invoke_model(
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Parsear resposta
        response_text = response.get('content', [{}])[0].get('text', '{}')
        
        try:
            # Tentar extrair JSON da resposta
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                intent_data = json.loads(json_match.group())
            else:
                intent_data = json.loads(response_text)
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
        # Preparar prompt para Claude formatar resposta
        prompt = f"""
Você é um assistente de IA que formata respostas em linguagem natural.

Formate a seguinte resposta de forma clara, concisa e amigável em português:

Domínio: {intent.domain}
Ação: {intent.action}
Dados: {json.dumps(response_data)}

Responda em linguagem natural, sem JSON ou formatação técnica.
Seja conciso e direto.
"""
        
        # Chamar Claude para formatar
        response = await self.bedrock.invoke_model(
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Extrair texto da resposta
        formatted_response = response.get('content', [{}])[0].get('text', '')
        
        return formatted_response.strip()
    
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
