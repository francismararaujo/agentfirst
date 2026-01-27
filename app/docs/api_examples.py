#!/usr/bin/env python3
"""
AgentFirst2 MVP - API Usage Examples

Este arquivo contém exemplos práticos de como integrar com a API do AgentFirst2.
Inclui exemplos para webhooks, autenticação, e casos de uso comuns.

Usage:
    python app/docs/api_examples.py
"""

import requests
import json
import hmac
import hashlib
from datetime import datetime
from typing import Dict, Any


class AgentFirstAPI:
    """Cliente para API do AgentFirst2"""
    
    def __init__(self, base_url: str = "https://ain6spik95.execute-api.us-east-1.amazonaws.com/prod"):
        """
        Inicializa cliente da API
        
        Args:
            base_url: URL base da API
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AgentFirst2-Client/1.0.0'
        })
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica saúde da aplicação
        
        Returns:
            Status da aplicação
        """
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtém status detalhado da aplicação
        
        Returns:
            Status detalhado
        """
        response = self.session.get(f"{self.base_url}/status")
        response.raise_for_status()
        return response.json()
    
    def send_telegram_update(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simula envio de update do Telegram
        
        Args:
            update_data: Dados do update do Telegram
            
        Returns:
            Resposta do webhook
        """
        response = self.session.post(
            f"{self.base_url}/webhook/telegram",
            json=update_data
        )
        response.raise_for_status()
        return response.json()
    
    def send_ifood_event(self, event_data: Dict[str, Any], secret_key: str) -> Dict[str, Any]:
        """
        Envia evento do iFood com assinatura HMAC
        
        Args:
            event_data: Dados do evento
            secret_key: Chave secreta para HMAC
            
        Returns:
            Resposta do webhook
        """
        # Serializar dados
        payload = json.dumps(event_data, separators=(',', ':'))
        
        # Calcular assinatura HMAC-SHA256
        signature = hmac.new(
            secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Enviar com assinatura
        headers = {
            'X-Signature': f'sha256={signature}'
        }
        
        response = self.session.post(
            f"{self.base_url}/webhook/ifood",
            data=payload,
            headers=headers
        )
        response.raise_for_status()
        return response.json()


def example_health_check():
    """Exemplo: Verificar saúde da aplicação"""
    print("=" * 60)
    print("EXEMPLO 1: HEALTH CHECK")
    print("=" * 60)
    
    api = AgentFirstAPI()
    
    try:
        # Health check
        health = api.health_check()
        print("✅ Health Check:")
        print(json.dumps(health, indent=2))
        print()
        
        # Status detalhado
        status = api.get_status()
        print("✅ Status Detalhado:")
        print(json.dumps(status, indent=2))
        print()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")


def example_telegram_webhook():
    """Exemplo: Webhook do Telegram"""
    print("=" * 60)
    print("EXEMPLO 2: TELEGRAM WEBHOOK")
    print("=" * 60)
    
    api = AgentFirstAPI()
    
    # Exemplo 1: Usuário novo enviando email para cadastro
    telegram_update_1 = {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {
                "id": 987654321,
                "is_bot": False,
                "first_name": "João",
                "username": "joao_restaurante"
            },
            "chat": {
                "id": 987654321,
                "first_name": "João",
                "type": "private"
            },
            "date": int(datetime.now().timestamp()),
            "text": "joao@pizzariaboa.com"
        }
    }
    
    print("📱 Exemplo 1: Cadastro de usuário")
    print("Mensagem:", telegram_update_1["message"]["text"])
    
    try:
        response = api.send_telegram_update(telegram_update_1)
        print("✅ Resposta:", json.dumps(response, indent=2))
        print()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro: {e}")
        print()
    
    # Exemplo 2: Usuário cadastrado fazendo pergunta
    telegram_update_2 = {
        "update_id": 123456790,
        "message": {
            "message_id": 2,
            "from": {
                "id": 987654321,
                "is_bot": False,
                "first_name": "João",
                "username": "joao_restaurante"
            },
            "chat": {
                "id": 987654321,
                "first_name": "João",
                "type": "private"
            },
            "date": int(datetime.now().timestamp()),
            "text": "Quantos pedidos tenho no iFood?"
        }
    }
    
    print("📱 Exemplo 2: Consulta de pedidos")
    print("Mensagem:", telegram_update_2["message"]["text"])
    
    try:
        response = api.send_telegram_update(telegram_update_2)
        print("✅ Resposta:", json.dumps(response, indent=2))
        print()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro: {e}")
        print()
    
    # Exemplo 3: Comando de supervisão (H.I.T.L.)
    telegram_update_3 = {
        "update_id": 123456791,
        "message": {
            "message_id": 3,
            "from": {
                "id": 987654321,
                "is_bot": False,
                "first_name": "João",
                "username": "joao_restaurante"
            },
            "chat": {
                "id": 987654321,
                "first_name": "João",
                "type": "private"
            },
            "date": int(datetime.now().timestamp()),
            "text": "/approve esc_abc123"
        }
    }
    
    print("📱 Exemplo 3: Comando de supervisão (H.I.T.L.)")
    print("Mensagem:", telegram_update_3["message"]["text"])
    
    try:
        response = api.send_telegram_update(telegram_update_3)
        print("✅ Resposta:", json.dumps(response, indent=2))
        print()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro: {e}")
        print()


