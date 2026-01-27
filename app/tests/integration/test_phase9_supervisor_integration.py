"""
Integration tests for Phase 9 - Supervisor (H.I.T.L.)

Tests the complete Human-in-the-Loop workflow:
- Decision evaluation and escalation
- Telegram notification to supervisors
- Human decision processing
- Learning from feedback
- End-to-end escalation workflow
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.core.supervisor import (
    Supervisor, EscalationRequest, EscalationStatus, DecisionComplexity,
    EscalationReason
)
from app.core.brain import Brain, Context, Intent
from app.core.auditor import Auditor
from app.omnichannel.models import ChannelType
from app.omnichannel.telegram_service import TelegramService


@pytest.mark.integration
class TestPhase9SupervisorIntegration:
    """Integration tests for Phase 9 - Supervisor (H.I.T.L.)"""

    @pytest.fixture
    async def mock_dynamodb_table(self):
        """Create mock DynamoDB table for escalations"""
        mock_table = MagicMock()
        mock_table.put_item.return_value = {}
        mock_table.get_item.return_value = {'Item': {}}
        return mock_table

    @pytest.fixture
    async def mock_telegram_service(self):
        """Create mock Telegram service"""
        telegram = AsyncMock()
        telegram.send_message.return_value = {"ok": True, "result": {"message_id": 123}}
        return telegram

    @pytest.fixture
    async def auditor(self):
        """Create Auditor instance"""
        with patch('boto3.resource'):
            return Auditor()

    @pytest.fixture
    async def supervisor(self, mock_dynamodb_table, auditor, mock_telegram_service):
        """Create Supervisor instance with mocked dependencies"""
        with patch('boto3.resource') as mock_resource:
            mock_dynamodb = MagicMock()
            mock_dynamodb.Table.return_value = mock_dynamodb_table
            mock_resource.return_value = mock_dynamodb
            
            supervisor = Supervisor(
                auditor=auditor,
                telegram_service=mock_telegram_service
            )
            supervisor.table = mock_dynamodb_table
            
            # Configure test supervisor
            supervisor.configure_supervisor(
                supervisor_id="test_supervisor",
                name="Test Supervisor",
                telegram_chat_id="123456789",
                specialties=["retail"],
                priority_threshold=1
            )
            
            return supervisor

    @pytest.fixture
    async def brain(self, auditor, supervisor):
        """Create Brain instance with Supervisor"""
        with patch('boto3.client'):
            brain = Brain(auditor=auditor, supervisor=supervisor)
            return brain

    @pytest.fixture
    def sample_context(self):
        """Create sample context for testing"""
        return Context(
            email="test@example.com",
            channel=ChannelType.TELEGRAM,
            session_id="test_session_123",
            user_profile={
                "tier": "pro",
                "telegram_id": 987654321
            },
            memory={
                "last_action": "check_orders",
                "last_connector": "ifood"
            }
        )

    @pytest.mark.asyncio
    async def test_complete_escalation_workflow_approve(
        self, 
        supervisor, 
        mock_dynamodb_table, 
        mock_telegram_service
    ):
        """Test complete escalation workflow - approval path"""
        
        # 1. Evaluate decision that requires supervision
        requires_supervision, escalation_id = await supervisor.evaluate_decision(
            user_email="test@example.com",
            agent="retail_agent",
            action="cancel_order",
            proposed_decision={"cancel": True, "order_id": "12345", "amount": 1500.00},
            context={
                "user_profile": {"tier": "enterprise"},
                "has_error": False,
                "order_details": {"value": 1500.00, "customer": "VIP"}
            },
            confidence=0.6
        )
        
        # Should require supervision due to high value and medium confidence
        assert requires_supervision is True
        assert escalation_id is not None
        assert escalation_id.startswith("esc_")
        
        # Verify escalation was stored
        mock_dynamodb_table.put_item.assert_called()
        stored_item = mock_dynamodb_table.put_item.call_args[1]['Item']
        assert stored_item['escalation_id'] == escalation_id
        assert stored_item['user_email'] == "test@example.com"
        assert stored_item['agent'] == "retail_agent"
        assert stored_item['action'] == "cancel_order"
        
        # Verify supervisor was notified
        mock_telegram_service.send_message.assert_called()
        notification_call = mock_telegram_service.send_message.call_args
        assert notification_call[1]['chat_id'] == "123456789"  # Test supervisor chat ID
        assert "ESCALAÇÃO REQUERIDA" in notification_call[1]['text']
        assert escalation_id in notification_call[1]['text']
        assert "/approve" in notification_call[1]['text']
        assert "/reject" in notification_call[1]['text']
        
        # 2. Mock escalation retrieval for human decision
        mock_escalation_data = {
            'escalation_id': escalation_id,
            'user_email': 'test@example.com',
            'agent': 'retail_agent',
            'action': 'cancel_order',
            'context': {'user_profile': {'tier': 'enterprise'}},
            'proposed_decision': {'cancel': True, 'order_id': '12345', 'amount': 1500.00},
            'confidence': 0.6,
            'complexity': 'high',
            'reason': 'high_value_transaction',
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'timeout_at': (datetime.utcnow() + timedelta(minutes=30)).isoformat(),
            'supervisor_id': 'test_supervisor',
            'supervisor_chat_id': '123456789',
            'priority': 3,
            'tags': []
        }
        
        mock_dynamodb_table.get_item.return_value = {'Item': mock_escalation_data}
        
        # 3. Process human approval
        success = await supervisor.process_human_decision(
            escalation_id=escalation_id,
            decision="approve",
            feedback="Approved - customer is VIP and amount is justified",
            supervisor_id="test_supervisor"
        )
        
        assert success is True
        
        # Verify escalation was updated with approval
        update_calls = [call for call in mock_dynamodb_table.put_item.call_args_list 
                       if call[1]['Item'].get('status') == 'approved']
        assert len(update_calls) > 0

    @pytest.mark.asyncio
    async def test_complete_escalation_workflow_reject(
        self, 
        supervisor, 
        mock_dynamodb_table, 
        mock_telegram_service
    ):
        """Test complete escalation workflow - rejection path"""
        
        # 1. Evaluate decision that requires supervision
        requires_supervision, escalation_id = await supervisor.evaluate_decision(
            user_email="test@example.com",
            agent="retail_agent",
            action="delete_data",
            proposed_decision={"delete": True, "data_type": "user_data"},
            context={
                "user_profile": {"tier": "free"},
                "has_error": True,
                "risk_level": "high"
            },
            confidence=0.3
        )
        
        assert requires_supervision is True
        assert escalation_id is not None
        
        # 2. Mock escalation retrieval
        mock_escalation_data = {
            'escalation_id': escalation_id,
            'user_email': 'test@example.com',
            'agent': 'retail_agent',
            'action': 'delete_data',
            'context': {'user_profile': {'tier': 'free'}, 'has_error': True},
            'proposed_decision': {'delete': True, 'data_type': 'user_data'},
            'confidence': 0.3,
            'complexity': 'critical',
            'reason': 'system_anomaly',
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'timeout_at': (datetime.utcnow() + timedelta(minutes=30)).isoformat(),
            'supervisor_id': 'test_supervisor',
            'supervisor_chat_id': '123456789',
            'priority': 4,
            'tags': []
        }
        
        mock_dynamodb_table.get_item.return_value = {'Item': mock_escalation_data}
        
        # 3. Process human rejection
        success = await supervisor.process_human_decision(
            escalation_id=escalation_id,
            decision="reject",
            feedback="Rejected - too risky, low confidence, and system error present",
            supervisor_id="test_supervisor"
        )
        
        assert success is True

    @pytest.mark.asyncio
    async def test_brain_supervisor_integration(
        self, 
        brain, 
        supervisor, 
        sample_context, 
        mock_dynamodb_table,
        mock_telegram_service
    ):
        """Test Brain integration with Supervisor"""
        
        # Mock retail agent
        mock_retail_agent = AsyncMock()
        mock_retail_agent.execute.return_value = {
            "success": True,
            "action": "cancel_order",
            "order_id": "12345",
            "message": "Order cancelled successfully"
        }
        
        brain.register_agent('retail', mock_retail_agent)
        
        # Mock Claude response for high-risk intent
        with patch.object(brain, '_classify_intent') as mock_classify:
            mock_classify.return_value = Intent(
                domain="retail",
                action="cancel_order",
                connector="ifood",
                confidence=0.4,  # Low confidence to trigger supervision
                entities={"order_id": "12345", "amount": 2000.00}
            )
            
            # Process message that should trigger supervision
            response = await brain.process(
                message="Cancel order 12345 worth $2000",
                context=sample_context
            )
            
            # Should return escalation message, not execute action
            assert "supervisão humana" in response.lower()
            assert "escalação" in response.lower()
            assert "esc_" in response  # Should contain escalation ID
            
            # Verify agent was NOT executed due to supervision
            mock_retail_agent.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_brain_human_decision_processing(
        self, 
        brain, 
        supervisor, 
        mock_dynamodb_table
    ):
        """Test Brain processing human decisions"""
        
        # Mock escalation data
        mock_escalation_data = {
            'escalation_id': 'esc_test123',
            'user_email': 'test@example.com',
            'agent': 'retail_agent',
            'action': 'cancel_order',
            'context': {'order_id': '12345'},
            'proposed_decision': {'cancel': True},
            'confidence': 0.4,
            'complexity': 'high',
            'reason': 'high_value_transaction',
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'timeout_at': (datetime.utcnow() + timedelta(minutes=30)).isoformat(),
            'supervisor_id': 'test_supervisor',
            'priority': 3,
            'tags': []
        }
        
        mock_dynamodb_table.get_item.return_value = {'Item': mock_escalation_data}
        
        # Process approval through Brain
        success = await brain.process_human_decision(
            escalation_id="esc_test123",
            decision="approve",
            feedback="Approved by supervisor",
            supervisor_id="test_supervisor"
        )
        
        assert success is True

    @pytest.mark.asyncio
    async def test_supervisor_learning_from_decisions(
        self, 
        supervisor, 
        mock_dynamodb_table
    ):
        """Test supervisor learning from human decisions"""
        
        # Create multiple escalations for the same pattern
        for i in range(5):
            escalation_id = f"esc_test_{i}"
            
            # Mock escalation data
            mock_escalation_data = {
                'escalation_id': escalation_id,
                'user_email': f'test{i}@example.com',
                'agent': 'retail_agent',
                'action': 'check_orders',
                'context': {'user_profile': {'tier': 'pro'}},
                'proposed_decision': {'orders': 3},
                'confidence': 0.75,
                'complexity': 'medium',
                'reason': 'manual_review',
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat(),
                'timeout_at': (datetime.utcnow() + timedelta(minutes=30)).isoformat(),
                'supervisor_id': 'test_supervisor',
                'priority': 2,
                'tags': []
            }
            
            mock_dynamodb_table.get_item.return_value = {'Item': mock_escalation_data}
            
            # Approve most decisions (4 out of 5)
            decision = "approve" if i < 4 else "reject"
            
            success = await supervisor.process_human_decision(
                escalation_id=escalation_id,
                decision=decision,
                feedback=f"Decision {i}",
                supervisor_id="test_supervisor"
            )
            
            assert success is True
        
        # Check if pattern was learned
        pattern_key = "retail_agent:check_orders"
        assert pattern_key in supervisor._decision_patterns
        
        pattern = supervisor._decision_patterns[pattern_key]
        assert pattern.occurrences == 5
        assert pattern.approval_rate == 0.8  # 4 approved out of 5

    @pytest.mark.asyncio
    async def test_escalation_timeout_handling(
        self, 
        supervisor, 
        mock_dynamodb_table
    ):
        """Test handling of expired escalations"""
        
        # Create expired escalation
        past_time = datetime.utcnow() - timedelta(hours=1)
        mock_escalation_data = {
            'escalation_id': 'esc_expired',
            'user_email': 'test@example.com',
            'agent': 'retail_agent',
            'action': 'cancel_order',
            'context': {},
            'proposed_decision': {'cancel': True},
            'confidence': 0.6,
            'complexity': 'high',
            'reason': 'high_value_transaction',
            'status': 'pending',
            'created_at': past_time.isoformat(),
            'timeout_at': past_time.isoformat(),  # Already expired
            'supervisor_id': 'test_supervisor',
            'priority': 3,
            'tags': []
        }
        
        mock_dynamodb_table.get_item.return_value = {'Item': mock_escalation_data}
        
        # Try to process expired escalation
        success = await supervisor.process_human_decision(
            escalation_id="esc_expired",
            decision="approve",
            supervisor_id="test_supervisor"
        )
        
        # Should fail due to timeout
        assert success is False

    @pytest.mark.asyncio
    async def test_multiple_supervisors_selection(
        self, 
        supervisor, 
        mock_dynamodb_table, 
        mock_telegram_service
    ):
        """Test supervisor selection based on specialties and priority"""
        
        # Configure multiple supervisors
        supervisor.configure_supervisor(
            supervisor_id="finance_supervisor",
            name="Finance Supervisor",
            telegram_chat_id="111111111",
            specialties=["finance"],
            priority_threshold=3
        )
        
        supervisor.configure_supervisor(
            supervisor_id="senior_supervisor",
            name="Senior Supervisor",
            telegram_chat_id="222222222",
            specialties=["general"],
            priority_threshold=1
        )
        
        # Test retail escalation with high priority
        requires_supervision, escalation_id = await supervisor.evaluate_decision(
            user_email="test@example.com",
            agent="retail_agent",
            action="cancel_order",
            proposed_decision={"cancel": True, "amount": 1000.00},
            context={"user_profile": {"tier": "enterprise"}},
            confidence=0.5
        )
        
        assert requires_supervision is True
        
        # Should notify test_supervisor (retail specialty, low threshold)
        mock_telegram_service.send_message.assert_called()
        notification_call = mock_telegram_service.send_message.call_args
        assert notification_call[1]['chat_id'] == "123456789"  # test_supervisor

    @pytest.mark.asyncio
    async def test_escalation_priority_calculation(
        self, 
        supervisor, 
        mock_dynamodb_table
    ):
        """Test escalation priority calculation"""
        
        # Test critical complexity + compliance reason + enterprise user
        requires_supervision, escalation_id = await supervisor.evaluate_decision(
            user_email="test@example.com",
            agent="retail_agent",
            action="delete_user",  # Critical action
            proposed_decision={"delete": True},
            context={
                "user_profile": {"tier": "enterprise"},
                "compliance_required": True
            },
            confidence=0.2  # Very low confidence
        )
        
        assert requires_supervision is True
        
        # Verify high priority was assigned
        stored_item = mock_dynamodb_table.put_item.call_args[1]['Item']
        assert stored_item['priority'] == 4  # Maximum priority

    @pytest.mark.asyncio
    async def test_error_handling_in_escalation(
        self, 
        supervisor, 
        mock_dynamodb_table, 
        mock_telegram_service
    ):
        """Test error handling during escalation process"""
        
        # Mock DynamoDB error
        mock_dynamodb_table.put_item.side_effect = Exception("DynamoDB error")
        
        # Should still return escalation ID even if storage fails
        requires_supervision, escalation_id = await supervisor.evaluate_decision(
            user_email="test@example.com",
            agent="retail_agent",
            action="cancel_order",
            proposed_decision={"cancel": True},
            context={},
            confidence=0.3
        )
        
        # Should escalate due to error (safety first)
        assert requires_supervision is True
        assert escalation_id is not None

    @pytest.mark.asyncio
    async def test_supervisor_configuration_validation(self, supervisor):
        """Test supervisor configuration validation"""
        
        # Configure supervisor with invalid data
        supervisor.configure_supervisor(
            supervisor_id="invalid_supervisor",
            name="",  # Empty name
            telegram_chat_id="invalid_chat_id",
            specialties=[],  # Empty specialties
            priority_threshold=0  # Invalid threshold
        )
        
        # Should still be configured (graceful handling)
        assert "invalid_supervisor" in supervisor.supervisors
        config = supervisor.supervisors["invalid_supervisor"]
        assert config["name"] == ""
        assert config["specialties"] == []
        assert config["priority_threshold"] == 0

    @pytest.mark.asyncio
    async def test_concurrent_escalations(
        self, 
        supervisor, 
        mock_dynamodb_table, 
        mock_telegram_service
    ):
        """Test handling multiple concurrent escalations"""
        
        # Create multiple escalations concurrently
        tasks = []
        for i in range(5):
            task = supervisor.evaluate_decision(
                user_email=f"test{i}@example.com",
                agent="retail_agent",
                action="cancel_order",
                proposed_decision={"cancel": True, "order_id": f"order_{i}"},
                context={"user_profile": {"tier": "pro"}},
                confidence=0.4
            )
            tasks.append(task)
        
        # Execute concurrently
        results = await asyncio.gather(*tasks)
        
        # All should require supervision
        for requires_supervision, escalation_id in results:
            assert requires_supervision is True
            assert escalation_id is not None
            assert escalation_id.startswith("esc_")
        
        # All escalation IDs should be unique
        escalation_ids = [result[1] for result in results]
        assert len(set(escalation_ids)) == 5  # All unique

    @pytest.mark.asyncio
    async def test_escalation_message_formatting(
        self, 
        supervisor, 
        mock_dynamodb_table, 
        mock_telegram_service
    ):
        """Test escalation message formatting for Telegram"""
        
        requires_supervision, escalation_id = await supervisor.evaluate_decision(
            user_email="test@example.com",
            agent="retail_agent",
            action="cancel_order",
            proposed_decision={
                "cancel": True,
                "order_id": "12345",
                "reason": "customer_request",
                "amount": 150.50
            },
            context={
                "user_profile": {"tier": "pro"},
                "order_details": {"restaurant": "Pizza Palace", "items": 3}
            },
            confidence=0.65
        )
        
        assert requires_supervision is True
        
        # Verify message formatting
        mock_telegram_service.send_message.assert_called()
        notification_call = mock_telegram_service.send_message.call_args
        message = notification_call[1]['text']
        
        # Check message contains all required elements
        assert "ESCALAÇÃO REQUERIDA" in message
        assert escalation_id in message
        assert "test@example.com" in message
        assert "retail_agent" in message
        assert "cancel_order" in message
        assert "65%" in message  # Confidence percentage
        assert "/approve" in message
        assert "/reject" in message
        assert "HTML" == notification_call[1]['parse_mode']  # HTML formatting