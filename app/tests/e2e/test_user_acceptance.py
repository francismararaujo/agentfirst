"""
End-to-End User Acceptance Tests (Phase 13.3)

Tests complete user workflows and acceptance criteria:
- User registration flow
- Message processing workflow
- iFood integration workflow
- H.I.T.L. supervision workflow
- Billing and upgrade workflow
"""

import pytest
import requests
import time
import json
from datetime import datetime
from typing import Dict, Any
from unittest.mock import patch


@pytest.mark.e2e
class TestUserRegistrationFlow:
    """E2E tests for user registration workflow"""

    @pytest.fixture
    def production_url(self):
        """Production API URL"""
        return "https://ain6spik95.execute-api.us-east-1.amazonaws.com/prod"

    @pytest.fixture
    def test_user_data(self):
        """Test user data"""
        timestamp = int(time.time())
        return {
            "telegram_id": 999888777 + timestamp,  # Unique ID
            "email": f"test.user.{timestamp}@example.com",
            "first_name": "Test User"
        }

    def test_new_user_registration_flow(self, production_url, test_user_data):
        """Test complete new user registration flow"""
        
        # Step 1: New user sends greeting
        greeting_update = {
            "update_id": int(time.time()),
            "message": {
                "message_id": 1,
                "from": {
                    "id": test_user_data["telegram_id"],
                    "is_bot": False,
                    "first_name": test_user_data["first_name"]
                },
                "chat": {
                    "id": test_user_data["telegram_id"],
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "Oi"
            }
        }
        
        response = requests.post(
            f"{production_url}/webhook/telegram",
            json=greeting_update,
            timeout=30
        )
        
        # Should process successfully
        assert response.status_code == 200, f"Greeting should be processed, got {response.status_code}"
        
        # Step 2: User sends email for registration
        email_update = {
            "update_id": int(time.time()) + 1,
            "message": {
                "message_id": 2,
                "from": {
                    "id": test_user_data["telegram_id"],
                    "is_bot": False,
                    "first_name": test_user_data["first_name"]
                },
                "chat": {
                    "id": test_user_data["telegram_id"],
                    "type": "private"
                },
                "date": int(time.time()),
                "text": test_user_data["email"]
            }
        }
        
        response = requests.post(
            f"{production_url}/webhook/telegram",
            json=email_update,
            timeout=30
        )
        
        # Should process email registration
        assert response.status_code == 200, f"Email registration should be processed, got {response.status_code}"
        
        # Step 3: User asks about orders (should work now)
        orders_update = {
            "update_id": int(time.time()) + 2,
            "message": {
                "message_id": 3,
                "from": {
                    "id": test_user_data["telegram_id"],
                    "is_bot": False,
                    "first_name": test_user_data["first_name"]
                },
                "chat": {
                    "id": test_user_data["telegram_id"],
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "Quantos pedidos tenho?"
            }
        }
        
        response = requests.post(
            f"{production_url}/webhook/telegram",
            json=orders_update,
            timeout=30
        )
        
        # Should process order query
        assert response.status_code == 200, f"Order query should be processed, got {response.status_code}"

    def test_existing_user_flow(self, production_url):
        """Test flow for existing user"""
        
        # Use a known test user (should be created in setup)
        existing_user_update = {
            "update_id": int(time.time()),
            "message": {
                "message_id": 1,
                "from": {
                    "id": 123456789,  # Known test user
                    "is_bot": False,
                    "first_name": "Existing User"
                },
                "chat": {
                    "id": 123456789,
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "Status da minha conta"
            }
        }
        
        response = requests.post(
            f"{production_url}/webhook/telegram",
            json=existing_user_update,
            timeout=30
        )
        
        # Should process successfully for existing user
        assert response.status_code == 200, f"Existing user query should be processed, got {response.status_code}"


@pytest.mark.e2e
class TestMessageProcessingWorkflow:
    """E2E tests for message processing workflow"""

    @pytest.fixture
    def production_url(self):
        """Production API URL"""
        return "https://ain6spik95.execute-api.us-east-1.amazonaws.com/prod"

    @pytest.fixture
    def registered_user(self):
        """Registered test user"""
        return {
            "telegram_id": 123456789,
            "email": "test@example.com",
            "first_name": "Test User"
        }

    def test_natural_language_processing(self, production_url, registered_user):
        """Test natural language message processing"""
        
        # Test various natural language queries
        test_messages = [
            "Quantos pedidos tenho?",
            "Qual foi meu faturamento hoje?",
            "Feche a loja por 30 minutos",
            "Como está minha avaliação?",
            "Quais são meus itens mais vendidos?"
        ]
        
        for i, message_text in enumerate(test_messages):
            update = {
                "update_id": int(time.time()) + i,
                "message": {
                    "message_id": i + 1,
                    "from": {
                        "id": registered_user["telegram_id"],
                        "is_bot": False,
                        "first_name": registered_user["first_name"]
                    },
                    "chat": {
                        "id": registered_user["telegram_id"],
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": message_text
                }
            }
            
            response = requests.post(
                f"{production_url}/webhook/telegram",
                json=update,
                timeout=30
            )
            
            # Should process all natural language queries
            assert response.status_code == 200, f"Message '{message_text}' should be processed, got {response.status_code}"
            
            # Add small delay between requests
            time.sleep(1)

    def test_context_preservation(self, production_url, registered_user):
        """Test context preservation across messages"""
        
        # First message: Ask about orders
        first_update = {
            "update_id": int(time.time()),
            "message": {
                "message_id": 1,
                "from": {
                    "id": registered_user["telegram_id"],
                    "is_bot": False,
                    "first_name": registered_user["first_name"]
                },
                "chat": {
                    "id": registered_user["telegram_id"],
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "Quantos pedidos tenho?"
            }
        }
        
        response = requests.post(
            f"{production_url}/webhook/telegram",
            json=first_update,
            timeout=30
        )
        
        assert response.status_code == 200, "First message should be processed"
        
        time.sleep(2)  # Allow processing
        
        # Second message: Follow-up question (should use context)
        second_update = {
            "update_id": int(time.time()) + 1,
            "message": {
                "message_id": 2,
                "from": {
                    "id": registered_user["telegram_id"],
                    "is_bot": False,
                    "first_name": registered_user["first_name"]
                },
                "chat": {
                    "id": registered_user["telegram_id"],
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "Confirme o primeiro"
            }
        }
        
        response = requests.post(
            f"{production_url}/webhook/telegram",
            json=second_update,
            timeout=30
        )
        
        # Should process follow-up with context
        assert response.status_code == 200, "Follow-up message should be processed with context"

    def test_error_handling(self, production_url, registered_user):
        """Test error handling in message processing"""
        
        # Test various edge cases
        edge_cases = [
            "",  # Empty message
            "x" * 1000,  # Very long message
            "🍔🍕🌮🥗🍰",  # Only emojis
            "123456789",  # Only numbers
            "!@#$%^&*()",  # Only special characters
        ]
        
        for i, message_text in enumerate(edge_cases):
            if not message_text:  # Skip empty message for this test
                continue
                
            update = {
                "update_id": int(time.time()) + i,
                "message": {
                    "message_id": i + 1,
                    "from": {
                        "id": registered_user["telegram_id"],
                        "is_bot": False,
                        "first_name": registered_user["first_name"]
                    },
                    "chat": {
                        "id": registered_user["telegram_id"],
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": message_text
                }
            }
            
            response = requests.post(
                f"{production_url}/webhook/telegram",
                json=update,
                timeout=30
            )
            
            # Should handle edge cases gracefully (not crash)
            assert response.status_code == 200, f"Edge case '{message_text[:50]}...' should be handled gracefully"
            
            time.sleep(0.5)


@pytest.mark.e2e
class TestiFoodIntegrationWorkflow:
    """E2E tests for iFood integration workflow"""

    @pytest.fixture
    def production_url(self):
        """Production API URL"""
        return "https://ain6spik95.execute-api.us-east-1.amazonaws.com/prod"

    def test_ifood_webhook_processing(self, production_url):
        """Test iFood webhook event processing"""
        
        # Simulate iFood order event
        ifood_event = {
            "eventId": f"evt_test_{int(time.time())}",
            "eventType": "order.placed",
            "timestamp": datetime.now().isoformat() + "Z",
            "merchantId": "test_merchant_123",
            "data": {
                "orderId": f"order_test_{int(time.time())}",
                "customerId": "customer_test_123",
                "totalAmount": 45.50,
                "items": [
                    {
                        "name": "Hambúrguer Clássico",
                        "quantity": 1,
                        "price": 25.00
                    },
                    {
                        "name": "Batata Frita",
                        "quantity": 1,
                        "price": 12.00
                    },
                    {
                        "name": "Refrigerante",
                        "quantity": 1,
                        "price": 8.50
                    }
                ]
            }
        }
        
        # Note: This will fail signature validation (expected)
        # but tests that the endpoint processes the structure
        response = requests.post(
            f"{production_url}/webhook/ifood",
            json=ifood_event,
            timeout=30
        )
        
        # Should reject due to signature validation (expected behavior)
        assert response.status_code in [400, 401], f"iFood webhook should validate signature, got {response.status_code}"

    def test_ifood_order_queries(self, production_url):
        """Test iFood order queries through Telegram"""
        
        registered_user = {
            "telegram_id": 123456789,
            "email": "test@example.com",
            "first_name": "Test User"
        }
        
        # Test iFood-specific queries
        ifood_queries = [
            "Quantos pedidos tenho no iFood?",
            "Qual foi meu faturamento no iFood hoje?",
            "Confirme todos os pedidos pendentes do iFood",
            "Feche minha loja no iFood por 1 hora"
        ]
        
        for i, query in enumerate(ifood_queries):
            update = {
                "update_id": int(time.time()) + i,
                "message": {
                    "message_id": i + 1,
                    "from": {
                        "id": registered_user["telegram_id"],
                        "is_bot": False,
                        "first_name": registered_user["first_name"]
                    },
                    "chat": {
                        "id": registered_user["telegram_id"],
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": query
                }
            }
            
            response = requests.post(
                f"{production_url}/webhook/telegram",
                json=update,
                timeout=30
            )
            
            # Should process iFood queries
            assert response.status_code == 200, f"iFood query '{query}' should be processed"
            
            time.sleep(1)


@pytest.mark.e2e
class TestHITLSupervisionWorkflow:
    """E2E tests for H.I.T.L. supervision workflow"""

    @pytest.fixture
    def production_url(self):
        """Production API URL"""
        return "https://ain6spik95.execute-api.us-east-1.amazonaws.com/prod"

    @pytest.fixture
    def supervisor_user(self):
        """Supervisor test user"""
        return {
            "telegram_id": 987654321,
            "email": "supervisor@example.com",
            "first_name": "Supervisor"
        }

    def test_escalation_trigger(self, production_url, supervisor_user):
        """Test escalation trigger for high-risk decisions"""
        
        # High-risk action that should trigger escalation
        high_risk_update = {
            "update_id": int(time.time()),
            "message": {
                "message_id": 1,
                "from": {
                    "id": supervisor_user["telegram_id"],
                    "is_bot": False,
                    "first_name": supervisor_user["first_name"]
                },
                "chat": {
                    "id": supervisor_user["telegram_id"],
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "Cancele o pedido de R$ 2.000"
            }
        }
        
        response = requests.post(
            f"{production_url}/webhook/telegram",
            json=high_risk_update,
            timeout=30
        )
        
        # Should process and potentially escalate
        assert response.status_code == 200, "High-risk action should be processed (may escalate)"

    def test_supervisor_commands(self, production_url, supervisor_user):
        """Test supervisor approval/rejection commands"""
        
        # Test approval command
        approval_update = {
            "update_id": int(time.time()),
            "message": {
                "message_id": 1,
                "from": {
                    "id": supervisor_user["telegram_id"],
                    "is_bot": False,
                    "first_name": supervisor_user["first_name"]
                },
                "chat": {
                    "id": supervisor_user["telegram_id"],
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "/approve esc_test123"
            }
        }
        
        response = requests.post(
            f"{production_url}/webhook/telegram",
            json=approval_update,
            timeout=30
        )
        
        # Should process supervisor command
        assert response.status_code == 200, "Supervisor approval command should be processed"
        
        time.sleep(1)
        
        # Test rejection command
        rejection_update = {
            "update_id": int(time.time()) + 1,
            "message": {
                "message_id": 2,
                "from": {
                    "id": supervisor_user["telegram_id"],
                    "is_bot": False,
                    "first_name": supervisor_user["first_name"]
                },
                "chat": {
                    "id": supervisor_user["telegram_id"],
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "/reject esc_test456 Risco muito alto"
            }
        }
        
        response = requests.post(
            f"{production_url}/webhook/telegram",
            json=rejection_update,
            timeout=30
        )
        
        # Should process supervisor command
        assert response.status_code == 200, "Supervisor rejection command should be processed"


@pytest.mark.e2e
class TestBillingWorkflow:
    """E2E tests for billing and upgrade workflow"""

    @pytest.fixture
    def production_url(self):
        """Production API URL"""
        return "https://ain6spik95.execute-api.us-east-1.amazonaws.com/prod"

    @pytest.fixture
    def billing_user(self):
        """User for billing tests"""
        return {
            "telegram_id": 555666777,
            "email": "billing.test@example.com",
            "first_name": "Billing User"
        }

    def test_usage_tracking(self, production_url, billing_user):
        """Test usage tracking and limits"""
        
        # Query usage status
        usage_update = {
            "update_id": int(time.time()),
            "message": {
                "message_id": 1,
                "from": {
                    "id": billing_user["telegram_id"],
                    "is_bot": False,
                    "first_name": billing_user["first_name"]
                },
                "chat": {
                    "id": billing_user["telegram_id"],
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "Quantas mensagens usei este mês?"
            }
        }
        
        response = requests.post(
            f"{production_url}/webhook/telegram",
            json=usage_update,
            timeout=30
        )
        
        # Should process usage query
        assert response.status_code == 200, "Usage query should be processed"

    def test_upgrade_information(self, production_url, billing_user):
        """Test upgrade information queries"""
        
        # Query upgrade options
        upgrade_update = {
            "update_id": int(time.time()),
            "message": {
                "message_id": 1,
                "from": {
                    "id": billing_user["telegram_id"],
                    "is_bot": False,
                    "first_name": billing_user["first_name"]
                },
                "chat": {
                    "id": billing_user["telegram_id"],
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "Como fazer upgrade?"
            }
        }
        
        response = requests.post(
            f"{production_url}/webhook/telegram",
            json=upgrade_update,
            timeout=30
        )
        
        # Should process upgrade query
        assert response.status_code == 200, "Upgrade query should be processed"

    def test_tier_validation(self, production_url, billing_user):
        """Test tier validation and limits"""
        
        # Multiple messages to test limits (should be handled gracefully)
        for i in range(5):
            message_update = {
                "update_id": int(time.time()) + i,
                "message": {
                    "message_id": i + 1,
                    "from": {
                        "id": billing_user["telegram_id"],
                        "is_bot": False,
                        "first_name": billing_user["first_name"]
                    },
                    "chat": {
                        "id": billing_user["telegram_id"],
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": f"Test message {i + 1}"
                }
            }
            
            response = requests.post(
                f"{production_url}/webhook/telegram",
                json=message_update,
                timeout=30
            )
            
            # Should process or handle limits gracefully
            assert response.status_code == 200, f"Message {i + 1} should be processed or limited gracefully"
            
            time.sleep(0.5)


@pytest.mark.e2e
class TestSystemReliability:
    """E2E tests for system reliability and resilience"""

    @pytest.fixture
    def production_url(self):
        """Production API URL"""
        return "https://ain6spik95.execute-api.us-east-1.amazonaws.com/prod"

    def test_system_availability(self, production_url):
        """Test system availability over time"""
        
        # Test availability over 30 seconds with requests every 5 seconds
        start_time = time.time()
        successful_requests = 0
        total_requests = 0
        
        while time.time() - start_time < 30:
            try:
                response = requests.get(f"{production_url}/health", timeout=10)
                total_requests += 1
                
                if response.status_code == 200:
                    successful_requests += 1
                    
            except Exception as e:
                total_requests += 1
                print(f"Request failed: {e}")
            
            time.sleep(5)
        
        # Calculate availability
        availability = (successful_requests / total_requests) * 100 if total_requests > 0 else 0
        
        # Should have high availability (>95%)
        assert availability >= 95.0, f"System availability should be >95%, got {availability:.1f}%"
        assert total_requests >= 5, f"Should have made at least 5 requests, made {total_requests}"

    def test_response_time_consistency(self, production_url):
        """Test response time consistency"""
        
        response_times = []
        
        # Make 10 requests and measure response times
        for i in range(10):
            start_time = time.time()
            
            try:
                response = requests.get(f"{production_url}/health", timeout=10)
                end_time = time.time()
                
                if response.status_code == 200:
                    response_times.append(end_time - start_time)
                    
            except Exception as e:
                print(f"Request {i + 1} failed: {e}")
            
            time.sleep(1)
        
        # Analyze response times
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            # Response time assertions
            assert avg_time < 3.0, f"Average response time should be <3s, got {avg_time:.2f}s"
            assert max_time < 10.0, f"Max response time should be <10s, got {max_time:.2f}s"
            assert len(response_times) >= 8, f"Should have at least 8 successful requests, got {len(response_times)}"

    def test_concurrent_user_simulation(self, production_url):
        """Test system under concurrent user load"""
        
        import threading
        import queue
        
        results = queue.Queue()
        
        def simulate_user(user_id):
            """Simulate a user session"""
            try:
                # User registration
                registration_update = {
                    "update_id": int(time.time()) + user_id,
                    "message": {
                        "message_id": 1,
                        "from": {
                            "id": 100000 + user_id,
                            "is_bot": False,
                            "first_name": f"User{user_id}"
                        },
                        "chat": {
                            "id": 100000 + user_id,
                            "type": "private"
                        },
                        "date": int(time.time()),
                        "text": f"test.user.{user_id}@example.com"
                    }
                }
                
                response = requests.post(
                    f"{production_url}/webhook/telegram",
                    json=registration_update,
                    timeout=30
                )
                
                success = response.status_code == 200
                results.put({"user_id": user_id, "success": success, "status_code": response.status_code})
                
            except Exception as e:
                results.put({"user_id": user_id, "success": False, "error": str(e)})
        
        # Simulate 5 concurrent users
        threads = []
        for user_id in range(5):
            thread = threading.Thread(target=simulate_user, args=(user_id,))
            threads.append(thread)
        
        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Collect results
        all_results = []
        while not results.empty():
            all_results.append(results.get())
        
        # Validate concurrent performance
        successful_users = [r for r in all_results if r["success"]]
        
        assert len(all_results) == 5, "Should have results for all 5 users"
        assert len(successful_users) >= 4, f"At least 4/5 users should succeed, got {len(successful_users)}"
        assert total_time < 60.0, f"5 concurrent users should complete in <60s, took {total_time:.2f}s"