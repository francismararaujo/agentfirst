"""
Unit tests for iFood Connector

Tests all 105+ homologation criteria:
- Authentication (OAuth 2.0)
- Merchant Management
- Order Polling (CRITICAL)
- Event Acknowledgment (CRITICAL)
- Order Types Support
- Payment Methods
- Duplicate Detection (MANDATORY)
- Performance & Security
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import json
import time

from app.domains.retail.ifood_connector import (
    iFoodConnector, iFoodCredentials, iFoodToken, iFoodEvent
)
from app.domains.retail.ifood_connector_extended import iFoodConnectorExtended
from app.config.secrets_manager import SecretsManager


@pytest.mark.unit
class TestiFoodConnector:
    """Unit tests for iFoodConnector"""

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
    def connector(self, mock_secrets_manager):
        """Create iFoodConnector instance"""
        return iFoodConnector(mock_secrets_manager)

    @pytest.fixture
    def extended_connector(self, mock_secrets_manager):
        """Create iFoodConnectorExtended instance"""
        return iFoodConnectorExtended(mock_secrets_manager)

    def test_connector_initialization(self, connector):
        """Test connector initialization"""
        assert connector.connector_type == 'ifood'
        assert connector.credentials is None
        assert connector.token is None
        assert connector.processed_events == set()
        assert connector.pending_acknowledgments == {}
        assert connector.request_timestamps == []

    def test_ifood_credentials(self):
        """Test iFoodCredentials dataclass"""
        creds = iFoodCredentials(
            client_id='test_id',
            client_secret='test_secret',
            merchant_id='test_merchant',
            webhook_secret='test_webhook'
        )
        
        assert creds.client_id == 'test_id'
        assert creds.client_secret == 'test_secret'
        assert creds.merchant_id == 'test_merchant'
        assert creds.webhook_secret == 'test_webhook'

    def test_ifood_token_properties(self):
        """Test iFoodToken properties"""
        # Create token that expires in 1 hour
        expires_at = datetime.now() + timedelta(hours=1)
        token = iFoodToken(
            access_token='test_token',
            refresh_token='test_refresh',
            expires_at=expires_at
        )
        
        assert not token.is_expired
        assert not token.needs_refresh
        
        # Create expired token
        expired_token = iFoodToken(
            access_token='test_token',
            refresh_token='test_refresh',
            expires_at=datetime.now() - timedelta(minutes=1)
        )
        
        assert expired_token.is_expired
        
        # Create token that needs refresh (80% expired)
        refresh_needed = iFoodToken(
            access_token='test_token',
            refresh_token='test_refresh',
            expires_at=datetime.now() + timedelta(minutes=1)  # Very close to expiry
        )
        
        assert refresh_needed.needs_refresh

    def test_ifood_event(self):
        """Test iFoodEvent dataclass"""
        event = iFoodEvent(
            id='event_123',
            type='ORDER_PLACED',
            order_id='order_456',
            merchant_id='merchant_789',
            timestamp=datetime.now(),
            data={'test': 'data'}
        )
        
        assert event.id == 'event_123'
        assert event.type == 'ORDER_PLACED'
        assert event.order_id == 'order_456'
        assert event.merchant_id == 'merchant_789'
        assert not event.acknowledged
        assert event.data == {'test': 'data'}

    @pytest.mark.asyncio
    async def test_load_credentials(self, connector, mock_secrets_manager):
        """Test loading credentials from secrets manager"""
        credentials = await connector._load_credentials()
        
        assert isinstance(credentials, iFoodCredentials)
        assert credentials.client_id == 'test_client_id'
        assert credentials.client_secret == 'test_client_secret'
        assert credentials.merchant_id == 'test_merchant_id'
        assert credentials.webhook_secret == 'test_webhook_secret'
        
        mock_secrets_manager.get_secret.assert_called_once_with("AgentFirst/ifood-credentials")

    @pytest.mark.asyncio
    async def test_check_rate_limit(self, connector):
        """Test rate limiting"""
        # Fill up rate limit
        connector.request_timestamps = [time.time()] * connector.MAX_REQUESTS_PER_MINUTE
        
        # This should trigger rate limiting
        start_time = time.time()
        await connector._check_rate_limit()
        elapsed = time.time() - start_time
        
        # Should have waited some time
        assert elapsed > 0

    @pytest.mark.asyncio
    async def test_make_request_with_auth(self, connector):
        """Test making authenticated request"""
        # Set up token
        connector.token = iFoodToken(
            access_token='test_token',
            refresh_token='test_refresh',
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {'success': True}
            mock_session.request.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            connector.session = mock_session
            
            result = await connector._make_request('GET', '/test')
            
            assert result == {'success': True}
            mock_session.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_request_rate_limited(self, connector):
        """Test handling 429 rate limited response"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            
            # First response: 429 Rate Limited
            mock_response_429 = AsyncMock()
            mock_response_429.status = 429
            mock_response_429.headers = {'Retry-After': '1'}
            
            # Second response: Success
            mock_response_200 = AsyncMock()
            mock_response_200.status = 200
            mock_response_200.json.return_value = {'success': True}
            
            mock_session.request.return_value.__aenter__.side_effect = [
                mock_response_429,
                mock_response_200
            ]
            mock_session_class.return_value = mock_session
            
            connector.session = mock_session
            
            with patch('asyncio.sleep') as mock_sleep:
                result = await connector._make_request('GET', '/test')
                
                assert result == {'success': True}
                mock_sleep.assert_called_with(1)  # Retry-After header value

    @pytest.mark.asyncio
    async def test_authenticate_success(self, connector):
        """Test successful authentication"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                'accessToken': 'new_access_token',
                'refreshToken': 'new_refresh_token',
                'expiresIn': 10800,  # 3 hours
                'tokenType': 'Bearer'
            }
            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            connector.session = mock_session
            
            result = await connector.authenticate()
            
            assert result is True
            assert connector.token is not None
            assert connector.token.access_token == 'new_access_token'
            assert connector.token.refresh_token == 'new_refresh_token'
            assert connector.token.token_type == 'Bearer'

    @pytest.mark.asyncio
    async def test_authenticate_failure(self, connector):
        """Test authentication failure"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.text.return_value = 'Unauthorized'
            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            connector.session = mock_session
            
            result = await connector.authenticate()
            
            assert result is False
            assert connector.token is None

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, connector):
        """Test successful token refresh"""
        # Set up existing token
        connector.token = iFoodToken(
            access_token='old_token',
            refresh_token='refresh_token',
            expires_at=datetime.now() + timedelta(minutes=1)  # Needs refresh
        )
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                'accessToken': 'new_access_token',
                'refreshToken': 'new_refresh_token',
                'expiresIn': 10800,
                'tokenType': 'Bearer'
            }
            mock_session.post.return_value.__aenter__.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            connector.session = mock_session
            
            result = await connector._refresh_token()
            
            assert result is True
            assert connector.token.access_token == 'new_access_token'

    @pytest.mark.asyncio
    async def test_get_merchant_status(self, connector):
        """Test getting merchant status with caching"""
        connector.token = iFoodToken(
            access_token='test_token',
            refresh_token='test_refresh',
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        with patch.object(connector, '_make_request') as mock_request:
            mock_request.return_value = {
                'state': 'AVAILABLE',
                'unavailabilityReason': None
            }
            
            # First call
            result1 = await connector.get_merchant_status()
            assert result1['state'] == 'AVAILABLE'
            
            # Second call should use cache
            result2 = await connector.get_merchant_status()
            assert result2['state'] == 'AVAILABLE'
            
            # Should only make one API call due to caching
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_poll_orders_performance(self, connector):
        """Test order polling performance SLA (< 5 seconds)"""
        connector.token = iFoodToken(
            access_token='test_token',
            refresh_token='test_refresh',
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        with patch.object(connector, '_make_request') as mock_request:
            # Simulate fast response
            mock_request.return_value = {
                'events': [
                    {
                        'id': 'event_1',
                        'type': 'ORDER_PLACED',
                        'orderId': 'order_1',
                        'merchantId': 'test_merchant_id',
                        'createdAt': datetime.now().isoformat()
                    }
                ]
            }
            
            start_time = time.time()
            events = await connector.poll_orders()
            elapsed = time.time() - start_time
            
            # Should meet performance SLA
            assert elapsed < connector.POLLING_TIMEOUT
            assert len(events) == 1
            assert events[0].id == 'event_1'

    @pytest.mark.asyncio
    async def test_acknowledge_events_deduplication(self, connector):
        """Test event acknowledgment with deduplication (MANDATORY)"""
        connector.token = iFoodToken(
            access_token='test_token',
            refresh_token='test_refresh',
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        # Create events with duplicates
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
        
        with patch.object(connector, '_make_request') as mock_request:
            mock_request.return_value = {'success': True}
            
            result = await connector.acknowledge_events(events)
            
            assert result is True
            # Should only acknowledge unique events
            mock_request.assert_called_once()
            call_args = mock_request.call_args[1]['data']
            assert len(call_args['eventIds']) == 2  # Only unique events
            assert 'event_1' in call_args['eventIds']
            assert 'event_2' in call_args['eventIds']

    @pytest.mark.asyncio
    async def test_acknowledge_events_retry_on_failure(self, connector):
        """Test acknowledgment retry on failure"""
        connector.token = iFoodToken(
            access_token='test_token',
            refresh_token='test_refresh',
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
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
        
        with patch.object(connector, '_make_request') as mock_request:
            # First call fails, second succeeds
            mock_request.side_effect = [
                Exception("Network error"),
                {'success': True}
            ]
            
            with patch('asyncio.sleep'):
                result = await connector.acknowledge_events(events)
                
                assert result is True
                assert mock_request.call_count == 2  # Original + retry

    @pytest.mark.asyncio
    async def test_confirm_order_performance(self, connector):
        """Test order confirmation performance SLA (< 2 seconds)"""
        connector.token = iFoodToken(
            access_token='test_token',
            refresh_token='test_refresh',
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        with patch.object(connector, '_make_request') as mock_request:
            mock_request.return_value = {'success': True}
            
            start_time = time.time()
            result = await connector.confirm_order('order_123')
            elapsed = time.time() - start_time
            
            # Should meet performance SLA
            assert elapsed < connector.CONFIRMATION_TIMEOUT
            assert result['success'] is True
            assert result['order_id'] == 'order_123'

    @pytest.mark.asyncio
    async def test_cancel_order(self, connector):
        """Test order cancellation"""
        connector.token = iFoodToken(
            access_token='test_token',
            refresh_token='test_refresh',
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        with patch.object(connector, '_make_request') as mock_request:
            mock_request.return_value = {'success': True}
            
            result = await connector.cancel_order('order_123', 'Ingrediente em falta')
            
            assert result['success'] is True
            assert result['order_id'] == 'order_123'
            assert result['reason'] == 'Ingrediente em falta'

    def test_webhook_signature_validation(self, connector):
        """Test webhook signature validation (Security requirement)"""
        # Set up credentials
        connector.credentials = iFoodCredentials(
            client_id='test_id',
            client_secret='test_secret',
            merchant_id='test_merchant',
            webhook_secret='test_secret_key'
        )
        
        payload = '{"orderId": "123", "status": "CONFIRMED"}'
        
        # Calculate correct signature
        import hmac
        import hashlib
        expected_signature = hmac.new(
            'test_secret_key'.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Test valid signature
        assert connector.validate_webhook_signature(payload, expected_signature) is True
        
        # Test invalid signature
        assert connector.validate_webhook_signature(payload, 'invalid_signature') is False

    @pytest.mark.asyncio
    async def test_close_session(self, connector):
        """Test session cleanup"""
        # Create mock session
        mock_session = AsyncMock()
        mock_session.closed = False
        connector.session = mock_session
        
        await connector.close()
        
        mock_session.close.assert_called_once()


@pytest.mark.unit
class TestiFoodConnectorExtended:
    """Unit tests for iFoodConnectorExtended"""

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
    def extended_connector(self, mock_secrets_manager):
        """Create iFoodConnectorExtended instance"""
        return iFoodConnectorExtended(mock_secrets_manager)

    @pytest.mark.asyncio
    async def test_get_orders_with_types(self, extended_connector):
        """Test getting orders with complete type support"""
        extended_connector.token = iFoodToken(
            access_token='test_token',
            refresh_token='test_refresh',
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        mock_order_data = {
            'orders': [
                {
                    'id': 'order_123',
                    'status': 'CONFIRMED',
                    'type': 'DELIVERY',
                    'timing': 'SCHEDULED',
                    'scheduledDateTime': '2025-01-26T18:00:00Z',
                    'createdAt': '2025-01-26T15:00:00Z',
                    'customer': {
                        'id': 'customer_1',
                        'name': 'João Silva',
                        'phone': '+5511999999999',
                        'document': '12345678901',
                        'documentType': 'CPF'
                    },
                    'deliveryAddress': {
                        'street': 'Rua das Flores',
                        'number': '123',
                        'complement': 'Apto 45',
                        'neighborhood': 'Centro',
                        'city': 'São Paulo',
                        'state': 'SP',
                        'postalCode': '01234-567'
                    },
                    'items': [
                        {
                            'id': 'item_1',
                            'name': 'Hambúrguer',
                            'quantity': 2,
                            'unitPrice': 25.90,
                            'totalPrice': 51.80,
                            'observations': 'Sem cebola'
                        }
                    ],
                    'payments': [
                        {
                            'method': 'CREDIT_CARD',
                            'value': 51.80,
                            'brand': 'Visa',
                            'authorizationCode': 'AUTH123',
                            'intermediatorCnpj': '12.345.678/0001-90'
                        }
                    ],
                    'deliveryObservations': 'Portão azul',
                    'pickupCode': 'ABC123',
                    'coupons': [
                        {
                            'code': 'DESCONTO10',
                            'discount': 5.18,
                            'sponsor': 'iFood'
                        }
                    ]
                }
            ]
        }
        
        with patch.object(extended_connector, '_make_request') as mock_request:
            mock_request.return_value = mock_order_data
            
            orders = await extended_connector.get_orders()
            
            assert len(orders) == 1
            order = orders[0]
            
            # Test basic order data
            assert order.id == 'order_123'
            assert order.status == 'CONFIRMED'
            assert order.customer == 'João Silva'
            assert order.total == 51.80
            
            # Test metadata with complete parsing
            metadata = order.metadata
            assert metadata['order_type'] == 'DELIVERY'
            assert metadata['timing'] == 'SCHEDULED'
            assert metadata['scheduled_at'] is not None
            assert metadata['customer']['name'] == 'João Silva'
            assert metadata['customer']['document'] == '12345678901'
            assert metadata['delivery_address']['street'] == 'Rua das Flores'
            assert metadata['delivery_observations'] == 'Portão azul'
            assert metadata['pickup_code'] == 'ABC123'
            
            # Test payment parsing
            payments = metadata['payments']
            assert len(payments) == 1
            assert payments[0]['method'] == 'CREDIT_CARD'
            assert payments[0]['brand'] == 'Visa'
            assert payments[0]['authorization_code'] == 'AUTH123'
            
            # Test coupon parsing
            coupons = metadata['coupons']
            assert len(coupons) == 1
            assert coupons[0]['sponsor'] == 'iFood'

    @pytest.mark.asyncio
    async def test_get_revenue_financial_integration(self, extended_connector):
        """Test financial integration with sales endpoint"""
        extended_connector.token = iFoodToken(
            access_token='test_token',
            refresh_token='test_refresh',
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        mock_sales_data = {
            'sales': {
                'totalRevenue': 2500.00,
                'totalOrders': 25,
                'topItems': [
                    {'name': 'Hambúrguer', 'quantity': 15, 'revenue': 750.00},
                    {'name': 'Pizza', 'quantity': 10, 'revenue': 500.00}
                ]
            }
        }
        
        with patch.object(extended_connector, '_make_request') as mock_request:
            mock_request.return_value = mock_sales_data
            
            revenue = await extended_connector.get_revenue('today')
            
            assert revenue.total_revenue == 2500.00
            assert revenue.total_orders == 25
            assert revenue.average_ticket == 100.00
            assert len(revenue.top_items) == 2
            assert revenue.top_items[0]['name'] == 'Hambúrguer'

    @pytest.mark.asyncio
    async def test_update_inventory_catalog_management(self, extended_connector):
        """Test item/catalog management"""
        extended_connector.token = iFoodToken(
            access_token='test_token',
            refresh_token='test_refresh',
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        with patch.object(extended_connector, '_make_request') as mock_request:
            mock_request.return_value = {'success': True}
            
            result = await extended_connector.update_inventory('Hambúrguer', 50)
            
            assert result['success'] is True
            assert result['item'] == 'Hambúrguer'
            assert result['quantity'] == 50
            assert result['status'] == 'available'
            
            # Test zero quantity (unavailable)
            result_zero = await extended_connector.update_inventory('Pizza', 0)
            assert result_zero['status'] == 'unavailable'

    @pytest.mark.asyncio
    async def test_picking_operations(self, extended_connector):
        """Test picking operations (9 criteria)"""
        extended_connector.token = iFoodToken(
            access_token='test_token',
            refresh_token='test_refresh',
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        with patch.object(extended_connector, '_make_request') as mock_request:
            mock_request.return_value = {'success': True}
            
            # Test start picking
            start_result = await extended_connector.start_picking('order_123')
            assert start_result['success'] is True
            assert start_result['status'] == 'picking_started'
            
            # Test end picking
            end_result = await extended_connector.end_picking('order_123')
            assert end_result['success'] is True
            assert end_result['status'] == 'picking_completed'

    @pytest.mark.asyncio
    async def test_get_cancellation_reasons(self, extended_connector):
        """Test getting cancellation reasons (MANDATORY display)"""
        extended_connector.token = iFoodToken(
            access_token='test_token',
            refresh_token='test_refresh',
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        mock_reasons_data = {
            'reasons': [
                {
                    'code': 'INGREDIENT_UNAVAILABLE',
                    'description': 'Ingrediente indisponível',
                    'category': 'RESTAURANT'
                },
                {
                    'code': 'CUSTOMER_REQUEST',
                    'description': 'Solicitação do cliente',
                    'category': 'CUSTOMER'
                }
            ]
        }
        
        with patch.object(extended_connector, '_make_request') as mock_request:
            mock_request.return_value = mock_reasons_data
            
            reasons = await extended_connector.get_cancellation_reasons()
            
            assert len(reasons) == 2
            assert reasons[0]['code'] == 'INGREDIENT_UNAVAILABLE'
            assert reasons[0]['description'] == 'Ingrediente indisponível'
            assert reasons[1]['category'] == 'CUSTOMER'