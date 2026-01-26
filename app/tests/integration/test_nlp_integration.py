"""
Integration tests for NLP Universal service.

Tests complete NLP workflows including intent classification,
entity extraction, and context-aware understanding.
"""

import pytest
from app.omnichannel.nlp_universal import NLPUniversal
from app.omnichannel.nlp_models import IntentType, EntityType


@pytest.mark.integration
class TestNLPIntegration:
    """Integration tests for NLP service"""
    
    @pytest.fixture
    def nlp(self):
        """Create NLP service"""
        return NLPUniversal()
    
    @pytest.mark.asyncio
    async def test_complete_order_checking_workflow(self, nlp):
        """Test complete workflow: check orders → follow-up question"""
        # Act - First message
        result1 = await nlp.understand("Quantos pedidos tenho no iFood?")
        
        # Assert first message
        assert result1.classification.intent == IntentType.CHECK_ORDERS
        assert result1.classification.connector == "ifood"
        
        # Act - Follow-up question
        context = {
            'last_intent': result1.classification.intent.value,
            'last_connector': result1.classification.connector
        }
        result2 = await nlp.understand("E qual foi o mais caro?", context)
        
        # Assert follow-up
        assert result2.classification.intent == IntentType.GET_TOP_ITEMS
        assert result2.classification.connector == "ifood"
    
    @pytest.mark.asyncio
    async def test_order_confirmation_workflow(self, nlp):
        """Test order confirmation workflow"""
        # Act - Check orders
        result1 = await nlp.understand("Quantos pedidos tenho?")
        assert result1.classification.intent == IntentType.CHECK_ORDERS
        
        # Act - Confirm order
        result2 = await nlp.understand("Confirme o pedido #12345")
        
        # Assert
        assert result2.classification.intent == IntentType.CONFIRM_ORDER
        order_ids = [e for e in result2.classification.entities if e.type == EntityType.ORDER_ID]
        assert len(order_ids) > 0
        assert order_ids[0].value == "12345"
    
    @pytest.mark.asyncio
    async def test_store_closure_workflow(self, nlp):
        """Test store closure workflow with duration extraction"""
        # Act
        result = await nlp.understand("Feche a loja por 30 minutos")
        
        # Assert
        assert result.classification.intent == IntentType.CLOSE_STORE
        durations = [e for e in result.classification.entities if e.type == EntityType.DURATION]
        assert len(durations) > 0
        assert durations[0].value == "30"
    
    @pytest.mark.asyncio
    async def test_revenue_query_workflow(self, nlp):
        """Test revenue query workflow"""
        # Act
        result = await nlp.understand("Qual foi meu faturamento hoje?")
        
        # Assert
        assert result.classification.intent == IntentType.GET_REVENUE
        dates = [e for e in result.classification.entities if e.type == EntityType.DATE]
        assert len(dates) > 0
        assert dates[0].value == "hoje"
    
    @pytest.mark.asyncio
    async def test_multi_connector_support(self, nlp):
        """Test support for multiple connectors"""
        # Act - iFood
        result1 = await nlp.understand("Quantos pedidos tenho no iFood?")
        assert result1.classification.connector == "ifood"
        
        # Act - 99food
        result2 = await nlp.understand("Quantos pedidos tenho no 99food?")
        assert result2.classification.connector == "99food"
        
        # Act - Shoppe
        result3 = await nlp.understand("Quantos pedidos tenho no Shoppe?")
        assert result3.classification.connector == "shoppe"
    
    @pytest.mark.asyncio
    async def test_context_preservation_across_messages(self, nlp):
        """Test context preservation across multiple messages"""
        # Act - First message
        result1 = await nlp.understand("Quantos pedidos tenho?")
        context = {
            'last_intent': result1.classification.intent.value,
            'last_connector': result1.classification.connector
        }
        
        # Act - Second message (no connector mentioned)
        result2 = await nlp.understand("Confirme esse", context)
        
        # Assert - Should use connector from context
        assert result2.classification.connector == context['last_connector']
    
    @pytest.mark.asyncio
    async def test_complex_message_with_multiple_entities(self, nlp):
        """Test parsing complex message with multiple entities"""
        # Act
        result = await nlp.understand(
            "Confirme o pedido #12345 no iFood por favor"
        )
        
        # Assert
        assert result.classification.intent == IntentType.CONFIRM_ORDER
        assert result.classification.connector == "ifood"
        
        order_ids = [e for e in result.classification.entities if e.type == EntityType.ORDER_ID]
        assert len(order_ids) > 0
        assert order_ids[0].value == "12345"
    
    @pytest.mark.asyncio
    async def test_followup_with_implicit_context(self, nlp):
        """Test follow-up questions with implicit context"""
        # Arrange
        context = {
            'last_intent': 'check_orders',
            'last_connector': 'ifood'
        }
        
        # Act - Follow-up: "Confirme esse" (confirm that one)
        result = await nlp.understand("Confirme esse", context)
        
        # Assert
        assert result.classification.intent == IntentType.CONFIRM_ORDER
        assert result.classification.connector == "ifood"
    
    @pytest.mark.asyncio
    async def test_error_recovery_unknown_intent(self, nlp):
        """Test error recovery for unknown intent"""
        # Act
        result = await nlp.understand("xyz abc 123 qwerty")
        
        # Assert
        assert result.classification.intent == IntentType.UNKNOWN
        assert result.classification.confidence == 0.0
        # Should still have default connector
        assert result.classification.connector == "ifood"
    
    @pytest.mark.asyncio
    async def test_nlp_result_serialization(self, nlp):
        """Test NLP result serialization and deserialization"""
        # Act - Understand message
        result1 = await nlp.understand("Quantos pedidos tenho no iFood?")
        
        # Serialize
        data = result1.to_dict()
        
        # Deserialize
        from app.omnichannel.nlp_models import NLPResult
        result2 = NLPResult.from_dict(data)
        
        # Assert
        assert result1.classification.intent == result2.classification.intent
        assert result1.classification.connector == result2.classification.connector
        assert len(result1.classification.entities) == len(result2.classification.entities)


