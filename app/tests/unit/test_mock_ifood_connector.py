"""
Unit tests for Mock iFood Connector

Tests the mock iFood connector functionality:
- Authentication
- Order management
- Revenue calculation
- Store management
- Event polling
"""

import pytest
from datetime import datetime

from app.domains.retail.mock_ifood_connector import MockiFoodConnector
from app.domains.retail.base_connector import Order, Revenue, StoreStatus


@pytest.mark.unit
class TestMockiFoodConnector:
    """Unit tests for MockiFoodConnector"""

    @pytest.fixture
    def connector(self):
        """Create MockiFoodConnector instance"""
        return MockiFoodConnector()

    def test_connector_initialization(self, connector):
        """Test connector initialization"""
        assert connector.connector_type == 'ifood'
        assert connector.authenticated is False
        assert connector.store_status == 'open'
        assert len(connector.mock_orders) > 0
        assert connector.mock_events == []

    @pytest.mark.asyncio
    async def test_authenticate(self, connector):
        """Test authentication"""
        result = await connector.authenticate()
        
        assert result is True
        assert connector.authenticated is True

    @pytest.mark.asyncio
    async def test_get_orders_all(self, connector):
        """Test getting all orders"""
        orders = await connector.get_orders()
        
        assert len(orders) > 0
        assert all(isinstance(order, Order) for order in orders)
        assert all(order.connector == 'ifood' for order in orders)

    @pytest.mark.asyncio
    async def test_get_orders_by_status(self, connector):
        """Test getting orders by status"""
        pending_orders = await connector.get_orders(status='pending')
        confirmed_orders = await connector.get_orders(status='confirmed')
        
        assert all(order.status == 'pending' for order in pending_orders)
        assert all(order.status == 'confirmed' for order in confirmed_orders)

    @pytest.mark.asyncio
    async def test_confirm_order_success(self, connector):
        """Test successful order confirmation"""
        # Get a pending order
        orders = await connector.get_orders(status='pending')
        if orders:
            order_id = orders[0].id
            
            result = await connector.confirm_order(order_id)
            
            assert result['success'] is True
            assert result['order_id'] == order_id
            assert result['status'] == 'confirmed'
            assert 'confirmed_at' in result

    @pytest.mark.asyncio
    async def test_confirm_order_not_found(self, connector):
        """Test confirming non-existent order"""
        result = await connector.confirm_order('nonexistent')
        
        assert result['success'] is False
        assert 'não encontrado' in result['error']

    @pytest.mark.asyncio
    async def test_confirm_order_wrong_status(self, connector):
        """Test confirming order with wrong status"""
        # Get a non-pending order
        orders = await connector.get_orders()
        non_pending_order = next((o for o in orders if o.status != 'pending'), None)
        
        if non_pending_order:
            result = await connector.confirm_order(non_pending_order.id)
            
            assert result['success'] is False
            assert 'não pode ser confirmado' in result['error']

    @pytest.mark.asyncio
    async def test_cancel_order_success(self, connector):
        """Test successful order cancellation"""
        orders = await connector.get_orders()
        # Find an order that can be cancelled
        cancellable_order = next((o for o in orders if o.status not in ['delivered', 'cancelled']), None)
        
        if cancellable_order:
            reason = "Ingrediente em falta"
            result = await connector.cancel_order(cancellable_order.id, reason)
            
            assert result['success'] is True
            assert result['order_id'] == cancellable_order.id
            assert result['reason'] == reason
            assert result['status'] == 'cancelled'

    @pytest.mark.asyncio
    async def test_cancel_order_not_found(self, connector):
        """Test cancelling non-existent order"""
        result = await connector.cancel_order('nonexistent', 'Test reason')
        
        assert result['success'] is False
        assert 'não encontrado' in result['error']

    @pytest.mark.asyncio
    async def test_get_revenue_today(self, connector):
        """Test getting revenue for today"""
        revenue = await connector.get_revenue('today')
        
        assert isinstance(revenue, Revenue)
        assert revenue.period == 'today'
        assert revenue.total_revenue > 0
        assert revenue.total_orders > 0
        assert revenue.average_ticket > 0
        assert len(revenue.top_items) > 0
        assert revenue.connector == 'ifood'

    @pytest.mark.asyncio
    async def test_get_revenue_week(self, connector):
        """Test getting revenue for week"""
        revenue = await connector.get_revenue('week')
        
        assert revenue.period == 'week'
        assert revenue.total_revenue > 0
        assert revenue.total_orders > 0

    @pytest.mark.asyncio
    async def test_get_revenue_month(self, connector):
        """Test getting revenue for month"""
        revenue = await connector.get_revenue('month')
        
        assert revenue.period == 'month'
        assert revenue.total_revenue > 0
        assert revenue.total_orders > 0

    @pytest.mark.asyncio
    async def test_manage_store_close(self, connector):
        """Test closing store"""
        status = await connector.manage_store('close', '30 minutes')
        
        assert isinstance(status, StoreStatus)
        assert status.status == 'closed'
        assert status.connector == 'ifood'
        assert status.duration == '30 minutes'
        assert connector.store_status == 'closed'

    @pytest.mark.asyncio
    async def test_manage_store_open(self, connector):
        """Test opening store"""
        status = await connector.manage_store('open')
        
        assert status.status == 'open'
        assert connector.store_status == 'open'

    @pytest.mark.asyncio
    async def test_manage_store_pause(self, connector):
        """Test pausing store"""
        status = await connector.manage_store('pause', '15 minutes')
        
        assert status.status == 'paused'
        assert status.duration == '15 minutes'
        assert connector.store_status == 'paused'

    @pytest.mark.asyncio
    async def test_update_inventory(self, connector):
        """Test updating inventory"""
        result = await connector.update_inventory('Hambúrguer', 50)
        
        assert result['success'] is True
        assert result['item'] == 'Hambúrguer'
        assert result['quantity'] == 50
        assert 'previous_quantity' in result
        assert result['status'] == 'available'

    @pytest.mark.asyncio
    async def test_update_inventory_zero_quantity(self, connector):
        """Test updating inventory with zero quantity"""
        result = await connector.update_inventory('Pizza', 0)
        
        assert result['success'] is True
        assert result['quantity'] == 0
        assert result['status'] == 'unavailable'

    @pytest.mark.asyncio
    async def test_forecast_demand_week(self, connector):
        """Test forecasting demand for week"""
        forecast = await connector.forecast_demand('week')
        
        assert forecast['period'] == 'week'
        assert forecast['predicted_orders'] > 0
        assert forecast['predicted_revenue'] > 0
        assert 'confidence' in forecast
        assert len(forecast['top_items_forecast']) > 0
        assert len(forecast['recommendations']) > 0

    @pytest.mark.asyncio
    async def test_forecast_demand_month(self, connector):
        """Test forecasting demand for month"""
        forecast = await connector.forecast_demand('month')
        
        assert forecast['period'] == 'month'
        assert forecast['predicted_orders'] > 0
        assert forecast['predicted_revenue'] > 0

    @pytest.mark.asyncio
    async def test_get_store_status(self, connector):
        """Test getting store status"""
        status = await connector.get_store_status()
        
        assert isinstance(status, StoreStatus)
        assert status.status == connector.store_status
        assert status.connector == 'ifood'

    @pytest.mark.asyncio
    async def test_poll_events(self, connector):
        """Test polling events"""
        events = await connector.poll_events()
        
        assert isinstance(events, list)
        # Events list might be empty or contain generated events

    @pytest.mark.asyncio
    async def test_acknowledge_event(self, connector):
        """Test acknowledging event"""
        # Add a mock event
        connector.mock_events.append({
            'id': 'test_event_1',
            'type': 'test',
            'timestamp': datetime.now().isoformat()
        })
        
        result = await connector.acknowledge_event('test_event_1')
        
        assert result is True
        # Event should be removed from list
        assert not any(e['id'] == 'test_event_1' for e in connector.mock_events)

    @pytest.mark.asyncio
    async def test_authentication_required(self, connector):
        """Test that operations require authentication"""
        # Reset authentication
        connector.authenticated = False
        
        # Any operation should trigger authentication
        await connector.get_orders()
        
        assert connector.authenticated is True

    def test_mock_orders_generation(self, connector):
        """Test mock orders generation"""
        orders = connector.mock_orders
        
        assert len(orders) > 0
        assert all(isinstance(order, Order) for order in orders)
        assert all(order.connector == 'ifood' for order in orders)
        assert all(order.total > 0 for order in orders)
        assert all(len(order.items) > 0 for order in orders)

    @pytest.mark.asyncio
    async def test_event_generation_on_confirm(self, connector):
        """Test event generation when confirming order"""
        initial_events = len(connector.mock_events)
        
        # Get a pending order and confirm it
        orders = await connector.get_orders(status='pending')
        if orders:
            await connector.confirm_order(orders[0].id)
            
            # Should have generated an event
            assert len(connector.mock_events) == initial_events + 1
            assert connector.mock_events[-1]['type'] == 'order_confirmed'

    @pytest.mark.asyncio
    async def test_event_generation_on_cancel(self, connector):
        """Test event generation when cancelling order"""
        initial_events = len(connector.mock_events)
        
        # Get a cancellable order and cancel it
        orders = await connector.get_orders()
        cancellable_order = next((o for o in orders if o.status not in ['delivered', 'cancelled']), None)
        
        if cancellable_order:
            await connector.cancel_order(cancellable_order.id, 'Test reason')
            
            # Should have generated an event
            assert len(connector.mock_events) == initial_events + 1
            assert connector.mock_events[-1]['type'] == 'order_cancelled'

    @pytest.mark.asyncio
    async def test_event_generation_on_store_management(self, connector):
        """Test event generation when managing store"""
        initial_events = len(connector.mock_events)
        
        await connector.manage_store('close')
        
        # Should have generated an event
        assert len(connector.mock_events) == initial_events + 1
        assert connector.mock_events[-1]['type'] == 'store_status_changed'