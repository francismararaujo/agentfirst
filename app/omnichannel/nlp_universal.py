"""
Universal NLP service for intent classification and entity extraction.

Processes natural language messages in Portuguese to understand user intent,
extract entities, and route to appropriate domain agents.
"""

from typing import Optional, List, Dict, Any
from app.omnichannel.nlp_models import (
    IntentType,
    EntityType,
    Entity,
    IntentClassification,
    NLPResult
)


class NLPUniversal:
    """
    Universal NLP service for understanding user intent in Portuguese.
    
    Handles:
    1. Intent classification (check_orders, confirm_order, etc)
    2. Entity extraction (order_id, connector, duration, etc)
    3. Context-aware understanding (follow-up questions)
    4. Domain routing (retail, tax, finance, etc)
    """
    
    # Intent patterns for Portuguese
    INTENT_PATTERNS = {
        IntentType.CHECK_ORDERS: [
            r"quantos pedidos",
            r"quais são os pedidos",
            r"me mostre os pedidos",
            r"listar pedidos",
            r"ver pedidos",
            r"pedidos pendentes",
            r"pedidos confirmados",
            r"meus pedidos"
        ],
        IntentType.CONFIRM_ORDER: [
            r"confirma",
            r"confirme",
            r"aceita",
            r"aceite",
            r"aprova",
            r"aprove",
            r"confirmar pedido",
            r"aceitar pedido"
        ],
        IntentType.CANCEL_ORDER: [
            r"cancela",
            r"cancele",
            r"rejeita",
            r"rejeite",
            r"nega",
            r"negar",
            r"cancelar pedido",
            r"rejeitar pedido"
        ],
        IntentType.CLOSE_STORE: [
            r"fecha",
            r"feche",
            r"fechar",
            r"fechar loja",
            r"fechar a loja",
            r"indisponível",
            r"indisponível por"
        ],
        IntentType.OPEN_STORE: [
            r"abre",
            r"abra",
            r"abrir",
            r"abrir loja",
            r"abrir a loja",
            r"disponível",
            r"reabrir"
        ],
        IntentType.GET_REVENUE: [
            r"faturamento",
            r"receita",
            r"ganho",
            r"lucro",
            r"vendas",
            r"quanto ganhei",
            r"quanto vendi",
            r"total de vendas"
        ],
        IntentType.GET_TOP_ITEMS: [
            r"itens mais vendidos",
            r"produtos mais vendidos",
            r"top itens",
            r"top produtos",
            r"mais vendido",
            r"bestseller",
            r"quais são os mais vendidos"
        ],
        IntentType.UPDATE_INVENTORY: [
            r"atualizar estoque",
            r"atualiza estoque",
            r"estoque",
            r"inventário",
            r"repor",
            r"reposição"
        ],
        IntentType.FORECAST_DEMAND: [
            r"previsão",
            r"demanda",
            r"quanto vou vender",
            r"previsão de vendas",
            r"tendência"
        ]
    }
    
    # Entity patterns for Portuguese
    ENTITY_PATTERNS = {
        EntityType.ORDER_ID: [
            r"pedido\s*#?(\d+)",
            r"#(\d+)",
            r"order\s*#?(\d+)"
        ],
        EntityType.CONNECTOR: [
            r"ifood",
            r"99food",
            r"shoppe",
            r"amazon",
            r"mercado livre"
        ],
        EntityType.DURATION: [
            r"(\d+)\s*minutos?",
            r"(\d+)\s*horas?",
            r"(\d+)\s*dias?"
        ],
        EntityType.DATE: [
            r"hoje",
            r"ontem",
            r"amanhã",
            r"esta semana",
            r"este mês",
            r"este ano"
        ]
    }
    
    def __init__(self, context_manager=None):
        """
        Initialize NLP service.
        
        Args:
            context_manager: Optional context manager for conversation history
        """
        self.context_manager = context_manager
    
    async def understand(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> NLPResult:
        """
        Understand user message and extract intent and entities.
        
        Args:
            text: User message in Portuguese
            context: Optional conversation context (for follow-up questions)
        
        Returns:
            NLPResult with classification and entities
        """
        # 1. Classify intent
        classification = await self._classify_intent(text, context)
        
        # 2. Extract entities
        entities = await self._extract_entities(text, classification)
        classification.entities = entities
        
        # 3. Determine domain and connector
        classification.domain = self._determine_domain(classification.intent)
        classification.connector = self._determine_connector(entities, context)
        
        # 4. Create result
        result = NLPResult(
            classification=classification,
            language="pt-BR",
            confidence_overall=classification.confidence
        )
        
        return result
    
    async def _classify_intent(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> IntentClassification:
        """
        Classify intent from user message.
        
        Args:
            text: User message
            context: Optional conversation context
        
        Returns:
            IntentClassification with intent and confidence
        """
        text_lower = text.lower()
        
        # Check for exact matches first
        best_intent = IntentType.UNKNOWN
        best_confidence = 0.0
        
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    confidence = 0.9  # High confidence for pattern match
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_intent = intent
                    break
        
        # If no pattern matched, check context for follow-up questions
        if best_intent == IntentType.UNKNOWN and context:
            best_intent, best_confidence = self._handle_followup(text, context)
        
        return IntentClassification(
            intent=best_intent,
            confidence=best_confidence,
            raw_text=text
        )
    
    async def _extract_entities(
        self,
        text: str,
        classification: IntentClassification
    ) -> List[Entity]:
        """
        Extract entities from user message.
        
        Args:
            text: User message
            classification: Intent classification (for context)
        
        Returns:
            List of extracted entities
        """
        import re
        
        entities = []
        text_lower = text.lower()
        
        # Extract order IDs
        for pattern in self.ENTITY_PATTERNS[EntityType.ORDER_ID]:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                order_id = match.group(1) if match.groups() else match.group(0)
                entities.append(Entity(
                    type=EntityType.ORDER_ID,
                    value=order_id,
                    confidence=0.95,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        # Extract connector
        for pattern in self.ENTITY_PATTERNS[EntityType.CONNECTOR]:
            if re.search(pattern, text_lower):
                connector = pattern.replace(r"\\", "")
                entities.append(Entity(
                    type=EntityType.CONNECTOR,
                    value=connector,
                    confidence=0.95
                ))
        
        # Extract duration
        for pattern in self.ENTITY_PATTERNS[EntityType.DURATION]:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                duration = match.group(1) if match.groups() else match.group(0)
                entities.append(Entity(
                    type=EntityType.DURATION,
                    value=duration,
                    confidence=0.90,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        # Extract date
        for pattern in self.ENTITY_PATTERNS[EntityType.DATE]:
            if re.search(pattern, text_lower):
                date_val = pattern.replace(r"\\", "")
                entities.append(Entity(
                    type=EntityType.DATE,
                    value=date_val,
                    confidence=0.85
                ))
        
        return entities
    
    def _determine_domain(self, intent: IntentType) -> str:
        """
        Determine domain based on intent.
        
        Args:
            intent: Classified intent
        
        Returns:
            Domain name (retail, tax, finance, etc)
        """
        # MVP only supports retail domain
        return "retail"
    
    def _determine_connector(
        self,
        entities: List[Entity],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Determine connector based on entities and context.
        
        Args:
            entities: Extracted entities
            context: Optional conversation context
        
        Returns:
            Connector name (ifood, 99food, etc) or None
        """
        # Check if connector was explicitly mentioned
        for entity in entities:
            if entity.type == EntityType.CONNECTOR:
                return entity.value.lower()
        
        # Check context for last used connector
        if context and context.get('last_connector'):
            return context['last_connector']
        
        # Default to iFood for MVP
        return "ifood"
    
    def _handle_followup(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> tuple:
        """
        Handle follow-up questions using conversation context.
        
        Examples:
        - "E qual foi o mais caro?" (And which was the most expensive?)
        - "Confirme esse" (Confirm that one)
        - "Qual foi o total?" (What was the total?)
        
        Args:
            text: User message
            context: Conversation context
        
        Returns:
            Tuple of (intent, confidence)
        """
        text_lower = text.lower()
        
        # Follow-up patterns that depend on context
        if any(word in text_lower for word in ["qual", "quais", "quanto", "como"]):
            # Question about previous context
            if context.get('last_intent') == 'check_orders':
                if "mais caro" in text_lower or "maior" in text_lower:
                    return IntentType.GET_TOP_ITEMS, 0.7
                elif "total" in text_lower or "faturamento" in text_lower:
                    return IntentType.GET_REVENUE, 0.7
        
        if any(word in text_lower for word in ["confirma", "confirme", "sim", "yes"]):
            # Confirmation of previous action
            if context.get('last_intent') == 'check_orders':
                return IntentType.CONFIRM_ORDER, 0.7
        
        if any(word in text_lower for word in ["cancela", "cancele", "não", "no"]):
            # Cancellation of previous action
            if context.get('last_intent') == 'check_orders':
                return IntentType.CANCEL_ORDER, 0.7
        
        return IntentType.UNKNOWN, 0.0
