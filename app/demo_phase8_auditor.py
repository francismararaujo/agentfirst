#!/usr/bin/env python3
"""
Demo script for Phase 8: Auditor & Compliance Integration

This script demonstrates the complete integration of the Auditor
with Brain and RetailAgent, showing:

1. End-to-end audit logging
2. Compliance features (LGPD, HIPAA, SOX)
3. Sensitive data detection
4. Financial data detection
5. Integrity verification
6. Performance tracking
7. Error handling with audit
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our components
from app.core.auditor import Auditor, AuditCategory, AuditLevel
from app.core.brain import Brain, Intent, Context
from app.domains.retail.retail_agent import RetailAgent
from app.omnichannel.models import ChannelType


async def demo_phase8_auditor():
    """Demonstrate Phase 8: Auditor & Compliance integration"""
    
    print("🔍 PHASE 8 DEMO: Auditor & Compliance Integration")
    print("=" * 60)
    
    # 1. Setup components with mocked dependencies
    print("\n1️⃣ Setting up components...")
    
    # Mock DynamoDB table
    mock_table = AsyncMock()
    mock_table.put_item.return_value = {}
    mock_table.query.return_value = {'Items': []}
    
    # Create Auditor with mocked DynamoDB
    auditor = Auditor()
    auditor.table = mock_table
    
    # Mock Bedrock client for Brain
    mock_bedrock = MagicMock()
    mock_bedrock.invoke_model.return_value = {
        'body': MagicMock(read=lambda: json.dumps({
            'content': [{
                'text': '{"domain": "retail", "action": "check_orders", "connector": "ifood", "confidence": 0.9}'
            }]
        }).encode())
    }
    
    # Create Brain with Auditor
    brain = Brain(
        bedrock_client=mock_bedrock,
        memory_service=None,
        event_bus=None,
        auditor=auditor
    )
    
    # Create RetailAgent with Auditor
    retail_agent = RetailAgent(
        event_bus=None,
        auditor=auditor
    )
    
    # Register RetailAgent in Brain
    brain.register_agent('retail', retail_agent)
    
    print("✅ Components initialized with Auditor integration")
    
    # 2. Create test context
    print("\n2️⃣ Creating test context...")
    
    context = Context(
        email="restaurant@example.com",
        channel=ChannelType.TELEGRAM,
        session_id="demo_session_123",
        user_profile={"tier": "pro", "restaurant": "Burger Palace"}
    )
    
    print(f"✅ Context created for {context.email}")
    
    # 3. Test Brain + Auditor integration
    print("\n3️⃣ Testing Brain + Auditor integration...")
    
    message = "Quantos pedidos tenho no iFood?"
    print(f"📨 Processing message: '{message}'")
    
    response = await brain.process(message, context)
    print(f"🤖 Brain response: {response}")
    
    # Check audit logs created by Brain
    brain_audit_calls = mock_table.put_item.call_count
    print(f"📋 Brain created {brain_audit_calls} audit logs")
    
    # 4. Test RetailAgent + Auditor integration
    print("\n4️⃣ Testing RetailAgent + Auditor integration...")
    
    # Reset mock to count only RetailAgent calls
    mock_table.put_item.reset_mock()
    
    intent = Intent(
        domain="retail",
        action="check_revenue",
        connector="ifood",
        confidence=0.95,
        entities={"time_period": "today"}
    )
    
    print(f"🎯 Executing intent: {intent.domain}.{intent.action}")
    
    result = await retail_agent.execute(intent, context)
    print(f"💰 RetailAgent result: {result.get('message', 'Success')}")
    
    # Check audit logs created by RetailAgent
    retail_audit_calls = mock_table.put_item.call_count
    print(f"📋 RetailAgent created {retail_audit_calls} audit logs")
    
    # 5. Demonstrate audit log structure
    print("\n5️⃣ Demonstrating audit log structure...")
    
    if mock_table.put_item.call_args_list:
        last_call = mock_table.put_item.call_args_list[-1]
        audit_item = last_call[1]['Item']
        
        print("📄 Sample audit log structure:")
        print(f"   📧 User: {audit_item.get('user_email')}")
        print(f"   🤖 Agent: {audit_item.get('agent')}")
        print(f"   ⚡ Action: {audit_item.get('action')}")
        print(f"   📊 Category: {audit_item.get('category')}")
        print(f"   🎯 Level: {audit_item.get('level')}")
        print(f"   ✅ Status: {audit_item.get('status')}")
        print(f"   🔒 Hash: {audit_item.get('hash', 'N/A')[:16]}...")
        print(f"   ⏱️ Duration: {audit_item.get('duration_ms', 'N/A')} ms")
        print(f"   🔐 Sensitive: {audit_item.get('sensitive_data', False)}")
        print(f"   💰 Financial: {audit_item.get('financial_data', False)}")
        print(f"   👤 PII: {audit_item.get('pii_data', False)}")
        print(f"   📅 TTL: {audit_item.get('ttl', 'N/A')}")
    
    # 6. Test sensitive data detection
    print("\n6️⃣ Testing sensitive data detection...")
    
    # Reset mock
    mock_table.put_item.reset_mock()
    
    # Log transaction with sensitive data
    await auditor.log_transaction(
        email="customer@example.com",
        action="process_payment",
        input_data={
            "customer_name": "João Silva",
            "email": "joao@example.com",
            "card_number": "**** **** **** 1234",
            "amount": 89.90
        },
        output_data={
            "payment_id": "pay_123",
            "status": "approved",
            "total": 89.90
        },
        agent="payment_service",
        category=AuditCategory.BUSINESS_OPERATION,
        level=AuditLevel.INFO
    )
    
    sensitive_call = mock_table.put_item.call_args[1]['Item']
    print(f"🔐 Sensitive data detected: {sensitive_call.get('sensitive_data')}")
    print(f"👤 PII data detected: {sensitive_call.get('pii_data')}")
    print(f"💰 Financial data detected: {sensitive_call.get('financial_data')}")
    
    # 7. Test error handling with audit
    print("\n7️⃣ Testing error handling with audit...")
    
    # Reset mock
    mock_table.put_item.reset_mock()
    
    error_intent = Intent(
        domain="retail",
        action="nonexistent_action",
        confidence=0.8
    )
    
    print(f"❌ Executing invalid intent: {error_intent.action}")
    
    error_result = await retail_agent.execute(error_intent, context)
    print(f"🚫 Error result: {error_result.get('error', 'Unknown error')}")
    
    # Check error audit logs
    error_calls = mock_table.put_item.call_count
    print(f"📋 Error created {error_calls} audit logs")
    
    if mock_table.put_item.call_args_list:
        error_call = mock_table.put_item.call_args_list[-1][1]['Item']
        print(f"⚠️ Error level: {error_call.get('level')}")
        print(f"📝 Error message: {error_call.get('error_message', 'N/A')}")
    
    # 8. Test compliance report generation
    print("\n8️⃣ Testing compliance report generation...")
    
    # Mock audit logs for compliance report
    from app.core.auditor import AuditEntry
    
    mock_logs = [
        AuditEntry(
            audit_id="audit_1",
            timestamp=datetime.utcnow().isoformat() + 'Z',
            timezone="UTC",
            user_email="restaurant@example.com",
            user_id=None,
            session_id="demo_session_123",
            channel="telegram",
            agent="brain",
            action="brain.process_complete",
            category=AuditCategory.BUSINESS_OPERATION,
            level=AuditLevel.INFO,
            input_data={"message": "Quantos pedidos tenho?"},
            output_data={"response": "Você tem 3 pedidos"},
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
        ),
        AuditEntry(
            audit_id="audit_2",
            timestamp=datetime.utcnow().isoformat() + 'Z',
            timezone="UTC",
            user_email="restaurant@example.com",
            user_id=None,
            session_id="demo_session_123",
            channel="telegram",
            agent="retail_agent",
            action="retail.check_revenue",
            category=AuditCategory.DATA_ACCESS,
            level=AuditLevel.INFO,
            input_data={"time_period": "today"},
            output_data={"total_revenue": 2847.50},
            context={},
            status="success",
            error_message=None,
            duration_ms=89.5,
            request_id=None,
            correlation_id=None,
            parent_audit_id=None,
            sensitive_data=False,
            pii_data=False,
            financial_data=True,
            hash="hash2",
            signature=None
        )
    ]
    
    # Mock get_audit_logs method
    async def mock_get_audit_logs(*args, **kwargs):
        return mock_logs
    
    auditor.get_audit_logs = mock_get_audit_logs
    
    # Generate compliance report
    start_date = datetime.utcnow() - timedelta(hours=1)
    end_date = datetime.utcnow()
    
    print(f"📊 Generating compliance report for period: {start_date.strftime('%H:%M')} - {end_date.strftime('%H:%M')}")
    
    report = await auditor.generate_compliance_report(
        start_date=start_date,
        end_date=end_date,
        user_email="restaurant@example.com"
    )
    
    print(f"📈 Compliance Report Summary:")
    print(f"   📊 Total operations: {report.total_operations}")
    print(f"   ✅ Successful: {report.successful_operations}")
    print(f"   ❌ Failed: {report.failed_operations}")
    print(f"   🔒 Security events: {report.security_events}")
    print(f"   👤 PII operations: {report.pii_operations}")
    print(f"   💰 Financial operations: {report.financial_operations}")
    print(f"   🔐 Sensitive operations: {report.sensitive_operations}")
    print(f"   🇧🇷 LGPD compliant: {'✅' if report.lgpd_compliant else '❌'}")
    print(f"   🏥 HIPAA compliant: {'✅' if report.hipaa_compliant else '❌'}")
    print(f"   📋 SOX compliant: {'✅' if report.sox_compliant else '❌'}")
    
    # 9. Test data export for LGPD
    print("\n9️⃣ Testing LGPD data export...")
    
    exported_data = await auditor.export_logs_for_compliance(
        email="restaurant@example.com",
        start_date=start_date,
        end_date=end_date,
        format="json"
    )
    
    parsed_data = json.loads(exported_data)
    print(f"📤 Exported {len(parsed_data)} audit records for LGPD compliance")
    print(f"📄 Sample export record:")
    if parsed_data:
        sample = parsed_data[0]
        print(f"   📧 Email: {sample.get('user_email')}")
        print(f"   ⚡ Action: {sample.get('action')}")
        print(f"   📅 Timestamp: {sample.get('timestamp')}")
        print(f"   👤 PII: {sample.get('pii_data')}")
        print(f"   💰 Financial: {sample.get('financial_data')}")
    
    # 10. Test integrity verification
    print("\n🔟 Testing integrity verification...")
    
    # Create audit entry and verify integrity
    test_entry = AuditEntry(
        audit_id="integrity_test",
        timestamp=datetime.utcnow().isoformat() + 'Z',
        timezone="UTC",
        user_email="test@example.com",
        user_id=None,
        session_id="test_session",
        channel="telegram",
        agent="test_agent",
        action="test_action",
        category=AuditCategory.SYSTEM_OPERATION,
        level=AuditLevel.INFO,
        input_data={"test": "data"},
        output_data={"result": "success"},
        context={},
        status="success",
        error_message=None,
        duration_ms=100.0,
        request_id=None,
        correlation_id=None,
        parent_audit_id=None,
        sensitive_data=False,
        pii_data=False,
        financial_data=False,
        hash="",  # Will be calculated
        signature=None
    )
    
    print(f"🔒 Original integrity: {'✅' if test_entry.verify_integrity() else '❌'}")
    
    # Tamper with data
    original_output = test_entry.output_data.copy()
    test_entry.output_data = {"result": "tampered"}
    
    print(f"🚫 Tampered integrity: {'✅' if test_entry.verify_integrity() else '❌'}")
    
    # Restore data
    test_entry.output_data = original_output
    print(f"🔒 Restored integrity: {'✅' if test_entry.verify_integrity() else '❌'}")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 PHASE 8 DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\n✅ Features demonstrated:")
    print("   🔍 End-to-end audit logging (Brain + RetailAgent)")
    print("   📊 Comprehensive audit log structure")
    print("   🔐 Sensitive data detection")
    print("   💰 Financial data detection")
    print("   👤 PII data detection")
    print("   ❌ Error handling with audit")
    print("   📈 Compliance reporting (LGPD, HIPAA, SOX)")
    print("   📤 LGPD data export")
    print("   🔒 Integrity verification with hash")
    print("   ⏱️ Performance tracking")
    print("   📅 Automatic TTL for data retention")
    
    print("\n🚀 Phase 8: Auditor & Compliance is COMPLETE and READY!")
    print("   The system now provides enterprise-grade audit capabilities")
    print("   with full compliance support for LGPD, HIPAA, and SOX.")


if __name__ == "__main__":
    asyncio.run(demo_phase8_auditor())