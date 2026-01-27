"""
Integration tests for Auditor

Tests complete audit workflows:
- End-to-end logging
- Compliance reporting
- LGPD compliance
- Data retention
- Integrity verification
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
import json

from app.core.auditor import Auditor, AuditLevel, AuditCategory
from app.domains.retail.retail_agent import RetailAgent
from app.core.brain import Intent, Context
from app.omnichannel.models import ChannelType


@pytest.mark.integration
class TestAuditorIntegration:
    """Integration tests for Auditor"""

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
    def retail_agent_with_auditor(self, auditor):
        """Create RetailAgent with Auditor"""
        return RetailAgent(auditor=auditor)

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
    async def test_end_to_end_audit_logging(self, retail_agent_with_auditor, mock_context, auditor):
        """Test end-to-end audit logging through RetailAgent"""
        intent = Intent(
            domain="retail",
            action="check_orders",
            connector="ifood",
            confidence=0.9,
            entities={"time_period": "today"}
        )
        
        # Execute action through RetailAgent (should trigger audit logging)
        result = await retail_agent_with_auditor.execute(intent, mock_context)
        
        # Verify audit log was created
        assert auditor.table.put_item.called
        
        # Verify audit log structure
        call_args = auditor.table.put_item.call_args[1]
        item = call_args['Item']
        
        assert item['PK'] == "restaurant@example.com"
        assert item['SK'].startswith("AUDIT#")
        assert item['agent'] == "retail_agent"
        assert item['action'] == "retail.check_orders"
        assert item['category'] == AuditCategory.BUSINESS_OPERATION.value
        assert item['status'] == "success"
        assert 'hash' in item
        assert 'ttl' in item

    @pytest.mark.asyncio
    async def test_audit_logging_with_error(self, retail_agent_with_auditor, mock_context, auditor):
        """Test audit logging when operation fails"""
        # Create intent that will fail
        intent = Intent(
            domain="retail",
            action="nonexistent_action",
            confidence=0.9
        )
        
        # Execute action (should fail and log error)
        result = await retail_agent_with_auditor.execute(intent, mock_context)
        
        # Verify error was logged
        assert result['success'] is False
        assert auditor.table.put_item.called
        
        # Verify error details in audit log
        call_args = auditor.table.put_item.call_args[1]
        item = call_args['Item']
        
        assert item['status'] == "error"
        assert 'error_message' in item

    @pytest.mark.asyncio
    async def test_sensitive_data_detection_integration(self, auditor):
        """Test sensitive data detection in real scenario"""
        # Log authentication event with sensitive data
        audit_id = await auditor.log_transaction(
            email="user@example.com",
            action="authenticate",
            input_data={
                "email": "user@example.com",
                "password": "secret123",
                "remember_me": True
            },
            output_data={
                "success": True,
                "token": "jwt_token_abc123",
                "expires_in": 3600
            },
            agent="auth_service",
            category=AuditCategory.AUTHENTICATION,
            level=AuditLevel.SECURITY
        )
        
        # Verify sensitive data was detected
        call_args = auditor.table.put_item.call_args[1]
        item = call_args['Item']
        
        assert item['sensitive_data'] is True
        assert item['pii_data'] is True
        assert item['category'] == AuditCategory.AUTHENTICATION.value
        assert item['level'] == AuditLevel.SECURITY.value

    @pytest.mark.asyncio
    async def test_financial_data_detection_integration(self, auditor):
        """Test financial data detection in real scenario"""
        # Log payment processing event
        audit_id = await auditor.log_transaction(
            email="customer@example.com",
            action="process_payment",
            input_data={
                "order_id": "order_123",
                "amount": 89.90,
                "payment_method": "credit_card",
                "card_last_four": "1234"
            },
            output_data={
                "payment_id": "pay_456",
                "status": "approved",
                "total": 89.90,
                "fee": 2.70
            },
            agent="payment_service",
            category=AuditCategory.BUSINESS_OPERATION,
            level=AuditLevel.INFO
        )
        
        # Verify financial data was detected
        call_args = auditor.table.put_item.call_args[1]
        item = call_args['Item']
        
        assert item['financial_data'] is True
        assert item['sensitive_data'] is True  # Credit card info
        assert item['category'] == AuditCategory.BUSINESS_OPERATION.value

    @pytest.mark.asyncio
    async def test_compliance_report_generation_integration(self, auditor):
        """Test complete compliance report generation"""
        # Create multiple audit logs with different characteristics
        audit_logs = [
            {
                'email': 'user1@example.com',
                'action': 'authenticate',
                'input_data': {'email': 'user1@example.com'},
                'output_data': {'success': True},
                'agent': 'auth_service',
                'category': AuditCategory.AUTHENTICATION,
                'level': AuditLevel.SECURITY,
                'status': 'success'
            },
            {
                'email': 'user1@example.com',
                'action': 'check_orders',
                'input_data': {'connector': 'ifood'},
                'output_data': {'orders': 5},
                'agent': 'retail_agent',
                'category': AuditCategory.BUSINESS_OPERATION,
                'level': AuditLevel.INFO,
                'status': 'success'
            },
            {
                'email': 'user1@example.com',
                'action': 'process_payment',
                'input_data': {'amount': 150.00},
                'output_data': {'payment_id': 'pay_123'},
                'agent': 'payment_service',
                'category': AuditCategory.BUSINESS_OPERATION,
                'level': AuditLevel.INFO,
                'status': 'success'
            },
            {
                'email': 'user1@example.com',
                'action': 'failed_operation',
                'input_data': {'test': 'data'},
                'output_data': {},
                'agent': 'test_service',
                'category': AuditCategory.SYSTEM_OPERATION,
                'level': AuditLevel.ERROR,
                'status': 'error'
            }
        ]
        
        # Log all transactions
        for log_data in audit_logs:
            await auditor.log_transaction(**log_data)
        
        # Mock get_audit_logs to return our test data
        from app.core.auditor import AuditEntry
        mock_audit_entries = []
        
        for i, log_data in enumerate(audit_logs):
            entry = AuditEntry(
                audit_id=f"audit_{i}",
                timestamp=datetime.utcnow().isoformat() + 'Z',
                timezone="UTC",
                user_email=log_data['email'],
                user_id=None,
                session_id=f"session_{i}",
                channel="telegram",
                agent=log_data['agent'],
                action=log_data['action'],
                category=log_data['category'],
                level=log_data['level'],
                input_data=log_data['input_data'],
                output_data=log_data['output_data'],
                context={},
                status=log_data['status'],
                error_message=None,
                duration_ms=100.0,
                request_id=None,
                correlation_id=None,
                parent_audit_id=None,
                sensitive_data='payment' in log_data['action'] or 'auth' in log_data['action'],
                pii_data='email' in str(log_data['input_data']),
                financial_data='payment' in log_data['action'] or 'amount' in str(log_data['input_data']),
                hash=f"hash_{i}",
                signature=None
            )
            mock_audit_entries.append(entry)
        
        with patch.object(auditor, 'get_audit_logs', return_value=mock_audit_entries):
            # Generate compliance report
            start_date = datetime.utcnow() - timedelta(days=1)
            end_date = datetime.utcnow()
            
            report = await auditor.generate_compliance_report(
                start_date=start_date,
                end_date=end_date,
                user_email="user1@example.com"
            )
            
            # Verify report statistics
            assert report.total_operations == 4
            assert report.successful_operations == 3
            assert report.failed_operations == 1
            assert report.security_events == 1
            
            # Verify category breakdown
            assert report.operations_by_category['authentication'] == 1
            assert report.operations_by_category['business_operation'] == 2
            assert report.operations_by_category['system_operation'] == 1
            
            # Verify agent breakdown
            assert report.operations_by_agent['auth_service'] == 1
            assert report.operations_by_agent['retail_agent'] == 1
            assert report.operations_by_agent['payment_service'] == 1
            assert report.operations_by_agent['test_service'] == 1
            
            # Verify level breakdown
            assert report.operations_by_level['info'] == 2
            assert report.operations_by_level['security'] == 1
            assert report.operations_by_level['error'] == 1
            
            # Verify data type counts
            assert report.pii_operations >= 1  # Authentication has email
            assert report.financial_operations >= 1  # Payment processing
            assert report.sensitive_operations >= 2  # Auth + Payment
            
            # Verify compliance flags
            assert report.lgpd_compliant is True  # No integrity violations
            assert report.hipaa_compliant is True
            assert report.sox_compliant is True

    @pytest.mark.asyncio
    async def test_data_retention_ttl_integration(self, auditor):
        """Test data retention TTL integration"""
        # Log transaction
        audit_id = await auditor.log_transaction(
            email="test@example.com",
            action="test_action",
            input_data={"test": "data"},
            output_data={"result": "success"},
            agent="test_agent"
        )
        
        # Verify TTL was set correctly
        call_args = auditor.table.put_item.call_args[1]
        item = call_args['Item']
        
        assert 'ttl' in item
        
        # TTL should be approximately 1 year from now
        expected_ttl = int((datetime.utcnow() + timedelta(days=365)).timestamp())
        actual_ttl = item['ttl']
        
        # Allow 1 hour tolerance
        assert abs(actual_ttl - expected_ttl) < 3600

    @pytest.mark.asyncio
    async def test_audit_log_integrity_verification_integration(self, auditor):
        """Test audit log integrity verification"""
        # Log transaction
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
        
        # Recreate AuditEntry and verify integrity
        from app.core.auditor import AuditEntry, AuditCategory, AuditLevel
        
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
    async def test_lgpd_compliance_integration(self, auditor):
        """Test LGPD compliance features"""
        # Log PII processing event
        audit_id = await auditor.log_transaction(
            email="user@example.com",
            action="process_personal_data",
            input_data={
                "name": "João Silva",
                "email": "joao@example.com",
                "cpf": "123.456.789-00",
                "phone": "+5511999999999"
            },
            output_data={
                "user_id": "user_123",
                "profile_created": True
            },
            agent="user_service",
            category=AuditCategory.DATA_MODIFICATION,
            level=AuditLevel.COMPLIANCE
        )
        
        # Verify PII data was detected and flagged
        call_args = auditor.table.put_item.call_args[1]
        item = call_args['Item']
        
        assert item['pii_data'] is True
        assert item['sensitive_data'] is True
        assert item['category'] == AuditCategory.DATA_MODIFICATION.value
        assert item['level'] == AuditLevel.COMPLIANCE.value
        
        # Test data export for LGPD compliance
        start_date = datetime.utcnow() - timedelta(hours=1)
        end_date = datetime.utcnow()
        
        # Mock audit logs for export
        mock_logs = [
            AuditEntry(
                audit_id=audit_id,
                timestamp=datetime.utcnow().isoformat() + 'Z',
                timezone="UTC",
                user_email="user@example.com",
                user_id=None,
                session_id="session_123",
                channel="web",
                agent="user_service",
                action="process_personal_data",
                category=AuditCategory.DATA_MODIFICATION,
                level=AuditLevel.COMPLIANCE,
                input_data=item['input_data'],
                output_data=item['output_data'],
                context={},
                status="success",
                error_message=None,
                duration_ms=200.0,
                request_id=None,
                correlation_id=None,
                parent_audit_id=None,
                sensitive_data=True,
                pii_data=True,
                financial_data=False,
                hash=item['hash'],
                signature=None
            )
        ]
        
        with patch.object(auditor, 'get_audit_logs', return_value=mock_logs):
            # Export logs for LGPD compliance
            exported_data = await auditor.export_logs_for_compliance(
                email="user@example.com",
                start_date=start_date,
                end_date=end_date,
                format="json"
            )
            
            # Verify export contains PII processing record
            parsed_data = json.loads(exported_data)
            assert len(parsed_data) == 1
            
            log_entry = parsed_data[0]
            assert log_entry['user_email'] == "user@example.com"
            assert log_entry['action'] == "process_personal_data"
            assert log_entry['pii_data'] is True
            assert log_entry['category'] == "data_modification"
            assert log_entry['level'] == "compliance"

    @pytest.mark.asyncio
    async def test_concurrent_audit_logging(self, auditor):
        """Test concurrent audit logging operations"""
        import asyncio
        
        # Create multiple concurrent logging operations
        tasks = []
        for i in range(10):
            task = auditor.log_transaction(
                email=f"user{i}@example.com",
                action=f"action_{i}",
                input_data={"index": i},
                output_data={"result": f"success_{i}"},
                agent="concurrent_agent"
            )
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all operations completed successfully
        for result in results:
            assert not isinstance(result, Exception)
            assert result.startswith("audit_")
        
        # Verify all logs were stored
        assert auditor.table.put_item.call_count == 10

    @pytest.mark.asyncio
    async def test_audit_correlation_tracking(self, auditor):
        """Test audit correlation tracking across operations"""
        correlation_id = "corr_123"
        parent_audit_id = None
        
        # Log parent operation
        parent_audit_id = await auditor.log_transaction(
            email="user@example.com",
            action="parent_operation",
            input_data={"operation": "parent"},
            output_data={"started": True},
            agent="parent_agent",
            correlation_id=correlation_id
        )
        
        # Log child operations
        child1_audit_id = await auditor.log_transaction(
            email="user@example.com",
            action="child_operation_1",
            input_data={"operation": "child1"},
            output_data={"completed": True},
            agent="child_agent",
            correlation_id=correlation_id,
            parent_audit_id=parent_audit_id
        )
        
        child2_audit_id = await auditor.log_transaction(
            email="user@example.com",
            action="child_operation_2",
            input_data={"operation": "child2"},
            output_data={"completed": True},
            agent="child_agent",
            correlation_id=correlation_id,
            parent_audit_id=parent_audit_id
        )
        
        # Verify correlation tracking
        assert auditor.table.put_item.call_count == 3
        
        # Check parent operation
        parent_call = auditor.table.put_item.call_args_list[0][1]['Item']
        assert parent_call['correlation_id'] == correlation_id
        assert parent_call['parent_audit_id'] is None
        
        # Check child operations
        child1_call = auditor.table.put_item.call_args_list[1][1]['Item']
        assert child1_call['correlation_id'] == correlation_id
        assert child1_call['parent_audit_id'] == parent_audit_id
        
        child2_call = auditor.table.put_item.call_args_list[2][1]['Item']
        assert child2_call['correlation_id'] == correlation_id
        assert child2_call['parent_audit_id'] == parent_audit_id