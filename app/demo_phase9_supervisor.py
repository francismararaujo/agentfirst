#!/usr/bin/env python3
"""
Demo Script for Phase 9 - Supervisor (H.I.T.L.)

This script demonstrates the Human-in-the-Loop (H.I.T.L.) functionality:
1. Decision evaluation and escalation
2. Supervisor notification via Telegram
3. Human decision processing
4. Learning from feedback
5. Pattern recognition and improvement

Usage:
    python app/demo_phase9_supervisor.py

Requirements:
    - AWS credentials configured
    - DynamoDB tables created
    - Telegram bot token configured
    - Supervisor chat ID configured
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.supervisor import (
    Supervisor, EscalationRequest, EscalationStatus, DecisionComplexity,
    EscalationReason
)
from app.core.brain import Brain, Context, Intent
from app.core.auditor import Auditor
from app.omnichannel.models import ChannelType
from app.omnichannel.telegram_service import TelegramService
from app.config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SupervisorDemo:
    """Demo class for Supervisor (H.I.T.L.) functionality"""
    
    def __init__(self):
        """Initialize demo components"""
        self.auditor = Auditor()
        self.telegram_service = TelegramService()
        self.supervisor = Supervisor(
            auditor=self.auditor,
            telegram_service=self.telegram_service
        )
        self.brain = Brain(
            auditor=self.auditor,
            supervisor=self.supervisor
        )
        
        # Demo data
        self.demo_scenarios = [
            {
                "name": "Low Risk Order Check",
                "user_email": "customer1@example.com",
                "agent": "retail_agent",
                "action": "check_orders",
                "proposed_decision": {"orders": 3, "total_value": 45.50},
                "context": {"user_profile": {"tier": "free"}},
                "confidence": 0.9,
                "expected_supervision": False
            },
            {
                "name": "High Value Order Cancellation",
                "user_email": "vip@example.com",
                "agent": "retail_agent",
                "action": "cancel_order",
                "proposed_decision": {
                    "cancel": True,
                    "order_id": "12345",
                    "amount": 1500.00,
                    "reason": "customer_request"
                },
                "context": {
                    "user_profile": {"tier": "enterprise"},
                    "order_details": {"restaurant": "Fine Dining", "items": 8}
                },
                "confidence": 0.6,
                "expected_supervision": True
            },
            {
                "name": "Critical Data Deletion",
                "user_email": "admin@example.com",
                "agent": "system_agent",
                "action": "delete_user_data",
                "proposed_decision": {
                    "delete": True,
                    "data_type": "personal_information",
                    "user_count": 1
                },
                "context": {
                    "user_profile": {"tier": "enterprise"},
                    "compliance_required": True,
                    "has_error": False
                },
                "confidence": 0.3,
                "expected_supervision": True
            },
            {
                "name": "System Error Recovery",
                "user_email": "support@example.com",
                "agent": "retail_agent",
                "action": "retry_payment",
                "proposed_decision": {
                    "retry": True,
                    "payment_id": "pay_67890",
                    "amount": 89.99
                },
                "context": {
                    "user_profile": {"tier": "pro"},
                    "has_error": True,
                    "error_type": "payment_gateway_timeout"
                },
                "confidence": 0.4,
                "expected_supervision": True
            },
            {
                "name": "Routine Inventory Check",
                "user_email": "manager@restaurant.com",
                "agent": "retail_agent",
                "action": "check_inventory",
                "proposed_decision": {"items": 25, "low_stock": 3},
                "context": {"user_profile": {"tier": "pro"}},
                "confidence": 0.85,
                "expected_supervision": False
            }
        ]
    
    async def setup_demo_supervisor(self):
        """Configure demo supervisor"""
        print("🔧 Configurando supervisor de demonstração...")
        
        # Configure demo supervisor
        # Note: In production, use a real supervisor's Telegram chat ID
        demo_chat_id = "123456789"  # Replace with actual chat ID for testing
        
        self.supervisor.configure_supervisor(
            supervisor_id="demo_supervisor",
            name="Demo Supervisor",
            telegram_chat_id=demo_chat_id,
            specialties=["retail", "system", "general"],
            priority_threshold=1
        )
        
        print(f"✅ Supervisor configurado: demo_supervisor (Chat ID: {demo_chat_id})")
        print(f"   Especialidades: retail, system, general")
        print(f"   Threshold de prioridade: 1")
        print()
    
    async def run_decision_evaluation_demo(self):
        """Demonstrate decision evaluation and escalation"""
        print("=" * 60)
        print("🧠 DEMO: AVALIAÇÃO DE DECISÕES E ESCALAÇÃO")
        print("=" * 60)
        print()
        
        escalation_ids = []
        
        for i, scenario in enumerate(self.demo_scenarios, 1):
            print(f"📋 Cenário {i}: {scenario['name']}")
            print(f"   Usuário: {scenario['user_email']}")
            print(f"   Agente: {scenario['agent']}")
            print(f"   Ação: {scenario['action']}")
            print(f"   Confiança: {scenario['confidence']:.0%}")
            print(f"   Supervisão esperada: {'Sim' if scenario['expected_supervision'] else 'Não'}")
            print()
            
            # Evaluate decision
            requires_supervision, escalation_id = await self.supervisor.evaluate_decision(
                user_email=scenario['user_email'],
                agent=scenario['agent'],
                action=scenario['action'],
                proposed_decision=scenario['proposed_decision'],
                context=scenario['context'],
                confidence=scenario['confidence']
            )
            
            # Check if prediction matches expectation
            prediction_correct = requires_supervision == scenario['expected_supervision']
            status_emoji = "✅" if prediction_correct else "❌"
            
            print(f"   {status_emoji} Resultado: {'Requer supervisão' if requires_supervision else 'Aprovado automaticamente'}")
            
            if requires_supervision:
                print(f"   📋 ID da escalação: {escalation_id}")
                escalation_ids.append(escalation_id)
                
                if settings.ENVIRONMENT != "test":
                    print(f"   📱 Notificação enviada para supervisor via Telegram")
            
            print(f"   🎯 Predição: {'Correta' if prediction_correct else 'Incorreta'}")
            print("-" * 40)
            print()
        
        return escalation_ids
    
    async def simulate_human_decisions(self, escalation_ids: list):
        """Simulate human decisions on escalations"""
        if not escalation_ids:
            print("ℹ️  Nenhuma escalação para processar.")
            return
        
        print("=" * 60)
        print("👤 DEMO: PROCESSAMENTO DE DECISÕES HUMANAS")
        print("=" * 60)
        print()
        
        # Simulate different human decisions
        decisions = [
            ("approve", "Aprovado - valor justificado para cliente VIP"),
            ("reject", "Rejeitado - risco muito alto para operação crítica"),
            ("approve", "Aprovado - erro de sistema, retry é seguro"),
            ("reject", "Rejeitado - necessário mais informações"),
            ("approve", "Aprovado - operação de rotina")
        ]
        
        for i, escalation_id in enumerate(escalation_ids):
            if i >= len(decisions):
                break
                
            decision, feedback = decisions[i]
            
            print(f"📋 Processando escalação: {escalation_id}")
            print(f"   👤 Decisão do supervisor: {decision.upper()}")
            print(f"   💬 Feedback: {feedback}")
            
            # Process human decision
            success = await self.supervisor.process_human_decision(
                escalation_id=escalation_id,
                decision=decision,
                feedback=feedback,
                supervisor_id="demo_supervisor"
            )
            
            if success:
                print(f"   ✅ Decisão processada com sucesso")
                print(f"   🧠 Sistema aprendeu com a decisão")
            else:
                print(f"   ❌ Erro ao processar decisão")
            
            print("-" * 40)
            print()
    
    async def demonstrate_learning(self):
        """Demonstrate learning from human decisions"""
        print("=" * 60)
        print("🎓 DEMO: APRENDIZADO DE PADRÕES")
        print("=" * 60)
        print()
        
        # Show learned patterns
        if self.supervisor._decision_patterns:
            print("📊 Padrões aprendidos:")
            print()
            
            for pattern_key, pattern in self.supervisor._decision_patterns.items():
                print(f"   🔍 Padrão: {pattern_key}")
                print(f"      Agente: {pattern.agent}")
                print(f"      Ação: {pattern.action}")
                print(f"      Ocorrências: {pattern.occurrences}")
                print(f"      Taxa de aprovação: {pattern.approval_rate:.0%}")
                print(f"      Threshold de confiança: {pattern.confidence_threshold:.0%}")
                print(f"      Última ocorrência: {pattern.last_seen.strftime('%Y-%m-%d %H:%M:%S')}")
                print()
        else:
            print("ℹ️  Nenhum padrão aprendido ainda.")
            print("   (Execute mais cenários para ver o aprendizado em ação)")
            print()
        
        # Show current confidence threshold
        print(f"🎯 Threshold de confiança atual: {self.supervisor.confidence_threshold:.0%}")
        print("   (Ajustado automaticamente baseado no aprendizado)")
        print()
    
    async def demonstrate_brain_integration(self):
        """Demonstrate Brain integration with Supervisor"""
        print("=" * 60)
        print("🧠 DEMO: INTEGRAÇÃO BRAIN + SUPERVISOR")
        print("=" * 60)
        print()
        
        # Mock retail agent
        class MockRetailAgent:
            async def execute(self, intent, context):
                return {
                    "success": True,
                    "action": intent.action,
                    "message": f"Ação {intent.action} executada com sucesso"
                }
        
        # Register mock agent
        self.brain.register_agent('retail', MockRetailAgent())
        
        # Test scenarios
        test_messages = [
            {
                "message": "Check my orders",
                "context": Context(
                    email="test@example.com",
                    channel=ChannelType.TELEGRAM,
                    session_id="demo_session",
                    user_profile={"tier": "free"}
                ),
                "expected_supervision": False
            },
            {
                "message": "Cancel order 12345 worth $2000",
                "context": Context(
                    email="vip@example.com",
                    channel=ChannelType.TELEGRAM,
                    session_id="demo_session_vip",
                    user_profile={"tier": "enterprise"}
                ),
                "expected_supervision": True
            }
        ]
        
        for i, test in enumerate(test_messages, 1):
            print(f"💬 Teste {i}: '{test['message']}'")
            print(f"   Usuário: {test['context'].email}")
            print(f"   Tier: {test['context'].user_profile['tier']}")
            print(f"   Supervisão esperada: {'Sim' if test['expected_supervision'] else 'Não'}")
            print()
            
            # Mock intent classification
            if "cancel" in test['message'].lower() and "2000" in test['message']:
                mock_intent = Intent(
                    domain="retail",
                    action="cancel_order",
                    connector="ifood",
                    confidence=0.4,  # Low confidence to trigger supervision
                    entities={"order_id": "12345", "amount": 2000.00}
                )
            else:
                mock_intent = Intent(
                    domain="retail",
                    action="check_orders",
                    connector="ifood",
                    confidence=0.9,  # High confidence, no supervision
                    entities={}
                )
            
            # Mock classification
            original_classify = self.brain._classify_intent
            self.brain._classify_intent = lambda msg, ctx: mock_intent
            
            try:
                # Process message
                response = await self.brain.process(
                    message=test['message'],
                    context=test['context']
                )
                
                # Check response
                supervision_triggered = "supervisão" in response.lower() or "escalação" in response.lower()
                prediction_correct = supervision_triggered == test['expected_supervision']
                
                print(f"   📤 Resposta: {response[:100]}{'...' if len(response) > 100 else ''}")
                print(f"   🎯 Supervisão acionada: {'Sim' if supervision_triggered else 'Não'}")
                print(f"   ✅ Predição: {'Correta' if prediction_correct else 'Incorreta'}")
                
            finally:
                # Restore original method
                self.brain._classify_intent = original_classify
            
            print("-" * 40)
            print()
    
    async def show_supervisor_stats(self):
        """Show supervisor statistics"""
        print("=" * 60)
        print("📊 ESTATÍSTICAS DO SUPERVISOR")
        print("=" * 60)
        print()
        
        # Show configuration
        print("⚙️  Configuração atual:")
        for supervisor_id, config in self.supervisor.supervisors.items():
            print(f"   👤 {supervisor_id}: {config['name']}")
            print(f"      Chat ID: {config['telegram_chat_id']}")
            print(f"      Especialidades: {', '.join(config['specialties'])}")
            print(f"      Threshold: {config['priority_threshold']}")
            print()
        
        # Show system settings
        print("🔧 Configurações do sistema:")
        print(f"   ⏱️  Timeout padrão: {self.supervisor.default_timeout_minutes} minutos")
        print(f"   🎯 Threshold de confiança: {self.supervisor.confidence_threshold:.0%}")
        print(f"   🔄 Max tentativas: {self.supervisor.max_retries}")
        print()
        
        # Show pattern cache info
        print("🧠 Cache de padrões:")
        print(f"   📊 Padrões em cache: {len(self.supervisor._decision_patterns)}")
        print(f"   ⏰ TTL do cache: {self.supervisor._pattern_cache_ttl} segundos")
        print(f"   🔄 Última atualização: {self.supervisor._last_pattern_update.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    async def run_complete_demo(self):
        """Run complete demo workflow"""
        print("🚀 INICIANDO DEMO COMPLETO - SUPERVISOR (H.I.T.L.)")
        print("=" * 60)
        print()
        
        try:
            # Setup
            await self.setup_demo_supervisor()
            
            # Run decision evaluation demo
            escalation_ids = await self.run_decision_evaluation_demo()
            
            # Simulate human decisions
            await self.simulate_human_decisions(escalation_ids)
            
            # Show learning
            await self.demonstrate_learning()
            
            # Show Brain integration
            await self.demonstrate_brain_integration()
            
            # Show statistics
            await self.show_supervisor_stats()
            
            print("=" * 60)
            print("✅ DEMO COMPLETO FINALIZADO COM SUCESSO!")
            print("=" * 60)
            print()
            print("🎯 Principais funcionalidades demonstradas:")
            print("   • Avaliação automática de decisões")
            print("   • Escalação para supervisão humana")
            print("   • Notificação via Telegram")
            print("   • Processamento de decisões humanas")
            print("   • Aprendizado de padrões")
            print("   • Integração com Brain")
            print("   • Melhoria contínua do sistema")
            print()
            print("📱 Para testar em produção:")
            print("   1. Configure um chat ID real do Telegram")
            print("   2. Execute cenários reais")
            print("   3. Responda às notificações com /approve ou /reject")
            print("   4. Observe o sistema aprender com suas decisões")
            print()
            
        except Exception as e:
            logger.error(f"Erro durante demo: {str(e)}")
            print(f"❌ Erro durante demo: {str(e)}")
            raise


async def main():
    """Main demo function"""
    demo = SupervisorDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    asyncio.run(main())