"""
Unit tests for Supervisor (H.I.T.L.)

Tests the Human-in-the-Loop functionality:
- Decision evaluation
- Escalation creation
- Human decision processing
- Learning from feedback
- Pattern recognition
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import json

from app.core.supervisor import (
    Supervisor, EscalationRequest, EscalationStatus, DecisionComplexity,
    EscalationReason, DecisionPattern
)
from app.core.auditor import Auditor


@pytest.mark.unit
class TestEscalationRequest:
    """Unit tests for EscalationRequest"""

    def test_escalation_request_creation(self):
        """Test EscalationRequest creation"""
        escalation = EscalationRequest(
            escalation_id="esc_test123",
            user_email="test@example.com",
            agent="retail_agent",
            action="cancel_order",
            context={"order_id": "123", "amount": 150.00},
            proposed_decision={"cancel": True, "reason": "customer_request"},
            confidence=0.7,
            complexity=DecisionComplexity.HIGH,
            reason=EscalationReason.HIGH_VALUE_TRANSACTION,
            priority=3
        )
        
        assert escalation.escalation_id == "esc_test123"
        assert escalation.user_email == "test@example.com"
        assert escalation.agent == "retail_agent"
        assert escalation.action == "cancel_order"
        assert escalation.complexity == DecisionComplexity.HIGH
        assert escalation.reason == EscalationReason.HIGH_VALUE_TRANSACTION
        assert escalation.status == EscalationStatus.PENDING
        assert escalation.priority == 3
        assert escalation.created_at is not None
        assert escalation.timeout_at is not None

    def test_escalation_request_timeout_calculation(self):
        """Test timeout calculation"""
        escalation = EscalationRequest(
            escalation_id="esc_test123",
            user_email="test@example.com",
            agent="retail_agent",
            action="test_action",
            context={},
            proposed_decision={},
            confidence=0.8,
            complexity=DecisionComplexity.MEDIUM,
            reason=EscalationReason.MANUAL_REVIEW
        )
        
        # Timeout should be 30 minutes from creation
        expected_timeout = escalation.created_at + timedelta(minutes=30)
        assert abs((escalation.timeout_at - expected_timeout).total_seconds()) < 1

    def test_escalation_request_is_expired(self):
        """Test expiration check"""
        # Create expired escalation
        past_time = datetime.utcnow() - timedelta(hours=1)
        escalation = EscalationRequest(
            escalation_id="esc_test123",
            user_email="test@example.com",
            agent="retail_agent",
            action="test_action",
            context={},
            proposed_decision={},
            confidence=0.8,
            complexity=DecisionComplexity.MEDIUM,
            reason=EscalationReason.MANUAL_REVIEW,
            created_at=past_time,
            timeout_at=past_time + timedelta(minutes=30)
        )
        
        assert escalation.is_expired() is True
        
        # Create non-expired escalation
        future_time = datetime.utcnow() + timedelta(hours=1)
        escalation.timeout_at = future_time
        assert escalation.is_expired() is False

    def test_escalation_request_priority_emoji(self):
        """Test priority emoji mapping"""
        escalation = EscalationRequest(
            escalation_id="esc_test123",
            user_email="test@example.com",
            agent="retail_agent",
            action="test_action",
            context={},
            proposed_decision={},
            confidence=0.8,
            complexity=DecisionComplexity.MEDIUM,
            reason=EscalationReason.MANUAL_REVIEW,
            priority=1
        )
        
        assert escalation.get_priority_emoji() == "🟢"  # Low priority
        
        escalation.priority = 2
        assert escalation.get_priority_emoji() == "🟡"  # Medium priority
        
        escalation.priority = 3
        assert escalation.get_priority_emoji() == "🟠"  # High priority
        
        escalation.priority = 4
        assert escalation.get_priority_emoji() == "🔴"  # Critical priority

    def test_escalation_request_serialization(self):
        """Test serialization to dict"""
        escalation = EscalationRequest(
            escalation_id="esc_test123",
            user_email="test@example.com",
            agent="retail_agent",
            action="cancel_order",
            context={"order_id": "123"},
            proposed_decision={"cancel": True},
            confidence=0.7,
            complexity=DecisionComplexity.HIGH,
            reason=EscalationReason.HIGH_VALUE_TRANSACTION
        )
        
        data = escalation.to_dict()
        
        assert isinstance(data, dict)
        assert data['escalation_id'] == "esc_test123"
        assert data['complexity'] == "high"
        assert data['reason'] == "high_value_transaction"
        assert data['status'] == "pending"
        assert 'created_at' in data
        assert 'timeout_at' in data


@pytest.mark.unit
class TestDecisionPattern:
    """Unit tests for DecisionPattern"""

    def test_decision_pattern_creation(self):
        """Test DecisionPattern creation"""
        pattern = DecisionPattern(
            pattern_id="retail:cancel_order",
            agent="retail_agent",
            action="cancel_order",
            context_features={"amount_range": "high", "user_tier": "pro"},
            decision_type="approved",
            human_approved=True,
            confidence_threshold=0.8
        )
        
        assert pattern.pattern_id == "retail:cancel_order"
        assert pattern.agent == "retail_agent"
        assert pattern.action == "cancel_order"
        assert pattern.human_approved is True
        assert pattern.confidence_threshold == 0.8
        assert pattern.occurrences == 1
        assert pattern.approval_rate == 0.0
        assert pattern.last_seen is not None


@pytest.mark.unit
class TestSupervisor:
    """Unit tests for Supervisor"""

    @pytest.fixture
    def mock_dynamodb_table(self):
        """Create mock DynamoDB table"""
        mock_table = MagicMock()
        mock_table.put_item.return_value = {}
        mock_table.get_item.return_value = {'Item': {}}
        return mock_table

    @pytest.fixture
    def mock_auditor(self):
        """Create mock Auditor"""
        auditor = AsyncMock()
        auditor.log_transaction.return_value = "audit_123"
        return auditor

    @pytest.fixture
    def mock_telegram_service(self):
        """Create mock Telegram service"""
        telegram = AsyncMock()
        telegram.send_message.return_value = {"ok": True}
        return telegram

    @pytest.fixture
    def supervisor(self, mock_dynamodb_table, mock_auditor, mock_telegram_service):
        """Create Supervisor instance with mocked dependencies"""
        with patch('boto3.resource') as mock_resource:
            mock_dynamodb = MagicMock()
            mock_dynamodb.Table.return_value = mock_dynamodb_table
            mock_resource.return_value = mock_dynamodb
            
            supervisor = Supervisor(
                auditor=mock_auditor,
                telegram_service=mock_telegram_service
            )
            supervisor.table = mock_dynamodb_table
            return supervisor

    def test_supervisor_initialization(self, supervisor):
        """Test Supervisor initialization"""
        assert supervisor.table_name == "AgentFirst-Escalation"
        assert supervisor.region == "us-east-1"
        assert supervisor.default_timeout_minutes == 30
        assert supervisor.confidence_threshold == 0.8
        assert "default" in supervisor.supervisors

    def test_configure_supervisor(self, supervisor):
        """Test supervisor configuration"""
        supervisor.configure_supervisor(
            supervisor_id="retail_supervisor",
            name="Retail Supervisor",
            telegram_chat_id="123456789",
            specialties=["retail", "finance"],
            priority_threshold=2
        )
        
        assert "retail_supervisor" in supervisor.supervisors
        config = supervisor.supervisors["retail_supervisor"]
        assert config["name"] == "Retail Supervisor"
        assert config["telegram_chat_id"] == "123456789"
        assert config["specialties"] == ["retail", "finance"]
        assert config["priority_threshold"] == 2

    @pytest.mark.asyncio
    async def test_assess_complexity_low(self, supervisor):
        """Test complexity assessment - low complexity"""
        complexity = await supervisor._assess_complexity(
            agent="retail_agent",
            action="check_orders",
            proposed_decision={"orders": 3},
            context={"user_profile": {"tier": "free"}},
            confidence=0.9
        )
        
        assert complexity == DecisionComplexity.LOW

    @pytest.mark.asyncio
    async def test_assess_complexity_high(self, supervisor):
        """Test complexity assessment - high complexity"""
        complexity = await supervisor._assess_complexity(
            agent="retail_agent",
            action="cancel_order",
            proposed_decision={"cancel": True, "amount": 1500.00},
            context={"has_error": True, "user_profile": {"tier": "enterprise"}},
            confidence=0.4
        )
        
        assert complexity in [DecisionComplexity.HIGH, DecisionComplexity.CRITICAL]

    @pytest.mark.asyncio
    async def test_assess_complexity_critical(self, supervisor):
        """Test complexity assessment - critical complexity"""
        complexity = await supervisor._assess_complexity(
            agent="retail_agent",
            action="delete_data",
            proposed_decision={"delete": True, "amount": 5000.00},
            context={"has_error": True, "user_profile": {"tier": "enterprise"}},
            confidence=0.2
        )
        
        assert complexity == DecisionComplexity.CRITICAL

    @pytest.mark.asyncio
    async def test_requires_supervision_critical(self, supervisor):
        """Test supervision requirement - critical decisions"""
        requires = await supervisor._requires_supervision(
            complexity=DecisionComplexity.CRITICAL,
            confidence=0.9,
            agent="retail_agent",
            action="delete_user",
            context={}
        )
        
        assert requires is True

    @pytest.mark.asyncio
    async def test_requires_supervision_low_confidence(self, supervisor):
        """Test supervision requirement - low confidence"""
        requires = await supervisor._requires_supervision(
            complexity=DecisionComplexity.MEDIUM,
            confidence=0.3,
            agent="retail_agent",
            action="check_orders",
            context={}
        )
        
        assert requires is True

    @pytest.mark.asyncio
    async def test_requires_supervision_high_confidence_low_complexity(self, supervisor):
        """Test supervision requirement - high confidence, low complexity"""
        requires = await supervisor._requires_supervision(
            complexity=DecisionComplexity.LOW,
            confidence=0.9,
            agent="retail_agent",
            action="check_orders",
            context={}
        )
        
        assert requires is False

    def test_determine_escalation_reason(self, supervisor):
        """Test escalation reason determination"""
        # High value transaction
        reason = supervisor._determine_escalation_reason(
            complexity=DecisionComplexity.HIGH,
            confidence=0.8,
            action="process_payment",
            context={"amount": 1500.00}
        )
        assert reason == EscalationReason.HIGH_VALUE_TRANSACTION
        
        # Error recovery
        reason = supervisor._determine_escalation_reason(
            complexity=DecisionComplexity.MEDIUM,
            confidence=0.6,
            action="retry_operation",
            context={"has_error": True}
        )
        assert reason == EscalationReason.ERROR_RECOVERY
        
        # System anomaly (very low confidence)
        reason = supervisor._determine_escalation_reason(
            complexity=DecisionComplexity.MEDIUM,
            confidence=0.2,
            action="check_orders",
            context={}
        )
        assert reason == EscalationReason.SYSTEM_ANOMALY

    def test_calculate_priority(self, supervisor):
        """Test priority calculation"""
        # High complexity + compliance reason + enterprise user
        priority = supervisor._calculate_priority(
            complexity=DecisionComplexity.HIGH,
            reason=EscalationReason.COMPLIANCE_CHECK,
            context={"user_profile": {"tier": "enterprise"}}
        )
        assert priority == 4  # Maximum priority
        
        # Low complexity + normal reason + free user
        priority = supervisor._calculate_priority(
            complexity=DecisionComplexity.LOW,
            reason=EscalationReason.MANUAL_REVIEW,
            context={"user_profile": {"tier": "free"}}
        )
        assert priority == 1  # Minimum priority

    def test_select_supervisor(self, supervisor):
        """Test supervisor selection"""
        # Configure specialized supervisor
        supervisor.configure_supervisor(
            supervisor_id="retail_expert",
            name="Retail Expert",
            telegram_chat_id="987654321",
            specialties=["retail"],
            priority_threshold=2
        )
        
        # Should select retail expert for retail agent with high priority
        supervisor_id, supervisor_info = supervisor._select_supervisor(
            agent="retail",
            action="cancel_order",
            priority=3
        )
        assert supervisor_id == "retail_expert"
        
        # Should select default for low priority
        supervisor_id, supervisor_info = supervisor._select_supervisor(
            agent="retail",
            action="check_orders",
            priority=1
        )
        assert supervisor_id == "default"

    def test_generate_escalation_id(self, supervisor):
        """Test escalation ID generation"""
        escalation_id = supervisor._generate_escalation_id()
        
        assert escalation_id.startswith("esc_")
        assert len(escalation_id) == 16  # "esc_" + 12 hex chars
        
        # Should generate unique IDs
        escalation_id2 = supervisor._generate_escalation_id()
        assert escalation_id != escalation_id2

    @pytest.mark.asyncio
    async def test_evaluate_decision_no_supervision(self, supervisor):
        """Test decision evaluation - no supervision required"""
        requires_supervision, escalation_id = await supervisor.evaluate_decision(
            user_email="test@example.com",
            agent="retail_agent",
            action="check_orders",
            proposed_decision={"orders": 3},
            context={"user_profile": {"tier": "free"}},
            confidence=0.9
        )
        
        assert requires_supervision is False
        assert escalation_id is None

    @pytest.mark.asyncio
    async def test_evaluate_decision_requires_supervision(self, supervisor):
        """Test decision evaluation - supervision required"""
        requires_supervision, escalation_id = await supervisor.evaluate_decision(
            user_email="test@example.com",
            agent="retail_agent",
            action="cancel_order",
            proposed_decision={"cancel": True, "amount": 1500.00},
            context={"user_profile": {"tier": "enterprise"}},
            confidence=0.4
        )
        
        assert requires_supervision is True
        assert escalation_id is not None
        assert escalation_id.startswith("esc_")

    @pytest.mark.asyncio
    async def test_create_escalation(self, supervisor, mock_dynamodb_table):
        """Test escalation creation"""
        escalation_id = await supervisor._create_escalation(
            user_email="test@example.com",
            agent="retail_agent",
            action="cancel_order",
            proposed_decision={"cancel": True},
            context={"order_id": "123"},
            confidence=0.6,
            complexity=DecisionComplexity.HIGH
        )
        
        assert escalation_id.startswith("esc_")
        mock_dynamodb_table.put_item.assert_called_once()
        
        # Verify item structure
        call_args = mock_dynamodb_table.put_item.call_args[1]
        item = call_args['Item']
        
        assert item['PK'] == escalation_id
        assert item['escalation_id'] == escalation_id
        assert item['user_email'] == "test@example.com"
        assert item['agent'] == "retail_agent"
        assert item['action'] == "cancel_order"
        assert item['complexity'] == "high"
        assert 'ttl' in item

    def test_format_escalation_message(self, supervisor):
        """Test escalation message formatting"""
        escalation = EscalationRequest(
            escalation_id="esc_test123",
            user_email="test@example.com",
            agent="retail_agent",
            action="cancel_order",
            context={"order_id": "123"},
            proposed_decision={"cancel": True, "reason": "customer_request"},
            confidence=0.7,
            complexity=DecisionComplexity.HIGH,
            reason=EscalationReason.HIGH_VALUE_TRANSACTION,
            priority=3
        )
        
        message = supervisor._format_escalation_message(escalation)
        
        assert "ESCALAÇÃO REQUERIDA" in message
        assert "esc_test123" in message
        assert "test@example.com" in message
        assert "retail_agent" in message
        assert "cancel_order" in message
        assert "HIGH" in message
        assert "70%" in message
        assert "/approve esc_test123" in message
        assert "/reject esc_test123" in message

    @pytest.mark.asyncio
    async def test_process_human_decision_approve(self, supervisor, mock_dynamodb_table):
        """Test processing human decision - approve"""
        # Mock escalation retrieval
        mock_escalation_data = {
            'escalation_id': 'esc_test123',
            'user_email': 'test@example.com',
            'agent': 'retail_agent',
            'action': 'cancel_order',
            'context': {'order_id': '123'},
            'proposed_decision': {'cancel': True},
            'confidence': 0.7,
            'complexity': 'high',
            'reason': 'high_value_transaction',
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'timeout_at': (datetime.utcnow() + timedelta(minutes=30)).isoformat(),
            'priority': 3,
            'tags': []
        }
        
        mock_dynamodb_table.get_item.return_value = {'Item': mock_escalation_data}
        
        success = await supervisor.process_human_decision(
            escalation_id="esc_test123",
            decision="approve",
            feedback="Approved by supervisor",
            supervisor_id="supervisor_1"
        )
        
        assert success is True
        
        # Verify escalation was updated
        assert mock_dynamodb_table.put_item.call_count >= 1

    @pytest.mark.asyncio
    async def test_process_human_decision_reject(self, supervisor, mock_dynamodb_table):
        """Test processing human decision - reject"""
        # Mock escalation retrieval
        mock_escalation_data = {
            'escalation_id': 'esc_test123',
            'user_email': 'test@example.com',
            'agent': 'retail_agent',
            'action': 'cancel_order',
            'context': {'order_id': '123'},
            'proposed_decision': {'cancel': True},
            'confidence': 0.7,
            'complexity': 'high',
            'reason': 'high_value_transaction',
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'timeout_at': (datetime.utcnow() + timedelta(minutes=30)).isoformat(),
            'priority': 3,
            'tags': []
        }
        
        mock_dynamodb_table.get_item.return_value = {'Item': mock_escalation_data}
        
        success = await supervisor.process_human_decision(
            escalation_id="esc_test123",
            decision="reject",
            feedback="Risk too high",
            supervisor_id="supervisor_1"
        )
        
        assert success is True

    @pytest.mark.asyncio
    async def test_process_human_decision_not_found(self, supervisor, mock_dynamodb_table):
        """Test processing human decision - escalation not found"""
        mock_dynamodb_table.get_item.return_value = {}  # No item found
        
        success = await supervisor.process_human_decision(
            escalation_id="esc_nonexistent",
            decision="approve",
            supervisor_id="supervisor_1"
        )
        
        assert success is False

    @pytest.mark.asyncio
    async def test_process_human_decision_expired(self, supervisor, mock_dynamodb_table):
        """Test processing human decision - expired escalation"""
        # Mock expired escalation
        past_time = datetime.utcnow() - timedelta(hours=1)
        mock_escalation_data = {
            'escalation_id': 'esc_test123',
            'user_email': 'test@example.com',
            'agent': 'retail_agent',
            'action': 'cancel_order',
            'context': {'order_id': '123'},
            'proposed_decision': {'cancel': True},
            'confidence': 0.7,
            'complexity': 'high',
            'reason': 'high_value_transaction',
            'status': 'pending',
            'created_at': past_time.isoformat(),
            'timeout_at': past_time.isoformat(),  # Already expired
            'priority': 3,
            'tags': []
        }
        
        mock_dynamodb_table.get_item.return_value = {'Item': mock_escalation_data}
        
        success = await supervisor.process_human_decision(
            escalation_id="esc_test123",
            decision="approve",
            supervisor_id="supervisor_1"
        )
        
        assert success is False

    def test_extract_context_features(self, supervisor):
        """Test context feature extraction"""
        context = {
            "amount": 750.00,
            "user_profile": {"tier": "pro"},
            "has_error": True
        }
        
        features = supervisor._extract_context_features(context)
        
        assert features["amount_range"] == "high"
        assert features["user_tier"] == "pro"
        assert features["has_error"] is True
        assert "hour_of_day" in features
        assert "day_of_week" in features

    def test_categorize_amount(self, supervisor):
        """Test amount categorization"""
        assert supervisor._categorize_amount(25.00) == "low"
        assert supervisor._categorize_amount(100.00) == "medium"
        assert supervisor._categorize_amount(500.00) == "high"
        assert supervisor._categorize_amount(2000.00) == "very_high"

    @pytest.mark.asyncio
    async def test_learn_from_decision_new_pattern(self, supervisor):
        """Test learning from decision - new pattern"""
        escalation = EscalationRequest(
            escalation_id="esc_test123",
            user_email="test@example.com",
            agent="retail_agent",
            action="cancel_order",
            context={"amount": 150.00},
            proposed_decision={"cancel": True},
            confidence=0.7,
            complexity=DecisionComplexity.HIGH,
            reason=EscalationReason.HIGH_VALUE_TRANSACTION,
            status=EscalationStatus.APPROVED
        )
        
        await supervisor._learn_from_decision(escalation)
        
        pattern_key = "retail_agent:cancel_order"
        assert pattern_key in supervisor._decision_patterns
        
        pattern = supervisor._decision_patterns[pattern_key]
        assert pattern.agent == "retail_agent"
        assert pattern.action == "cancel_order"
        assert pattern.human_approved is True
        assert pattern.approval_rate == 1.0
        assert pattern.occurrences == 1

    @pytest.mark.asyncio
    async def test_learn_from_decision_update_pattern(self, supervisor):
        """Test learning from decision - update existing pattern"""
        # Create existing pattern
        pattern_key = "retail_agent:cancel_order"
        supervisor._decision_patterns[pattern_key] = DecisionPattern(
            pattern_id=pattern_key,
            agent="retail_agent",
            action="cancel_order",
            context_features={},
            decision_type="approved",
            human_approved=True,
            confidence_threshold=0.8,
            occurrences=2,
            approval_rate=0.5  # 1 approved, 1 rejected
        )
        
        # New approved decision
        escalation = EscalationRequest(
            escalation_id="esc_test123",
            user_email="test@example.com",
            agent="retail_agent",
            action="cancel_order",
            context={},
            proposed_decision={"cancel": True},
            confidence=0.7,
            complexity=DecisionComplexity.HIGH,
            reason=EscalationReason.HIGH_VALUE_TRANSACTION,
            status=EscalationStatus.APPROVED
        )
        
        await supervisor._learn_from_decision(escalation)
        
        pattern = supervisor._decision_patterns[pattern_key]
        assert pattern.occurrences == 3
        assert pattern.approval_rate == (0.5 * 2 + 1.0) / 3  # Updated approval rate

    @pytest.mark.asyncio
    async def test_check_learned_patterns_high_approval(self, supervisor):
        """Test learned pattern check - high approval rate"""
        # Create pattern with high approval rate
        pattern_key = "retail_agent:check_orders"
        supervisor._decision_patterns[pattern_key] = DecisionPattern(
            pattern_id=pattern_key,
            agent="retail_agent",
            action="check_orders",
            context_features={},
            decision_type="approved",
            human_approved=True,
            confidence_threshold=0.8,
            approval_rate=0.9  # High approval rate
        )
        
        result = await supervisor._check_learned_patterns(
            agent="retail_agent",
            action="check_orders",
            context={},
            confidence=0.8
        )
        
        assert result is False  # Should not require supervision

    @pytest.mark.asyncio
    async def test_check_learned_patterns_low_approval(self, supervisor):
        """Test learned pattern check - low approval rate"""
        # Create pattern with low approval rate
        pattern_key = "retail_agent:delete_data"
        supervisor._decision_patterns[pattern_key] = DecisionPattern(
            pattern_id=pattern_key,
            agent="retail_agent",
            action="delete_data",
            context_features={},
            decision_type="rejected",
            human_approved=False,
            confidence_threshold=0.8,
            approval_rate=0.2  # Low approval rate
        )
        
        result = await supervisor._check_learned_patterns(
            agent="retail_agent",
            action="delete_data",
            context={},
            confidence=0.8
        )
        
        assert result is True  # Should require supervision

    @pytest.mark.asyncio
    async def test_check_learned_patterns_no_pattern(self, supervisor):
        """Test learned pattern check - no pattern found"""
        result = await supervisor._check_learned_patterns(
            agent="unknown_agent",
            action="unknown_action",
            context={},
            confidence=0.8
        )
        
        assert result is None  # No pattern found