@pytest.mark.integration
class TestNLPContextAwareness:
    """Tests for context-aware NLP understanding"""
    
    @pytest.fixture
    def nlp(self):
        """Create NLP service"""
        return NLPUniversal()
    
    @pytest.mark.asyncio
    async def test_followup_question_which_was_most_expensive(self, nlp):
        """Test follow-up: 'which was the most expensive'"""
        # Arrange
        context = {'last_intent': 'check_orders'}
        
        # Act
        result = await nlp.understand("E qual foi o mais caro?", context)
        
        # Assert
        assert result.classification.intent == IntentType.GET_TOP_ITEMS
    
    @pytest.mark.asyncio
    async def test_followup_question_what_was_total(self, nlp):
        """Test follow-up: 'what was the total'"""
        # Arrange
        context = {'last_intent': 'check_orders'}
        
        # Act
        result = await nlp.understand("Qual foi o total?", context)
        
        # Assert
        assert result.classification.intent == IntentType.GET_REVENUE
    
    @pytest.mark.asyncio
    async def test_followup_confirmation_yes(self, nlp):
        """Test follow-up: confirmation with 'yes'"""
        # Arrange
        context = {'last_intent': 'check_orders'}
        
        # Act
        result = await nlp.understand("Sim, confirme", context)
        
        # Assert
        assert result.classification.intent == IntentType.CONFIRM_ORDER
    
    @pytest.mark.asyncio
    async def test_followup_cancellation_no(self, nlp):
        """Test follow-up: cancellation with 'no'"""
        # Arrange
        context = {'last_intent': 'check_orders'}
        
        # Act
        result = await nlp.understand("Não, cancela", context)
        
        # Assert
        assert result.classification.intent == IntentType.CANCEL_ORDER
