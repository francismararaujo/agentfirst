"""
Integration tests for Phase 8: Auditor & Compliance

Tests complete audit integration with Brain and RetailAgent:
- End-to-end audit logging
- Brain + Auditor integration
- RetailAgent + Auditor integration
- Compliance workflows
- LGPD compliance features
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json

from app.core.brain import Brain, Intent, Context
from app.core.auditor import Auditor, AuditLevel, AuditCategory
from app.domains.retail.retail_agent import RetailAgent
from app.omnichannel.models import ChannelType


@pytest.mark.integration
class TestPhase8AuditorIntegration:
    """Integration tests for Phase 8: Auditor & Compliance"""

    @pytest.fixture
    def mock_dynamodb_table(self):
        """Create mock DynamoDB table"""
        mock_table = AsyncMock()
        mock_table.put_item.return_value = {}
        mock_table.query.return_value = {'Items': []}
        return mock_table

    @pytest.fixture
    def auditor(self, mock_dynamodb_table):
        """Create Auditor instance"""
        with patch('boto3.resource') as mock_resource:
            mock_dynamodb = AsyncMock()
            mock_dynamodb.Table.return_value = mock_dynamodb_table
            mock_resource.return_value = mock_dynamodb
            
            auditor = Auditor()
            auditor.table = mock_dynamodb_table
            return auditor

    @pytest.fixture
    def mock_bedrock_client(self):
        """Create mock Bedrock client"""
        mock_client = MagicMock()
        mock_client.invoke_model.return_value = {
            'body': MagicMock(read=lambda: json.dumps({
                'content': [{
                    'text': '{"domain": "retail", "action": "check_orders", "confidence": 0.9}'
                }]
            }).encode())
        }
        return mock_client

    @pytest.fixture
    def brain_with_auditor(self, auditor, mock_bedrock_client):
        """Create Brain with Auditor integration"""
        return Brain(
            bedrock_client=mock_bedrock_client,
            memory_service=None,
            event_bus=None,
            auditor=auditor
        )

    @pytest.fixture
    def retail_agent_with_auditor(self, auditor):
        """Create RetailAgent with Auditor integration"""
        return RetailAgent(
            event_bus=None,
            auditor=auditor
        )

    @pytest.fixture
    def mock_context(self):
        """Create mock context"""
        return Context(
            email="restaurant@example.com",
            channel=ChannelType.TELEGRAM,
            session_id="session_123",
            user_profile={"tier": "pro"}
        )

    @pytest.mark.asyncio
    async def test_brain_auditor_integration(self, brain_with_auditor, retail_agent_with_auditor, mock_context, auditor):
        """Test complete Brain + Auditor integration"""
        # Register retail agent
        brain_with_auditor.register_agent('retail', retail_agent_with_auditor)
        
        # Process message through Brain
        message = "Quantos pedidos tenho?"
        response = await brain_with_auditor.process(message, mock_context)
        
        # Verify audit logs were created
        assert auditor.table.put_item.call_count >= 3  # Start, classify, complete
        
        # Verify audit log structure for Brain operations
        calls = auditor.table.put_item.call_args_list
        
        # Check start operation
        start_call = calls[0][1]['Item']
        assert start_call['PK'] == "restaurant@example.com"
        assert start_call['action'] == "brain.process_start"
        assert start_call['agent'] == "brain"
        assert start_call['category'] == AuditCategory.SYSTEM_OPERATION.value
        assert start_call['status'] == "started"
        
        # Check classification operation
        classify_call = calls[1][1]['Item']
        assert classify_call['action'] == "brain.classify_intent"
        assert classify_call['agent'] == "brain"
        assert 'domain' in classify_call['output_data']
        assert 'confidence' in classify_call['output_data']
        
        # Check completion operation
        complete_call = calls[-1][1]['Item']
        assert complete_call['action'] == "brain.process_complete"
        assert complete_call['status'] == "success"
        assert 'duration_ms' in complete_call

    @pytest.mark.asyncio
    async def test_retail_agent_auditor_integration(self, retail_agent_with_auditor, mock_context, auditor):
        """Test complete RetailAgent + Auditor integration"""
        intent = Intent(
            domain="retail",
            action="check_orders",
            connector="ifood",
            confidence=0.9
        )
        
        # Execute action through RetailAgent
        result = await retail_agent_with_auditor.execute(intent, mock_context)
        
        # Verify audit logs were created
        assert auditor.table.put_item.call_count >= 2  # Start and complete
        
        # Verify audit log structure for RetailAgent operations
        calls = auditor.table.put_item.call_args_list
        
        # Check start operation
        start_call = calls[0][1]['Item']
        assert start_call['action'] == "retail.check_orders.start"
        assert start_call['agent'] == "retail_agent"
        assert start_call['category'] == AuditCategory.BUSINESS_OPERATION.value
        assert start_call['status'] == "started"
        
        # Check completion operation
        complete_call = calls[1][1]['Item']
        assert complete_call['action'] == "retail.check_orders"
        assert complete_call['agent'] == "retail_agent"
        assert complete_call['status'] == "success"
        assert 'duration_ms' in complete_call

    @pytest.mark.asyncio
    async def test_end_to_end_audit_workflow(self, brain_with_auditor, retail_agent_with_auditor, mock_context, auditor):
        """Test complete end-to-end audit workflow"""
        # Register retail agent
        brain_with_auditor.register_agent('retail', retail_agent_with_auditor)
        
        # Process multiple messages to create audit trail
        messages = [
            "Quantos pedidos tenho?",
            "Confirme o pedido 123",
            "Qual foi meu faturamento hoje?"
        ]
        
        for message in messages:
            await brain_with_auditor.process(message, mock_context)
        
        # Verify comprehensive audit trail
        total_calls = auditor.table.put_item.call_count
        assert total_calls >= 9  # 3 messages × 3 operations each (start, classify, complete)
        
        # Verify all operations are properly logged
        calls = auditor.table.put_item.call_args_list
        
        # Check that all operations have required audit fields
        for call in calls:
            item = call[1]['Item']
            assert 'PK' in item  # User email
            assert 'SK' in item  # Sort key with timestamp
            assert 'audit_id' in item
            assert 'timestamp' in item
            assert 'agent' in item
            assert 'action' in item
            assert 'status' in item
            assert 'hash' in item
            assert 'ttl' in item

    @pytest.mark.asyncio
    async def test_audit_error_handling(self, brain_with_auditor, retail_agent_with_auditor, mock_context, auditor):
        """Test audit logging for error scenarios"""
        # Register retail agent
        brain_with_auditor.register_agent('retail', retail_agent_with_auditor)
        
        # Process message that will cause error (unsupported action)
        intent = Intent(
            domain="retail",
            action="nonexistent_action",
            confidence=0.9
        )
        
        result = await retail_agent_with_auditor.execute(intent, mock_context)
        
        # Verify error was logged
        assert not result['success']
        assert auditor.table.put_item.call_count >= 2
        
        # Check error audit log
        calls = auditor.table.put_item.call_args_list
        error_call = calls[1][1]['Item']  # Second call should be the error
        
        assert error_call['action'] == "retail.nonexistent_action.error"
        assert error_call['status'] == "error"
        assert error_call['level'] == AuditLevel.WARNING.value
        assert error_call['category'] == AuditCategory.ERROR_EVENT.value
        assert 'error_message' in error_call

    @pytest.mark.asyncio
    async def test_audit_sensitive_data_detection(self, retail_agent_with_auditor, mock_context, auditor):
        """Test sensitive data detection in audit logs"""
        intent = Intent(
            domain="retail",
            action="check_orders",
            connector="ifood",
            confidence=0.9
        )
        
        # Execute action that returns customer data
        result = await retail_agent_with_auditor.execute(intent, mock_context)
        
        # Verify sensitive data detection
        calls = auditor.table.put_item.call_args_list
        complete_call = calls[-1][1]['Item']
        
        # Should detect customer names in mock orders as sensitive data
        assert complete_call.get('sensitive_data') is True

    @pytest.mark.asyncio
    async def test_audit_financial_data_detection(self, retail_agent_with_auditor, mock_context, auditor):
        """Test financial data detection in audit logs"""
        intent = Intent(
            domain="retail",
            action="check_revenue",
            connector="ifood",
            confidence=0.9
        )
        
        # Execute action that returns financial data
        result = await retail_agent_with_auditor.execute(intent, mock_context)
        
        # Verify financial data detection
        calls = auditor.table.put_item.call_args_list
        complete_call = calls[-1][1]['Item']
        
        # Should detect revenue data as financial
        assert complete_call.get('financial_data') is True

    @pytest.mark.asyncio
    async def test_audit_category_classification(self, retail_agent_with_auditor, mock_context, auditor):
        """Test audit category classification for different actions"""
        test_cases = [
            ("check_orders", AuditCategory.DATA_ACCESS),
            ("confirm_order", AuditCategory.DATA_MODIFICATION),
            ("check_revenue", AuditCategory.DATA_ACCESS),
            ("manage_store", AuditCategory.DATA_MODIFICATION),
        ]
        
        for action, expected_category in test_cases:
            # Reset mock
            auditor.table.put_item.reset_mock()
            
            intent = Intent(
                domain="retail",
                action=action,
                connector="ifood",
                confidence=0.9
            )
            
            await retail_agent_with_auditor.execute(intent, mock_context)
            
            # Check category classification
            calls = auditor.table.put_item.call_args_list
            complete_call = calls[-1][1]['Item']
            
            assert complete_call['category'] == expected_category.value

    @pytest.mark.asyncio
    async def test_audit_performance_tracking(self, retail_agent_with_auditor, mock_context, auditor):
        """Test audit performance tracking (duration_ms)"""
        intent = Intent(
            domain="retail",
            action="check_orders",
            connector="ifood",
            confidence=0.9
        )
        
        # Execute action
        result = await retail_agent_with_auditor.execute(intent, mock_context)
        
        # Verify duration tracking
        calls = auditor.table.put_item.call_args_list
        complete_call = calls[-1][1]['Item']
        
        assert 'duration_ms' in complete_call
        assert isinstance(complete_call['duration_ms'], (int, float))
        assert complete_call['duration_ms'] >= 0

    @pytest.mark.asyncio
    async def test_audit_correlation_tracking(self, brain_with_auditor, retail_agent_with_auditor, mock_context, auditor):
        """Test audit correlation tracking across Brain and RetailAgent"""
        # Register retail agent
        brain_with_auditor.register_agent('retail', retail_agent_with_auditor)
        
        # Process message
        message = "Quantos pedidos tenho?"
        await brain_with_auditor.process(message, mock_context)
        
        # Verify session correlation
        calls = auditor.table.put_item.call_args_list
        
        for call in calls:
            item = call[1]['Item']
            assert item['session_id'] == "session_123"
            assert item['channel'] == "telegram"
            assert item['user_email'] == "restaurant@example.com"

    @pytest.mark.asyncio
    async def test_audit_ttl_configuration(self, auditor):
        """Test audit TTL configuration for compliance"""
        # Log a transaction
        await auditor.log_transaction(
            email="test@example.com",
            action="test_action",
            input_data={"test": "data"},
            output_data={"result": "success"},
            agent="test_agent"
        )
        
        # Verify TTL is set correctly (1 year)
        call_args = auditor.table.put_item.call_args[1]
        item = call_args['Item']
        
        assert 'ttl' in item
        
        # TTL should be approximately 1 year from now
        expected_ttl = int((datetime.utcnow() + timedelta(days=365)).timestamp())
        actual_ttl = item['ttl']
        
        # Allow 1 hour tolerance
        assert abs(actual_ttl - expected_ttl) < 3600

    @pytest.mark.asyncio
    async def test_audit_hash_integrity(self, auditor):
        """Test audit hash integrity verification"""
        # Log a transaction
        audit_id = await auditor.log_transaction(
            email="test@example.com",
            action="test_action",
            input_data={"test": "data"},
            output_data={"result": "success"},
            agent="test_agent"
        )
        
        # Verify hash was calculated
        call_args = auditor.table.put_item.call_args[1]
        item = call_args['Item']
        
        assert 'hash' in item
        assert len(item['hash']) == 64  # SHA-256 hex length
        
        # Verify hash is deterministic
        from app.core.auditor import AuditEntry
        entry = AuditEntry(
            audit_id=item['audit_id'],
            timestamp=item['timestamp'],
            timezone=item['timezone'],
            user_email=item['user_email'],
            user_id=item['user_id'],
            session_id=item['session_id'],
            channel=item['channel'],
            agent=item['agent'],
            action=item['action'],
            category=AuditCategory(item['category']),
            level=AuditLevel(item['level']),
            input_data=item['input_data'],
            output_data=item['output_data'],
            context=item['context'],
            status=item['status'],
            error_message=item['error_message'],
            duration_ms=item['duration_ms'],
            request_id=item['request_id'],
            correlation_id=item['correlation_id'],
            parent_audit_id=item['parent_audit_id'],
            sensitive_data=item['sensitive_data'],
            pii_data=item['pii_data'],
            financial_data=item['financial_data'],
            hash=item['hash'],
            signature=item['signature']
        )
        
        # Verify integrity
        assert entry.verify_integrity() is True

    @pytest.mark.asyncio
    async def test_lgpd_compliance_workflow(self, brain_with_auditor, retail_agent_with_auditor, mock_context, auditor):
        """Test LGPD compliance workflow"""
        # Register retail agent
        brain_with_auditor.register_agent('retail', retail_agent_with_auditor)
        
        # Process message that involves personal data
        message = "Quantos pedidos tenho?"
        await brain_with_auditor.process(message, mock_context)
        
        # Generate compliance report
        start_date = datetime.utcnow() - timedelta(hours=1)
        end_date = datetime.utcnow()
        
        # Mock audit logs for compliance report
        from app.core.auditor import AuditEntry
        mock_logs = [
            AuditEntry(
                audit_id="audit_1",
                timestamp=datetime.utcnow().isoformat() + 'Z',
                timezone="UTC",
                user_email="restaurant@example.com",
                user_id=None,
                session_id="session_123",
                channel="telegram",
                agent="brain",
                action="brain.process_complete",
                category=AuditCategory.BUSINESS_OPERATION,
                level=AuditLevel.INFO,
                input_data={"message": message},
                output_data={"response": "success"},
                context={},
                status="success",
                error_message=None,
                duration_ms=150.0,
                request_id=None,
                correlation_id=None,
                parent_audit_id=None,
                sensitive_data=True,
                pii_data=True,
                financial_data=True,
                hash="hash1",
                signature=None
            )
        ]
        
        with patch.object(auditor, 'get_audit_logs', return_value=mock_logs):
            report = await auditor.generate_compliance_report(
                start_date=start_date,
                end_date=end_date,
                user_email="restaurant@example.com"
            )
            
            # Verify LGPD compliance features
            assert report.total_operations == 1
            assert report.pii_operations == 1
            assert report.financial_operations == 1
            assert report.sensitive_operations == 1
            assert report.lgpd_compliant is True  # No integrity violations
            
            # Test data export for LGPD
            exported_data = await auditor.export_logs_for_compliance(
                email="restaurant@example.com",
                start_date=start_date,
                end_date=end_date,
                format="json"
            )
            
            # Verify export contains audit data
            parsed_data = json.loads(exported_data)
            assert len(parsed_data) == 1
            assert parsed_data[0]['user_email'] == "restaurant@example.com"
            assert parsed_data[0]['pii_data'] is True

    @pytest.mark.asyncio
    async def test_audit_system_resilience(self, brain_with_auditor, retail_agent_with_auditor, mock_context, auditor):
        """Test audit system resilience to failures"""
        # Register retail agent
        brain_with_auditor.register_agent('retail', retail_agent_with_auditor)
        
        # Mock DynamoDB failure
        auditor.table.put_item.side_effect = Exception("DynamoDB error")
        
        # Process message - should not fail even if audit fails
        message = "Quantos pedidos tenho?"
        response = await brain_with_auditor.process(message, mock_context)
        
        # Verify system continues to work despite audit failure
        assert response is not None
        assert "erro" not in response.lower()  # Should not show audit error to user

    @pytest.mark.asyncio
    async def test_audit_concurrent_operations(self, retail_agent_with_auditor, mock_context, auditor):
        """Test audit logging for concurrent operations"""
        import asyncio
        
        # Create multiple concurrent operations
        intents = [
            Intent(domain="retail", action="check_orders", connector="ifood", confidence=0.9),
            Intent(domain="retail", action="check_revenue", connector="ifood", confidence=0.9),
            Intent(domain="retail", action="manage_store", connector="ifood", confidence=0.9),
        ]
        
        # Execute concurrently
        tasks = [retail_agent_with_auditor.execute(intent, mock_context) for intent in intents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all operations completed successfully
        for result in results:
            assert not isinstance(result, Exception)
            assert result.get('success') is not False
        
        # Verify all operations were audited
        assert auditor.table.put_item.call_count >= 6  # 3 operations × 2 logs each (start + complete)