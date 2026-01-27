"""
Unit tests for Retail Agent

Tests the Retail Agent functionality:
- Tool execution
- State management
- Error handling
- Mock connector integration
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.domains.retail.retail_agent import RetailAgent, RetailState
from app.domains.retail.mock_ifood_connector import MockiFoodConnector
from app.core.brain import Intent, Context
from app.omnichannel.models import ChannelType


@pytest.mark.unit
class TestRetailAgent:
    """Unit tests for RetailAgent"""

    @pytest.fixture
    def retail_agent(self):
        """Create RetailAgent instance"""
        return RetailAgent()

    @pytest.fixture
    def mock_context(self):
        """Create mock context"""
        return Context(
            email="test@example.com",
            channel=ChannelType.TELEGRAM,
            session_id="test_session",
            user_profile={"tier": "free"}
        )

    @pytest.fixture
    def mock_ifood_connector(self):
        """Create mock iFood connector"""
        return MockiFoodConnector()

    def test_retail_agent_initialization(self, retail_agent):
        """Test RetailAgent initialization"""
        assert retail_agent.state is not None
        assert isinstance(retail_agent.state, RetailState)
        assert retail_agent.connectors == {}
        assert len(retail_agent.tools) == 7
        assert 'check_orders' in retail_agent.tools
        assert 'confirm_order' in retail_agent.tools
        assert 'cancel_order' in retail_agent.tools

    def test_register_connector(self, retail_agent, mock_ifood_connector):
        """Test connector registration"""
        retail_agent.register_connector('ifood', mock_ifood_connector)
        
        assert 'ifood' in retail_agent.connectors
        assert retail_agent.connectors['ifood'] == mock_ifood_connector

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self, retail_agent, mock_context):
        """Test executing unknown action"""
        intent = Intent(
            domain="retail",
            action="unknown_action",
            confidence=0.8
        )
        
        result = await retail_agent.execute(intent, mock_context)
        
        assert result['success'] is False
        assert 'não suportada' in result['error']
        assert 'available_actions' in result

    @pytest.mark.asyncio
    async def test_check_orders_without_connector(self, retail_agent, mock_context):
        """Test check_orders without registered connector"""
        intent = Intent(
            domain="retail",
            action="check_orders",
            connector="ifood",
            confidence=0.9
        )
        
        result = await retail_agent.execute(intent, mock_context)
        
        assert result['success'] is True
        assert result['connector'] == 'ifood'
        assert 'orders' in result
        assert len(result['orders']) > 0
        assert result['total_orders'] > 0

    @pytest.mark.asyncio
    async def test_check_orders_with_connector(self, retail_agent, mock_context, mock_ifood_connector):
        """Test check_orders with registered connector"""
        retail_agent.register_connector('ifood', mock_ifood_connector)
        
        intent = Intent(
            domain="retail",
            action="check_orders",
            connector="ifood",
            confidence=0.9
        )
        
        result = await retail_agent.execute(intent, mock_context)
        
        assert result['success'] is True
        assert result['connector'] == 'ifood'
        assert 'orders' in result

    @pytest.mark.asyncio
    async def test_confirm_order_without_order_id(self, retail_agent, mock_context):
        """Test confirm_order without order_id"""
        intent = Intent(
            domain="retail",
            action="confirm_order",
            connector="ifood",
            confidence=0.9,
            entities={}
        )
        
        result = await retail_agent.execute(intent, mock_context)
        
        assert result['success'] is True  # Should use first pending order
        assert 'order_id' in result

    @pytest.mark.asyncio
    async def test_confirm_order_with_order_id(self, retail_agent, mock_context):
        """Test confirm_order with specific order_id"""
        intent = Intent(
            domain="retail",
            action="confirm_order",
            connector="ifood",
            confidence=0.9,
            entities={"order_id": "12345"}
        )
        
        result = await retail_agent.execute(intent, mock_context)
        
        assert result['success'] is True
        assert result['order_id'] == "12345"
        assert result['connector'] == 'ifood'

    @pytest.mark.asyncio
    async def test_cancel_order(self, retail_agent, mock_context):
        """Test cancel_order"""
        intent = Intent(
            domain="retail",
            action="cancel_order",
            connector="ifood",
            confidence=0.9,
            entities={"order_id": "12345", "reason": "Ingrediente em falta"}
        )
        
        result = await retail_agent.execute(intent, mock_context)
        
        assert result['success'] is True
        assert result['order_id'] == "12345"
        assert result['reason'] == "Ingrediente em falta"

    @pytest.mark.asyncio
    async def test_cancel_order_without_order_id(self, retail_agent, mock_context):
        """Test cancel_order without order_id"""
        intent = Intent(
            domain="retail",
            action="cancel_order",
            connector="ifood",
            confidence=0.9,
            entities={}
        )
        
        result = await retail_agent.execute(intent, mock_context)
        
        assert result['success'] is False
        assert 'ID do pedido não especificado' in result['error']

    @pytest.mark.asyncio
    async def test_check_revenue(self, retail_agent, mock_context):
        """Test check_revenue"""
        intent = Intent(
            domain="retail",
            action="check_revenue",
            connector="ifood",
            confidence=0.9,
            entities={"time_period": "today"}
        )
        
        result = await retail_agent.execute(intent, mock_context)
        
        assert result['success'] is True
        assert result['connector'] == 'ifood'
        assert 'revenue' in result
        assert result['revenue']['period'] == 'today'
        assert result['revenue']['total_revenue'] > 0

    @pytest.mark.asyncio
    async def test_manage_store_close(self, retail_agent, mock_context):
        """Test manage_store close action"""
        intent = Intent(
            domain="retail",
            action="manage_store",
            connector="ifood",
            confidence=0.9,
            entities={"action": "close", "duration": "30 minutes"}
        )
        
        result = await retail_agent.execute(intent, mock_context)
        
        assert result['success'] is True
        assert result['action'] == 'close'
        assert result['status'] == 'closed'
        assert result['duration'] == '30 minutes'

    @pytest.mark.asyncio
    async def test_manage_store_open(self, retail_agent, mock_context):
        """Test manage_store open action"""
        intent = Intent(
            domain="retail",
            action="manage_store",
            connector="ifood",
            confidence=0.9,
            entities={"action": "open"}
        )
        
        result = await retail_agent.execute(intent, mock_context)
        
        assert result['success'] is True
        assert result['action'] == 'open'
        assert result['status'] == 'open'

    @pytest.mark.asyncio
    async def test_update_inventory(self, retail_agent, mock_context):
        """Test update_inventory"""
        intent = Intent(
            domain="retail",
            action="update_inventory",
            connector="ifood",
            confidence=0.9,
            entities={"item": "Hambúrguer", "quantity": 50}
        )
        
        result = await retail_agent.execute(intent, mock_context)
        
        assert result['success'] is True
        assert result['item'] == 'Hambúrguer'
        assert result['quantity'] == 50

    @pytest.mark.asyncio
    async def test_forecast_demand(self, retail_agent, mock_context):
        """Test forecast_demand"""
        intent = Intent(
            domain="retail",
            action="forecast_demand",
            connector="ifood",
            confidence=0.9,
            entities={"period": "week"}
        )
        
        result = await retail_agent.execute(intent, mock_context)
        
        assert result['success'] is True
        assert 'forecast' in result
        assert result['forecast']['period'] == 'week'
        assert result['forecast']['predicted_orders'] > 0

    @pytest.mark.asyncio
    async def test_execute_with_event_bus(self, mock_context):
        """Test execute with event bus"""
        mock_event_bus = AsyncMock()
        retail_agent = RetailAgent(event_bus=mock_event_bus)
        
        intent = Intent(
            domain="retail",
            action="check_orders",
            connector="ifood",
            confidence=0.9
        )
        
        result = await retail_agent.execute(intent, mock_context)
        
        assert result['success'] is True
        mock_event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_auditor(self, mock_context):
        """Test execute with auditor"""
        mock_auditor = AsyncMock()
        retail_agent = RetailAgent(auditor=mock_auditor)
        
        intent = Intent(
            domain="retail",
            action="check_orders",
            connector="ifood",
            confidence=0.9
        )
        
        result = await retail_agent.execute(intent, mock_context)
        
        assert result['success'] is True
        mock_auditor.log_transaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_error_handling(self, retail_agent, mock_context):
        """Test error handling in execute"""
        # Mock a tool that raises an exception
        async def failing_tool(intent, context):
            raise Exception("Test error")
        
        retail_agent.tools['failing_action'] = failing_tool
        
        intent = Intent(
            domain="retail",
            action="failing_action",
            confidence=0.9
        )
        
        result = await retail_agent.execute(intent, mock_context)
        
        assert result['success'] is False
        assert 'Test error' in result['error']
        assert result['action'] == 'failing_action'

    @pytest.mark.asyncio
    async def test_handle_event_order_received(self, retail_agent):
        """Test handling order_received event"""
        event_data = {
            'order_id': '12345',
            'connector': 'ifood',
            'customer': 'Test Customer'
        }
        
        # Should not raise exception
        await retail_agent.handle_event('order_received', event_data)

    @pytest.mark.asyncio
    async def test_handle_event_order_confirmed(self, retail_agent):
        """Test handling order_confirmed event"""
        event_data = {
            'order_id': '12345',
            'connector': 'ifood'
        }
        
        # Should not raise exception
        await retail_agent.handle_event('order_confirmed', event_data)

    @pytest.mark.asyncio
    async def test_handle_event_order_cancelled(self, retail_agent):
        """Test handling order_cancelled event"""
        event_data = {
            'order_id': '12345',
            'connector': 'ifood',
            'reason': 'Customer request'
        }
        
        # Should not raise exception
        await retail_agent.handle_event('order_cancelled', event_data)

    @pytest.mark.asyncio
    async def test_handle_unknown_event(self, retail_agent):
        """Test handling unknown event type"""
        event_data = {'test': 'data'}
        
        # Should not raise exception
        await retail_agent.handle_event('unknown_event', event_data)


@pytest.mark.unit
class TestRetailState:
    """Unit tests for RetailState"""

    def test_retail_state_initialization(self):
        """Test RetailState initialization"""
        state = RetailState()
        
        assert state.last_connector is None
        assert state.last_orders == []
        assert state.last_revenue is None
        assert state.store_status == "open"

    def test_retail_state_with_data(self):
        """Test RetailState with initial data"""
        orders = [{'id': '123', 'status': 'pending'}]
        revenue = {'total': 100.0}
        
        state = RetailState(
            last_connector='ifood',
            last_orders=orders,
            last_revenue=revenue,
            store_status='closed'
        )
        
        assert state.last_connector == 'ifood'
        assert state.last_orders == orders
        assert state.last_revenue == revenue
        assert state.store_status == 'closed'