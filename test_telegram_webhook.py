#!/usr/bin/env python3
"""
Script para testar o webhook do Telegram

Este script simula uma mensagem do Telegram para testar se o webhook está funcionando.
"""

import json
import requests

# URL do webhook (será atualizada após o deploy)
WEBHOOK_URL = "https://ain6spik95.execute-api.us-east-1.amazonaws.com/prod/webhook/telegram"

# Mensagem de teste simulando o formato do Telegram
test_message = {
    "update_id": 123456789,
    "message": {
        "message_id": 1,
        "from": {
            "id": 123456789,
            "is_bot": False,
            "first_name": "Test",
            "username": "testuser",
            "language_code": "pt-br"
        },
        "chat": {
            "id": 123456789,
            "first_name": "Test",
            "username": "testuser",
            "type": "private"
        },
        "date": 1640995200,
        "text": "Olá! Este é um teste do webhook."
    }
}

def test_webhook():
    """Testa o webhook do Telegram"""
    try:
        print(f"🧪 Testando webhook: {WEBHOOK_URL}")
        
        response = requests.post(
            WEBHOOK_URL,
            json=test_message,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📝 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook funcionando!")
        else:
            print("❌ Webhook com problema")
            
    except Exception as e:
        print(f"❌ Erro ao testar webhook: {str(e)}")

if __name__ == "__main__":
    test_webhook()