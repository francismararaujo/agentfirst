"""
Integration tests for iFood Connector

Tests complete workflows and homologation scenarios:
- Complete order lifecycle
- Event polling and acknowledgment
- Performance SLAs
- Error handling and recovery
- Omnichannel integration
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
import asyncio
import time

from app.domains.retail.ifood_connector import iFoodConnector, iFoodEvent
from app.domains.retail.ifood_connector_extended import iFoodConnectorExtended
from app.domains.retail.retail_agent import RetailAgent
from app.core.brain import Intent, Context
from app.omnichannel.models import ChannelType
from app.config.secrets_manager import SecretsManager


@pytest.mark.integration
class TestiFoodIntegration:
    """Integration tests for iFood Connector"""

    @pytest.fixture
    def mock_secrets_manager(self):
        """Create mock secrets manager"""
        mock_sm = AsyncMock(spec=SecretsManager)
        mock_sm.get_secret.return_value = {
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'merchant_id': 'test_merchant_id',
            'webhook_secret': 'test_webhook_secret'
        }
        return mock_sm

    @pytest.fixture
    def ifood_connector(self, mock_secrets_manager):
        """Create iFood connector"""
        return iFoodConnectorExtended(mock_secrets_manager)

    @pytest.fixture
    def retail_agent(self, ifood_connector):
        """Create retail agent with iFood connector"""
        agent = RetailAgent()
        agent.register_connector('ifood', ifood_connector)
        return agent

    @pytest.fixture
    def mock_context(self):
        """Create mock context"""
        return Context(
            email="restaurant@example.com",
            channel=ChannelType.TELEGRAM,
            session_id="test_session",
            user_profile={"tier": "pro"}
        )

    @pytest.mark.asyncio
    async def test_complete_order_lifecycle(self, ifood_connector):
        """Test complete order lifecycle from polling to confirmation"""
        # Mock authentication
        with patch.object(ifood_connector, 'authenticate', return_value=True):
            # Mock polling response
            mock_events = [
                {
                    'events': [
                        {
                            'id': 'event_123',
                            'type': 'ORDER_PLACED',
                            'orderId': 'order_456',
                            'merchantId': 'test_merchant_id',
                            'createdAt': datetime.now().isoformat()
                        }
                    ]
                }
            ]
            
            # Mock order details
            mock_order_data = {
                'orders': [
                    {
                        'id': 'order_456',
                        'status': 'PENDING',
                        'type': 'DELIVERY',
                        'timing': 'IMMEDIATE',
                        'createdAt': datetime.now().isoformat(),
                        'customer': {
                            'id': 'customer_1',
                            'name': 'João Silva',
                            'phone': '+5511999999999'
                        },
                        'items': [
                            {
                                'id': 'item_1',
                                'name': 'Hambúrguer',
                                'quantity': 2,
                                'unitPrice': 25.90,
                                'totalPrice': 51.80
                            }
                        ],
                        'payments': [
                            {
                                'method': 'CREDIT_CARD',
                                'value': 51.80,
                                'brand': 'Visa'
                            }
                        ]
                    }
                ]
            }
            
            with patch.object(ifood_connector, '_make_request') as mock_request:
                # Setup different responses for different endpoints
                def mock_request_side_effect(method, endpoint, **kwargs):
                    if 'events:polling' in endpoint:
                        return mock_events[0]
                    elif 'orders' in endpoint and method == 'GET':
                        return mock_order_data
                    elif 'acknowledgment' in endpoint:
                        return {'success': True}
                    elif 'confirm' in endpoint:
                        return {'success': True}
                    else:
                        return {'success': True}
                
                mock_request.side_effect = mock_request_side_effect
                
                # 1. Poll for new orders
                events = await ifood_connector.poll_orders()
                assert len(events) == 1
                assert events[0].type == 'ORDER_PLACED'
                assert events[0].order_id == 'order_456'
                
                # 2. Acknowledge events (MANDATORY)
                ack_result = await ifood_connector.acknowledge_events(events)
                assert ack_result is True
                
                # 3. Get order details
                orders = await ifood_connector.get_orders(status='PENDING')
                assert len(orders) == 1
                order = orders[0]
                assert order.id == 'order_456'
                assert order.customer == 'João Silva'
                
                # 4. Confirm order
                confirm_result = await ifood_connector.confirm_order('order_456')
                assert confirm_result['success'] is True

    @pytest.mark.asyncio
    async def test_polling_performance_sla(self, ifood_connector):
        """Test polling performance meets SLA (< 5 seconds)"""
        with patch.object(ifood_connector, 'authenticate', return_value=True):
            with patch.object(ifood_connector, '_make_request') as mock_request:
                mock_request.return_value = {'events': []}
                
                # Test multiple polling cycles
                for _ in range(5):
                    start_time = time.time()
                    await ifood_connector.poll_orders()
                    elapsed = time.time() - start_time
                    
                    # Must meet SLA
                    assert elapsed < ifood_connector.POLLING_TIMEOUT

    @pytest.mark.asyncio
    async def test_confirmation_performance_sla(self, ifood_connector):
        """Test confirmation performance meets SLA (< 2 seconds)"""
        with patch.object(ifood_connector, 'authenticate', return_value=True):
            with patch.object(ifood_connector, '_make_request') as mock_request:
                mock_request.return_value = {'success': True}
                
                # Test multiple confirmations
                for i in range(3):
                    start_time = time.time()
                    await ifood_connector.confirm_order(f'order_{i}')
                    elapsed = time.time() - start_time
                    
                    # Must meet SLA
                    assert elapsed < ifood_connector.CONFIRMATION_TIMEOUT

    @pytest.mark.asyncio
    async def test_event_deduplication_mandatory(self, ifood_connector):
        """Test mandatory event deduplication"""
        with patch.object(ifood_connector, 'authenticate', return_value=True):
            # Create duplicate events
            events = [
                iFoodEvent(
                    id='event_1',
                    type='ORDER_PLACED',
                    order_id='order_1',
                    merchant_id='test_merchant_id',
                    timestamp=datetime.now(),
                    data={}
                ),
                iFoodEvent(
                    id='event_1',  # Duplicate
                    type='ORDER_PLACED',
                    order_id='order_1',
                    merchant_id='test_merchant_id',
                    timestamp=datetime.now(),
                    data={}
                ),
                iFoodEvent(
                    id='event_2',
                    type='ORDER_CONFIRMED',
                    order_id='order_2',
                    merchant_id='test_merchant_id',
                    timestamp=datetime.now(),
                    data={}
                )
            ]
            
            with patch.object(ifood_connector, '_make_request') as mock_request:
                mock_request.return_value = {'success': True}
                
                # First acknowledgment
                result1 = await ifood_connector.acknowledge_events(events)
                assert result1 is True
                
                # Second acknowledgment with same events (should deduplicate)
                result2 = await ifood_connector.acknowledge_events(events)
                assert result2 is True
                
                # Should have processed unique events only
                assert len(ifood_connector.processed_events) == 2
                assert 'event_1' in ifood_connector.processed_events
                assert 'event_2' in ifood_connector.processed_events

    @pytest.mark.asyncio
    async def test_authentication_token_refresh(self, ifood_connector):
        """Test automatic token refresh at 80% expiration"""
        # Create token that needs refresh
        ifood_connector.token = type('Token', (), {
            'access_token': 'old_token',
            'refresh_token': 'refresh_token',
            'expires_at': datetime.now() + timedelta(minutes=1),
            'is_expired': False,
            'needs_refresh': True
        })()
        
        with patch.object(ifood_connector, '_refresh_token', return_value=True) as mock_refresh:
            with patch.object(ifood_connector, '_make_request') as mock_request:
                mock_request.return_value = {'events': []}
                
                # This should trigger token refresh
                await ifood_connector.poll_orders()
                
                mock_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limiting_handling(self, ifood_connector):
        """Test rate limiting handling (429 responses)"""
        with patch.object(ifood_connector, 'authenticate', return_value=True):
            # Fill up rate limit
            ifood_connector.request_timestamps = [time.time()] * ifood_connector.MAX_REQUESTS_PER_MINUTE
            
            with patch('asyncio.sleep') as mock_sleep:
                await ifood_connector._check_rate_limit()
                
                # Should have waited due to rate limit
                mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_recovery_and_retry(self, ifood_connector):
        """Test error recovery and retry mechanisms"""
        with patch.object(ifood_connector, 'authenticate', return_value=True):
            events = [
                iFoodEvent(
                    id='event_1',
                    type='ORDER_PLACED',
                    order_id='order_1',
                    merchant_id='test_merchant_id',
                    timestamp=datetime.now(),
                    data={}
                )
            ]
            
            with patch.object(ifood_connector, '_make_request') as mock_request:
                # First call fails, second succeeds
                mock_request.side_effect = [
                    Exception("Network error"),
                    {'success': True}
                ]
                
                with patch('asyncio.sleep'):
                    # Should retry and succeed
                    result = await ifood_connector.acknowledge_events(events)
                    assert result is True
                    assert mock_request.call_count == 2

    @pytest.mark.asyncio
    async def test_retail_agent_integration(self, retail_agent, mock_context):
        """Test integration with Retail Agent"""
        intent = Intent(
            domain="retail",
            action="check_orders",
            connector="ifood",
            confidence=0.9
        )
        
        # Mock iFood connector responses
        ifood_connector = retail_agent.connectors['ifood']
        
        with patch.object(ifood_connector, 'authenticate', return_value=True):
            with patch.object(ifood_connector, 'get_orders') as mock_get_orders:
                mock_get_orders.return_value = [
                    type('Order', (), {
                        'id': 'order_123',
                        'status': 'pending',
                        'total': 89.90,
                        'customer': 'João Silva',
                        'items': [{'name': 'Hambúrguer', 'quantity': 2}],
                        'created_at': datetime.now(),
                        'connector': 'ifood',
                        'metadata': {}
                    })()
                ]
                
                # Execute via Retail Agent
                result = await retail_agent.execute(intent, mock_context)
                
                assert result['success'] is True
                assert result['connector'] == 'ifood'
                assert len(result['orders']) == 1
                assert result['orders'][0].id == 'order_123'

    @pytest.mark.asyncio
    async def test_webhook_signature_validation_integration(self, ifood_connector):
        """Test webhook signature validation in integration scenario"""
        # Setup credentials
        await ifood_connector._load_credentials()
        
        # Simulate webhook payload
        webhook_payload = '{"orderId": "123", "status": "CONFIRMED", "timestamp": "2025-01-26T15:00:00Z"}'
        
        # Calculate correct signature
        import hmac
        import hashlib
        correct_signature = hmac.new(
            ifood_connector.credentials.webhook_secret.encode('utf-8'),
            webhook_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Test validation
        assert ifood_connector.validate_webhook_signature(webhook_payload, correct_signature) is True
        assert ifood_connector.validate_webhook_signature(webhook_payload, 'wrong_signature') is False

    @pytest.mark.asyncio
    async def test_scheduled_order_handling(self, ifood_connector):
        """Test handling of scheduled orders (MANDATORY display)"""
        with patch.object(ifood_connector, 'authenticate', return_value=True):
            scheduled_time = datetime.now() + timedelta(hours=2)
            mock_order_data = {
                'orders': [
                    {
                        'id': 'scheduled_order_123',
                        'status': 'PENDING',
                        'type': 'DELIVERY',
                        'timing': 'SCHEDULED',
                        'scheduledDateTime': scheduled_time.isoformat() + 'Z',
                        'createdAt': datetime.now().isoformat() + 'Z',
                        'customer': {'id': '1', 'name': 'Cliente Agendado'},
                        'items': [
                            {
                                'id': 'item_1',
                                'name': 'Pizza',
                                'quantity': 1,
                                'unitPrice': 45.90,
                                'totalPrice': 45.90
                            }
                        ],
                        'payments': [{'method': 'PIX', 'value': 45.90}]
                    }
                ]
            }
            
            with patch.object(ifood_connector, '_make_request') as mock_request:
                mock_request.return_value = mock_order_data
                
                orders = await ifood_connector.get_orders()
                
                assert len(orders) == 1
                order = orders[0]
                
                # Verify scheduled order parsing
                assert order.metadata['timing'] == 'SCHEDULED'
                assert order.metadata['scheduled_at'] is not None
                
                # Verify scheduled time is properly parsed
                parsed_time = datetime.fromisoformat(order.metadata['scheduled_at'].replace('Z', '+00:00'))
                assert abs((parsed_time - scheduled_time).total_seconds()) < 60  # Within 1 minute

    @pytest.mark.asyncio
    async def test_payment_methods_parsing(self, ifood_connector):
        """Test parsing of all payment methods (9 criteria)"""
        with patch.object(ifood_connector, 'authenticate', return_value=True):
            mock_order_data = {
                'orders': [
                    {
                        'id': 'payment_test_order',
                        'status': 'CONFIRMED',
                        'type': 'DELIVERY',
                        'timing': 'IMMEDIATE',
                        'createdAt': datetime.now().isoformat() + 'Z',
                        'customer': {'id': '1', 'name': 'Cliente Teste'},
                        'items': [
                            {
                                'id': 'item_1',
                                'name': 'Produto',
                                'quantity': 1,
                                'unitPrice': 100.00,
                                'totalPrice': 100.00
                            }
                        ],
                        'payments': [
                            {
                                'method': 'CREDIT_CARD',
                                'value': 50.00,
                                'brand': 'Visa',
                                'authorizationCode': 'AUTH123456',
                                'intermediatorCnpj': '12.345.678/0001-90'
                            },
                            {
                                'method': 'CASH',
                                'value': 30.00,
                                'changeFor': 50.00
                            },
                            {
                                'method': 'PIX',
                                'value': 20.00
                            }
                        ]
                    }
                ]
            }
            
            with patch.object(ifood_connector, '_make_request') as mock_request:
                mock_request.return_value = mock_order_data
                
                orders = await ifood_connector.get_orders()
                
                assert len(orders) == 1
                order = orders[0]
                payments = order.metadata['payments']
                
                # Verify all payment methods parsed correctly
                assert len(payments) == 3
                
                # Credit card payment
                credit_payment = payments[0]
                assert credit_payment['method'] == 'CREDIT_CARD'
                assert credit_payment['brand'] == 'Visa'
                assert credit_payment['authorization_code'] == 'AUTH123456'
                assert credit_payment['intermediator_cnpj'] == '12.345.678/0001-90'
                
                # Cash payment
                cash_payment = payments[1]
                assert cash_payment['method'] == 'CASH'
                assert cash_payment['change_for'] == 50.00
                
                # PIX payment
                pix_payment = payments[2]
                assert pix_payment['method'] == 'PIX'

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, ifood_connector):
        """Test concurrent operations (polling + confirmation)"""
        with patch.object(ifood_connector, 'authenticate', return_value=True):
            with patch.object(ifood_connector, '_make_request') as mock_request:
                mock_request.return_value = {'success': True, 'events': []}
                
                # Run concurrent operations
                tasks = [
                    ifood_connector.poll_orders(),
                    ifood_connector.confirm_order('order_1'),
                    ifood_connector.cancel_order('order_2', 'Test reason'),
                    ifood_connector.get_merchant_status()
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # All operations should complete successfully
                for result in results:
                    assert not isinstance(result, Exception)

    @pytest.mark.asyncio
    async def test_session_cleanup(self, ifood_connector):
        """Test proper session cleanup"""
        # Create session
        await ifood_connector._get_session()
        assert ifood_connector.session is not None
        
        # Close session
        await ifood_connector.close()
        
        # Verify session was closed
        assert ifood_connector.session.close.called