def example_ifood_webhook():
    """Exemplo: Webhook do iFood"""
    print("=" * 60)
    print("EXEMPLO 3: IFOOD WEBHOOK")
    print("=" * 60)
    
    api = AgentFirstAPI()
    
    # Chave secreta (em produção, vem do AWS Secrets Manager)
    secret_key = "ifood_webhook_secret_key_example"
    
    # Exemplo 1: Novo pedido
    ifood_event_1 = {
        "eventId": "evt_123456789",
        "eventType": "order.placed",
        "timestamp": datetime.now().isoformat() + "Z",
        "merchantId": "merchant_123",
        "data": {
            "orderId": "order_456",
            "customerId": "customer_789",
            "totalAmount": 45.50,
            "items": [
                {
                    "name": "Hambúrguer Clássico",
                    "quantity": 1,
                    "price": 25.00,
                    "observations": "Sem cebola"
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
            ],
            "delivery": {
                "address": "Rua das Flores, 123",
                "estimatedTime": "30-40 min"
            },
            "payment": {
                "method": "credit_card",
                "brand": "visa",
                "lastFourDigits": "1234"
            }
        }
    }
    
    print("🍔 Exemplo 1: Novo pedido recebido")
    print("Evento:", ifood_event_1["eventType"])
    print("Pedido:", ifood_event_1["data"]["orderId"])
    print("Valor:", f"R$ {ifood_event_1['data']['totalAmount']:.2f}")
    
    try:
        response = api.send_ifood_event(ifood_event_1, secret_key)
        print("✅ Resposta:", json.dumps(response, indent=2))
        print()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro: {e}")
        print()
    
    # Exemplo 2: Pedido confirmado
    ifood_event_2 = {
        "eventId": "evt_123456790",
        "eventType": "order.confirmed",
        "timestamp": datetime.now().isoformat() + "Z",
        "merchantId": "merchant_123",
        "data": {
            "orderId": "order_456",
            "confirmedAt": datetime.now().isoformat() + "Z",
            "estimatedPreparationTime": 25
        }
    }
    
    print("🍔 Exemplo 2: Pedido confirmado")
    print("Evento:", ifood_event_2["eventType"])
    print("Pedido:", ifood_event_2["data"]["orderId"])
    
    try:
        response = api.send_ifood_event(ifood_event_2, secret_key)
        print("✅ Resposta:", json.dumps(response, indent=2))
        print()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro: {e}")
        print()


def example_integration_patterns():
    """Exemplos de padrões de integração"""
    print("=" * 60)
    print("EXEMPLO 4: PADRÕES DE INTEGRAÇÃO")
    print("=" * 60)
    
    print("🔧 Padrão 1: Monitoramento de Saúde")
    print("""
# Verificação periódica de saúde
import time
import requests

def monitor_health(api_url, interval=60):
    while True:
        try:
            response = requests.get(f"{api_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {datetime.now()}: {data['status']}")
            else:
                print(f"❌ {datetime.now()}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {datetime.now()}: {e}")
        
        time.sleep(interval)

# Uso
monitor_health("https://ain6spik95.execute-api.us-east-1.amazonaws.com/prod")
""")
    
    print("🔧 Padrão 2: Webhook com Retry")
    print("""
# Webhook com retry automático
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def send_webhook_with_retry(url, data, headers=None):
    response = requests.post(url, json=data, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

# Uso
try:
    result = send_webhook_with_retry(
        "https://ain6spik95.execute-api.us-east-1.amazonaws.com/prod/webhook/telegram",
        telegram_update_data
    )
    print("✅ Webhook enviado:", result)
except Exception as e:
    print("❌ Falha após 3 tentativas:", e)
""")
    
    print("🔧 Padrão 3: Validação de Assinatura HMAC")
    print("""
# Validação de webhook do iFood
import hmac
import hashlib

def validate_ifood_signature(payload, signature, secret_key):
    # Calcular assinatura esperada
    expected_signature = hmac.new(
        secret_key.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Extrair assinatura do header
    if signature.startswith('sha256='):
        received_signature = signature[7:]
    else:
        return False
    
    # Comparação segura
    return hmac.compare_digest(expected_signature, received_signature)

# Uso em Flask/FastAPI
@app.route('/webhook/ifood', methods=['POST'])
def ifood_webhook():
    signature = request.headers.get('X-Signature')
    payload = request.get_data(as_text=True)
    
    if not validate_ifood_signature(payload, signature, SECRET_KEY):
        return {'error': 'Invalid signature'}, 401
    
    # Processar evento...
    return {'ok': True}
""")


def example_error_handling():
    """Exemplos de tratamento de erros"""
    print("=" * 60)
    print("EXEMPLO 5: TRATAMENTO DE ERROS")
    print("=" * 60)
    
    api = AgentFirstAPI()
    
    print("❌ Exemplo 1: Endpoint inexistente")
    try:
        response = api.session.get(f"{api.base_url}/nonexistent")
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Status Code: {e.response.status_code}")
        if e.response.headers.get('content-type') == 'application/json':
            error_data = e.response.json()
            print(f"Error Details: {json.dumps(error_data, indent=2)}")
        print()
    
    print("❌ Exemplo 2: Dados inválidos no webhook")
    try:
        invalid_update = {
            "invalid_field": "invalid_data"
        }
        response = api.send_telegram_update(invalid_update)
    except requests.exceptions.HTTPError as e:
        print(f"Validation Error: {e}")
        print(f"Status Code: {e.response.status_code}")
        print()
    except Exception as e:
        print(f"Unexpected Error: {e}")
        print()
    
    print("❌ Exemplo 3: Timeout de conexão")
    try:
        # Simular timeout (URL inválida)
        api.base_url = "http://192.0.2.1:8000"  # TEST-NET-1 (não roteável)
        api.session.timeout = 5
        response = api.health_check()
    except requests.exceptions.Timeout as e:
        print(f"Timeout Error: {e}")
        print("Dica: Verifique conectividade de rede e status do serviço")
        print()
    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: {e}")
        print("Dica: Serviço pode estar indisponível")
        print()


def main():
    """Executa todos os exemplos"""
    print("🚀 AGENTFIRST2 MVP - EXEMPLOS DE USO DA API")
    print("=" * 60)
    print()
    
    # Executar exemplos
    example_health_check()
    example_telegram_webhook()
    example_ifood_webhook()
    example_integration_patterns()
    example_error_handling()
    
    print("=" * 60)
    print("✅ TODOS OS EXEMPLOS EXECUTADOS")
    print("=" * 60)
    print()
    print("📚 Recursos Adicionais:")
    print("• Documentação OpenAPI: /docs/openapi.yaml")
    print("• Swagger UI: https://ain6spik95.execute-api.us-east-1.amazonaws.com/prod/docs")
    print("• Health Check: https://ain6spik95.execute-api.us-east-1.amazonaws.com/prod/health")
    print("• Status: https://ain6spik95.execute-api.us-east-1.amazonaws.com/prod/status")
    print()
    print("🔗 Links Úteis:")
    print("• Telegram Bot API: https://core.telegram.org/bots/api")
    print("• iFood Developer: https://developer.ifood.com.br")
    print("• AWS Lambda: https://docs.aws.amazon.com/lambda/")
    print("• CloudWatch: https://docs.aws.amazon.com/cloudwatch/")


if __name__ == "__main__":
    main()