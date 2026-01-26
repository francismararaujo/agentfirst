"""
Unit tests for NLP Universal service.

Tests intent classification, entity extraction, and context-aware understanding.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from hypothesis import given, strategies as st

from app.omnichannel.nlp_universal import NLPUniversal
from app.omnichannel.nlp_models import (
    IntentType,
    EntityType,
    Entity,
    IntentClassification,
    NLPResult
)


@pytest.mark.unit
class TestNLPUniversal:
    """Tests for NLPUniversal service"""
    
    @pytest.fixture
    def nlp(self):
        """Create NLP service instance"""
        return NLPUniversal()
    
    @pytest.mark.asyncio
    async def test_understand_check_orders(self, nlp):
        """Test understanding 'check orders' intent"""
        # Act
        result = await nlp.understand("Quantos pedidos tenho?")
        
        # Assert
        assert result.classification.intent == IntentType.CHECK_ORDERS
        assert result.classification.confidence > 0.8
        assert result.classification.domain == "retail"
    
    @pytest.mark.asyncio
    async def test_understand_confirm_order(self, nlp):
        """Test understanding 'confirm order' intent"""
        # Act
        result = await nlp.understand("Confirme esse pedido")
        
        # Assert
        assert result.classification.intent == IntentType.CONFIRM_ORDER
        assert result.classification.confidence > 0.8
    
    @pytest.mark.asyncio
    async def test_understand_cancel_order(self, nlp):
        """Test understanding 'cancel order' intent"""
        # Act
        result = await nlp.understand("Cancela esse pedido")
        
        # Assert
        assert result.classification.intent == IntentType.CANCEL_ORDER
        assert result.classification.confidence > 0.8
    
    @pytest.mark.asyncio
    async def test_understand_close_store(self, nlp):
        """Test understanding 'close store' intent"""
        # Act
        result = await nlp.understand("Feche a loja por 30 minutos")
        
        # Assert
        assert result.classification.intent == IntentType.CLOSE_STORE
        assert result.classification.confidence > 0.8
    
    @pytest.mark.asyncio
    async def test_understand_get_revenue(self, nlp):
        """Test understanding 'get revenue' intent"""
        # Act
        result = await nlp.understand("Qual foi meu faturamento hoje?")
        
        # Assert
        assert result.classification.intent == IntentType.GET_REVENUE
        assert result.classification.confidence > 0.8
    
    @pytest.mark.asyncio
    async def test_understand_get_top_items(self, nlp):
        """Test understanding 'get top items' intent"""
        # Act
        result = await nlp.understand("Quais são meus itens mais vendidos?")
        
        # Assert
        assert result.classification.intent == IntentType.GET_TOP_ITEMS
        assert result.classification.confidence > 0.8
    
    @pytest.mark.asyncio
    async def test_extract_order_id(self, nlp):
        """Test extracting order ID from message"""
        # Act
        result = await nlp.understand("Confirme o pedido #12345")
        
        # Assert
        order_ids = [e for e in result.classification.entities if e.type == EntityType.ORDER_ID]
        assert len(order_ids) > 0
        assert order_ids[0].value == "12345"
    
    @pytest.mark.asyncio
    async def test_extract_connector(self, nlp):
        """Test extracting connector from message"""
        # Act
        result = await nlp.understand("Quantos pedidos tenho no iFood?")
        
        # Assert
        assert result.classification.connector == "ifood"
    
    @pytest.mark.asyncio
    async def test_extract_duration(self, nlp):
        """Test extracting duration from message"""
        # Act
        result = await nlp.understand("Feche a loja por 30 minutos")
        
        # Assert
        durations = [e for e in result.classification.entities if e.type == EntityType.DURATION]
        assert len(durations) > 0
        assert durations[0].value == "30"
    
    @pytest.mark.asyncio
    async def test_extract_date(self, nlp):
        """Test extracting date from message"""
        # Act
        result = await nlp.understand("Qual foi meu faturamento hoje?")
        
        # Assert
        dates = [e for e in result.classification.entities if e.type == EntityType.DATE]
        assert len(dates) > 0
        assert dates[0].value == "hoje"
    
    @pytest.mark.asyncio
    async def test_followup_question_which_was_most_expensive(self, nlp):
        """Test understanding follow-up question 'which was most expensive'"""
        # Arrange
        context = {
            'last_intent': 'check_orders',
            'last_connector': 'ifood'
        }
        
        # Act
        result = await nlp.understand("E qual foi o mais caro?", context)
        
        # Assert
        assert result.classification.intent == IntentType.GET_TOP_ITEMS
        assert result.classification.confidence > 0.6
    
    @pytest.mark.asyncio
    async def test_followup_question_confirm_that(self, nlp):
        """Test understanding follow-up question 'confirm that'"""
        # Arrange
        context = {
            'last_intent': 'check_orders',
            'last_connector': 'ifood'
        }
        
        # Act
        result = await nlp.understand("Confirme esse", context)
        
        # Assert
        assert result.classification.intent == IntentType.CONFIRM_ORDER
        assert result.classification.confidence > 0.6
    
    @pytest.mark.asyncio
    async def test_context_aware_connector(self, nlp):
        """Test using connector from context"""
        # Arrange
        context = {
            'last_connector': '99food'
        }
        
        # Act
        result = await nlp.understand("Quantos pedidos tenho?", context)
        
        # Assert
        assert result.classification.connector == "99food"
    
    @pytest.mark.asyncio
    async def test_unknown_intent(self, nlp):
        """Test handling unknown intent"""
        # Act
        result = await nlp.understand("xyz abc 123")
        
        # Assert
        assert result.classification.intent == IntentType.UNKNOWN
        assert result.classification.confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_multiple_entities(self, nlp):
        """Test extracting multiple entities"""
        # Act
        result = await nlp.understand("Confirme o pedido #12345 no iFood por 30 minutos")
        
        # Assert
        assert len(result.classification.entities) >= 3
        entity_types = [e.type for e in result.classification.entities]
        assert EntityType.ORDER_ID in entity_types
        assert EntityType.CONNECTOR in entity_types
        assert EntityType.DURATION in entity_types
    
    @pytest.mark.asyncio
    async def test_case_insensitive(self, nlp):
        """Test case-insensitive intent classification"""
        # Act
        result1 = await nlp.understand("Quantos pedidos tenho?")
        result2 = await nlp.understand("QUANTOS PEDIDOS TENHO?")
        result3 = await nlp.understand("QuAnToS pEdIdOs TeNhO?")
        
        # Assert
        assert result1.classification.intent == result2.classification.intent
        assert result2.classification.intent == result3.classification.intent


@pytest.mark.unit
class TestNLPModels:
    """Tests for NLP models"""
    
    def test_entity_creation(self):
        """Test creating Entity"""
        # Act
        entity = Entity(
            type=EntityType.ORDER_ID,
            value="12345",
            confidence=0.95
        )
        
        # Assert
        assert entity.type == EntityType.ORDER_ID
        assert entity.value == "12345"
        assert entity.confidence == 0.95
    
    def test_entity_to_dict(self):
        """Test Entity serialization"""
        # Arrange
        entity = Entity(
            type=EntityType.ORDER_ID,
            value="12345",
            confidence=0.95,
            start_pos=0,
            end_pos=10
        )
        
        # Act
        data = entity.to_dict()
        
        # Assert
        assert data['type'] == 'order_id'
        assert data['value'] == '12345'
        assert data['confidence'] == 0.95
    
    def test_entity_from_dict(self):
        """Test Entity deserialization"""
        # Arrange
        data = {
            'type': 'order_id',
            'value': '12345',
            'confidence': 0.95,
            'start_pos': 0,
            'end_pos': 10
        }
        
        # Act
        entity = Entity.from_dict(data)
        
        # Assert
        assert entity.type == EntityType.ORDER_ID
        assert entity.value == '12345'
    
    def test_intent_classification_creation(self):
        """Test creating IntentClassification"""
        # Act
        classification = IntentClassification(
            intent=IntentType.CHECK_ORDERS,
            confidence=0.95,
            domain="retail",
            connector="ifood"
        )
        
        # Assert
        assert classification.intent == IntentType.CHECK_ORDERS
        assert classification.confidence == 0.95
        assert classification.domain == "retail"
    
    def test_intent_classification_to_dict(self):
        """Test IntentClassification serialization"""
        # Arrange
        entity = Entity(
            type=EntityType.ORDER_ID,
            value="12345",
            confidence=0.95
        )
        classification = IntentClassification(
            intent=IntentType.CHECK_ORDERS,
            confidence=0.95,
            entities=[entity],
            domain="retail"
        )
        
        # Act
        data = classification.to_dict()
        
        # Assert
        assert data['intent'] == 'check_orders'
        assert len(data['entities']) == 1
        assert data['domain'] == 'retail'
    
    def test_nlp_result_creation(self):
        """Test creating NLPResult"""
        # Arrange
        classification = IntentClassification(
            intent=IntentType.CHECK_ORDERS,
            confidence=0.95
        )
        
        # Act
        result = NLPResult(
            classification=classification,
            language="pt-BR",
            confidence_overall=0.95
        )
        
        # Assert
        assert result.classification.intent == IntentType.CHECK_ORDERS
        assert result.language == "pt-BR"


@pytest.mark.property
class TestNLPProperties:
    """Property-based tests for NLP"""
    
    @given(st.sampled_from([
        "Quantos pedidos tenho?",
        "Confirme esse pedido",
        "Cancela esse pedido",
        "Feche a loja",
        "Qual foi meu faturamento?"
    ]))
    def test_intent_classification_always_returns_valid_intent(self, message):
        """Validates: Intent classification always returns valid intent type
        
        Property: result.intent is always a valid IntentType
        """
        # Arrange
        nlp = NLPUniversal()
        
        # Act
        import asyncio
        result = asyncio.run(nlp.understand(message))
        
        # Assert
        assert isinstance(result.classification.intent, IntentType)
        assert result.classification.intent in IntentType
    
    @given(st.text(min_size=1, max_size=500))
    def test_confidence_is_between_0_and_1(self, message):
        """Validates: Confidence score is always between 0 and 1
        
        Property: 0.0 <= confidence <= 1.0
        """
        # Arrange
        nlp = NLPUniversal()
        
        # Act
        import asyncio
        result = asyncio.run(nlp.understand(message))
        
        # Assert
        assert 0.0 <= result.classification.confidence <= 1.0
        assert 0.0 <= result.confidence_overall <= 1.0
    
    @given(st.text(min_size=1, max_size=500))
    def test_entities_have_valid_types(self, message):
        """Validates: All extracted entities have valid types
        
        Property: entity.type is always a valid EntityType
        """
        # Arrange
        nlp = NLPUniversal()
        
        # Act
        import asyncio
        result = asyncio.run(nlp.understand(message))
        
        # Assert
        for entity in result.classification.entities:
            assert isinstance(entity.type, EntityType)
            assert entity.type in EntityType
    
    @given(st.text(min_size=1, max_size=500))
    def test_entity_confidence_is_valid(self, message):
        """Validates: Entity confidence is between 0 and 1
        
        Property: 0.0 <= entity.confidence <= 1.0
        """
        # Arrange
        nlp = NLPUniversal()
        
        # Act
        import asyncio
        result = asyncio.run(nlp.understand(message))
        
        # Assert
        for entity in result.classification.entities:
            assert 0.0 <= entity.confidence <= 1.0
    
    @given(st.text(min_size=1, max_size=500))
    def test_domain_is_valid(self, message):
        """Validates: Domain is always valid
        
        Property: domain is one of supported domains
        """
        # Arrange
        nlp = NLPUniversal()
        
        # Act
        import asyncio
        result = asyncio.run(nlp.understand(message))
        
        # Assert
        assert result.classification.domain in ["retail", "tax", "finance", "sales", "hr", "marketing", "health", "legal", "education"]
