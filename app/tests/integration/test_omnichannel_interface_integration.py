"""
Integration tests for OmnichannelInterface.

Tests the complete omnichannel flow with real service integration.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from app.omnichannel.interface import OmnichannelInterface
from app.omnichannel.models import ChannelType
from app.omnichannel.database.models import User, UserTier
from app.core.brain import Brain
from app.core.auditor import Auditor
from app.core.supervisor import Supervisor
from app.core.event_bus import EventBus


@pytest.mark.integration
class TestOmnichannelInterfaceIntegration:
    """Integration tests for OmnichannelInterface"""
    
    @pytest.fixture
    async def sample_user(self):
        """Create sample user for testing"""
        from app.omnichannel.database.repositories import UserRepository
        
        user_repo = UserRepository()
        
        # Create test user
        user = User(
            email="integration_test@example.com",
            tier=UserTier.FREE,
            telegram_id=987654321,
            created_at=datetime.now()
        )
        
        # Clean up any existing user first
        try:
            await user_repo.delete("integration_test@example.com")
        except:
            pass
        
        # Create new user
        created_user = await user_repo.create(user)
        
        yield created_user
        
        # Cleanup
        try:
            await user_repo.delete("integration_test@example.com")
        except:
            pass
    
    @pytest.fixture
    def omnichannel_interface(self):
        """Create OmnichannelInterface with real services"""
        # Initialize real services
        auditor = Auditor()
        telegram_service = AsyncMock()
        telegram_service.send_message.return_value = {"ok": True, "result": {"message_id": 123}}
        
        supervisor = Supervisor(auditor=auditor, telegram_service=telegram_service)
        
        # Initialize EventBus with proper config
        from app.core.event_bus import EventBusConfig
        event_bus_config = EventBusConfig(region="us-east-1")
        event_bus = EventBus(event_bus_config)
        
        brain = Brain(auditor=auditor, supervisor=supervisor)
        
        return OmnichannelInterface(
            brain=brain,
            auditor=auditor,
            supervisor=supervisor,
            event_bus=event_bus,
            telegram_service=telegram_service
        )
    
    @pytest.mark.asyncio
    async def test_complete_message_processing_flow(self, omnichannel_interface, sample_user):
        """Test complete message processing flow with real services"""
        # Mock external dependencies that require API calls
        with patch.object(omnichannel_interface.brain, 'process') as mock_brain_process:
            mock_brain_process.return_value = "Você tem 3 pedidos no iFood: Pedido #123 (R$ 45,50), Pedido #124 (R$ 32,00), Pedido #125 (R$ 67,80)"
            
            # Register user channel first
            registration_result = await omnichannel_interface.register_user_channel(
                email=sample_user.email,
                channel=ChannelType.TELEGRAM,
                channel_user_id=str(sample_user.telegram_id),
                metadata={"chat_id": str(sample_user.telegram_id)}
            )
            
            assert registration_result is True
            
            # Process message
            result = await omnichannel_interface.process_message(
                channel=ChannelType.TELEGRAM,
                channel_user_id=str(sample_user.telegram_id),
                message_text="Quantos pedidos tenho no iFood?",
                message_id="test_msg_123",
                metadata={"chat_id": str(sample_user.telegram_id)}
            )
            
            # Assertions
            assert result["success"] is True
            assert "pedidos no iFood" in result["response"]
            assert result["channel"] == "telegram"
            assert result["intent"] == "check_orders"
            assert result["connector"] == "ifood"
            assert result["processing_time_seconds"] > 0
            
            # Verify brain was called with correct context
            mock_brain_process.assert_called_once()
            call_args = mock_brain_process.call_args
            assert call_args[0][0] == "Quantos pedidos tenho no iFood?"  # message text
            
            # Verify context has correct structure
            context = call_args[0][1]
            assert context.email == sample_user.email
            assert context.channel == ChannelType.TELEGRAM
            assert context.user_profile["tier"] == "free"
            assert context.user_profile["telegram_id"] == sample_user.telegram_id
    
    @pytest.mark.asyncio
    async def test_usage_limit_enforcement_integration(self, omnichannel_interface, sample_user):
        """Test usage limit enforcement with real billing services"""
        # Mock user to have reached limit
        with patch.object(omnichannel_interface.usage_tracker, 'can_process_message') as mock_can_process:
            mock_can_process.return_value = False
            
            with patch.object(omnichannel_interface.limit_enforcer, 'get_limit_status') as mock_limit_status:
                mock_limit_status.return_value = {
                    "messages_used": 100,
                    "messages_remaining": 0,
                    "limit": 100,
                    "tier": "free"
                }
                
                with patch.object(omnichannel_interface.billing_manager, 'generate_upgrade_link') as mock_upgrade:
                    mock_upgrade.return_value = f"https://agentfirst.com/upgrade?email={sample_user.email}&tier=pro"
                    
                    # Register user channel
                    await omnichannel_interface.register_user_channel(
                        email=sample_user.email,
                        channel=ChannelType.TELEGRAM,
                        channel_user_id=str(sample_user.telegram_id)
                    )
                    
                    # Process message
                    result = await omnichannel_interface.process_message(
                        channel=ChannelType.TELEGRAM,
                        channel_user_id=str(sample_user.telegram_id),
                        message_text="Quantos pedidos tenho?",
                        message_id="test_msg_limit"
                    )
                    
                    # Assertions
                    assert result["success"] is False
                    assert result["reason"] == "usage_limit_exceeded"
                    assert "Limite atingido" in result["response"]
                    assert "100 mensagens gratuitas" in result["response"]
                    assert "Upgrade para Pro" in result["response"]
                    assert "10.000 mensagens/mês" in result["response"]
                    assert sample_user.email in result["response"]
    
    @pytest.mark.asyncio
    async def test_new_order_notification_integration(self, omnichannel_interface, sample_user):
        """Test new order notification with real services"""
        order_data = {
            "order_id": "order_integration_123",
            "total_amount": 89.50,
            "customer": {
                "name": "João da Silva",
                "phone": "+5511999999999"
            },
            "items": [
                {"name": "Hambúrguer Clássico", "quantity": 2, "price": 25.00},
                {"name": "Batata Frita", "quantity": 1, "price": 15.00},
                {"name": "Refrigerante 2L", "quantity": 1, "price": 12.00}
            ],
            "delivery_address": {
                "street": "Rua das Flores, 123",
                "neighborhood": "Centro",
                "city": "São Paulo"
            }
        }
        
        # Register user channel first
        await omnichannel_interface.register_user_channel(
            email=sample_user.email,
            channel=ChannelType.TELEGRAM,
            channel_user_id=str(sample_user.telegram_id),
            metadata={"chat_id": str(sample_user.telegram_id)}
        )
        
        # Handle new order notification
        result = await omnichannel_interface.handle_new_order_notification(
            email=sample_user.email,
            order_data=order_data,
            connector="ifood"
        )
        
        # Assertions
        assert result["success"] is True
        assert result["channels_notified"] == 1
        assert "telegram" in result["results"]
        assert result["results"]["telegram"]["success"] is True
        assert "message_id" in result["results"]["telegram"]
        
        # Verify Telegram service was called with correct parameters
        omnichannel_interface.telegram_service.send_message.assert_called_once()
        call_args = omnichannel_interface.telegram_service.send_message.call_args
        
        assert call_args[1]["chat_id"] == str(sample_user.telegram_id)
        assert "Novo pedido no IFOOD" in call_args[1]["text"]
        assert "order_integration_123" in call_args[1]["text"]
        assert "R$ 89,50" in call_args[1]["text"]
        assert "João da Silva" in call_args[1]["text"]
        assert "3" in call_args[1]["text"]  # items count
    
    @pytest.mark.asyncio
    async def test_context_preservation_across_messages(self, omnichannel_interface, sample_user):
        """Test context preservation across multiple messages"""
        # Mock brain responses for conversation flow
        brain_responses = [
            "Você tem 3 pedidos no iFood: #123 (R$ 45,50), #124 (R$ 32,00), #125 (R$ 67,80)",
            "O pedido mais caro é o #125 com R$ 67,80",
            "✅ Pedido #125 confirmado no iFood!"
        ]
        
        with patch.object(omnichannel_interface.brain, 'process') as mock_brain_process:
            mock_brain_process.side_effect = brain_responses
            
            # Register user channel
            await omnichannel_interface.register_user_channel(
                email=sample_user.email,
                channel=ChannelType.TELEGRAM,
                channel_user_id=str(sample_user.telegram_id)
            )
            
            # Message 1: Check orders
            result1 = await omnichannel_interface.process_message(
                channel=ChannelType.TELEGRAM,
                channel_user_id=str(sample_user.telegram_id),
                message_text="Quantos pedidos tenho?",
                message_id="msg_1"
            )
            
            assert result1["success"] is True
            assert "3 pedidos no iFood" in result1["response"]
            
            # Message 2: Follow-up question (context-dependent)
            result2 = await omnichannel_interface.process_message(
                channel=ChannelType.TELEGRAM,
                channel_user_id=str(sample_user.telegram_id),
                message_text="Qual foi o mais caro?",
                message_id="msg_2"
            )
            
            assert result2["success"] is True
            assert "mais caro é o #125" in result2["response"]
            
            # Message 3: Confirm order (context-dependent)
            result3 = await omnichannel_interface.process_message(
                channel=ChannelType.TELEGRAM,
                channel_user_id=str(sample_user.telegram_id),
                message_text="Confirme esse pedido",
                message_id="msg_3"
            )
            
            assert result3["success"] is True
            assert "confirmado" in result3["response"]
            
            # Verify brain was called 3 times with increasing context
            assert mock_brain_process.call_count == 3
            
            # Check that context was preserved and grew
            contexts = [call[0][1] for call in mock_brain_process.call_args_list]
            
            # First message should have minimal context
            assert len(contexts[0].conversation_history) == 0
            
            # Second message should have previous conversation
            assert len(contexts[1].conversation_history) >= 2  # User + Assistant from first message
            
            # Third message should have full conversation history
            assert len(contexts[2].conversation_history) >= 4  # All previous messages
    
    @pytest.mark.asyncio
    async def test_audit_logging_integration(self, omnichannel_interface, sample_user):
        """Test audit logging integration with real auditor"""
        with patch.object(omnichannel_interface.brain, 'process') as mock_brain_process:
            mock_brain_process.return_value = "Teste de auditoria"
            
            # Register user channel
            await omnichannel_interface.register_user_channel(
                email=sample_user.email,
                channel=ChannelType.TELEGRAM,
                channel_user_id=str(sample_user.telegram_id)
            )
            
            # Process message
            result = await omnichannel_interface.process_message(
                channel=ChannelType.TELEGRAM,
                channel_user_id=str(sample_user.telegram_id),
                message_text="Teste de auditoria",
                message_id="audit_test_msg"
            )
            
            assert result["success"] is True
            
            # Verify audit logs were created
            # Note: In a real integration test, we would query the audit logs
            # from DynamoDB to verify they were actually stored
            
            # For now, we verify the auditor methods were called
            assert omnichannel_interface.auditor.log_transaction.call_count >= 1
            
            # Check audit call for successful message processing
            audit_calls = omnichannel_interface.auditor.log_transaction.call_args_list
            
            # Find the successful processing audit log
            success_audit = None
            for call in audit_calls:
                if call[1]["action"] == "message_processed":
                    success_audit = call
                    break
            
            assert success_audit is not None
            assert success_audit[1]["email"] == sample_user.email
            assert success_audit[1]["input_data"]["channel"] == "telegram"
            assert success_audit[1]["input_data"]["message"] == "Teste de auditoria"
            assert success_audit[1]["output_data"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_event_bus_integration(self, omnichannel_interface, sample_user):
        """Test event bus integration with real event publishing"""
        with patch.object(omnichannel_interface.brain, 'process') as mock_brain_process:
            mock_brain_process.return_value = "Teste de eventos"
            
            # Register user channel
            await omnichannel_interface.register_user_channel(
                email=sample_user.email,
                channel=ChannelType.TELEGRAM,
                channel_user_id=str(sample_user.telegram_id)
            )
            
            # Process message
            result = await omnichannel_interface.process_message(
                channel=ChannelType.TELEGRAM,
                channel_user_id=str(sample_user.telegram_id),
                message_text="Teste de eventos",
                message_id="event_test_msg"
            )
            
            assert result["success"] is True
            
            # Verify event was published
            omnichannel_interface.event_bus.publish.assert_called_once()
            
            # Check event data
            call_args = omnichannel_interface.event_bus.publish.call_args
            assert call_args[1]["topic"] == "omnichannel.message_processed"
            
            event_data = call_args[1]["data"]
            assert event_data["email"] == sample_user.email
            assert event_data["channel"] == "telegram"
            assert event_data["intent"] == "unknown"  # Default for test message
            assert "timestamp" in event_data
            assert "processing_time_seconds" in event_data
    
    @pytest.mark.asyncio
    async def test_error_recovery_integration(self, omnichannel_interface, sample_user):
        """Test error recovery and graceful degradation"""
        # Mock brain to raise exception
        with patch.object(omnichannel_interface.brain, 'process') as mock_brain_process:
            mock_brain_process.side_effect = Exception("Simulated brain error")
            
            # Register user channel
            await omnichannel_interface.register_user_channel(
                email=sample_user.email,
                channel=ChannelType.TELEGRAM,
                channel_user_id=str(sample_user.telegram_id)
            )
            
            # Process message
            result = await omnichannel_interface.process_message(
                channel=ChannelType.TELEGRAM,
                channel_user_id=str(sample_user.telegram_id),
                message_text="Teste de erro",
                message_id="error_test_msg"
            )
            
            # Assertions
            assert result["success"] is False
            assert result["error"] == "Simulated brain error"
            assert "Ops! Algo deu errado" in result["response"]
            assert result["processing_time_seconds"] > 0
            
            # Verify error was audited
            error_audit_found = False
            for call in omnichannel_interface.auditor.log_transaction.call_args_list:
                if call[1]["action"] == "message_processing_error":
                    error_audit_found = True
                    assert call[1]["email"] == sample_user.email
                    assert call[1]["input_data"]["error"] == "Simulated brain error"
                    assert call[1]["output_data"]["success"] is False
                    break
            
            assert error_audit_found, "Error audit log not found"
    
    @pytest.mark.asyncio
    async def test_multi_channel_support_preparation(self, omnichannel_interface, sample_user):
        """Test preparation for multi-channel support (WhatsApp, Web, App)"""
        # This test verifies the interface is ready for multiple channels
        # even though only Telegram is fully implemented
        
        # Test channel registration for different channel types
        channels_to_test = [
            (ChannelType.TELEGRAM, str(sample_user.telegram_id)),
            (ChannelType.WHATSAPP, "whatsapp_123456789"),
            (ChannelType.WEB, "web_session_abc123"),
            (ChannelType.APP, "app_user_xyz789")
        ]
        
        for channel_type, channel_user_id in channels_to_test:
            result = await omnichannel_interface.register_user_channel(
                email=sample_user.email,
                channel=channel_type,
                channel_user_id=channel_user_id,
                metadata={"test": True}
            )
            
            # All channels should be registerable
            assert result is True
        
        # Test status endpoint shows all supported channels
        status = await omnichannel_interface.get_interface_status()
        
        supported_channels = status["channels_supported"]
        assert "telegram" in supported_channels
        assert "whatsapp" in supported_channels
        assert "web" in supported_channels
        assert "app" in supported_channels
        assert "email" in supported_channels
        assert "sms" in supported_channels
        
        # Test features are all enabled
        features = status["features"]
        assert features["natural_language"] is True
        assert features["omnichannel_transparent"] is True
        assert features["context_preserved"] is True
        assert features["email_based_auth"] is True
        assert features["freemium_billing"] is True
        assert features["enterprise_grade"] is True
        assert features["h_i_t_l_supervision"] is True
        assert features["audit_logging"] is True