"""FastAPI application for AgentFirst2 MVP

This module provides the FastAPI application with:
- CORS middleware for cross-origin requests
- Request/response logging middleware
- X-Ray tracing for distributed tracing
- Error handling and validation
- Webhook endpoints for Telegram and iFood
"""

import logging
import json
import time
from typing import Callable
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

from app.config.settings import settings
from app.core.request_validator import RequestValidator
from app.omnichannel.telegram_service import TelegramService
from app.core.auditor import Auditor, AuditCategory, AuditLevel
from app.core.supervisor import Supervisor

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Patch AWS SDK for X-Ray tracing
if settings.XRAY_ENABLED:
    patch_all()

# Create FastAPI app
app = FastAPI(
    title="AgentFirst2 MVP API",
    version="1.0.0",
    description="""
**AgentFirst2** é uma plataforma de IA omnichannel para restaurantes que permite gerenciar operações de negócio através de linguagem natural.

## Principais Funcionalidades
- 🍔 **Gestão de Pedidos**: Integração completa com iFood (105+ critérios de homologação)
- 🧠 **Linguagem Natural**: Processamento via Claude 3.5 Sonnet
- 📱 **Omnichannel**: Telegram, WhatsApp, Web, App (contexto unificado por email)
- 👤 **H.I.T.L.**: Supervisão humana para decisões críticas
- 💰 **Freemium**: Free (100 msg/mês), Pro (10k msg/mês), Enterprise (ilimitado)
- 🔒 **Enterprise-Grade**: Encryption, PITR, GSI, DLQ, X-Ray, CloudWatch

## Documentação
- **OpenAPI Spec**: `/docs/openapi.yaml`
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **Exemplos**: `/docs/examples`
""",
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "AgentFirst2 Support",
        "email": "support@agentfirst.com",
        "url": "https://agentfirst.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# Custom middleware for request/response logging
@app.middleware("http")
async def logging_middleware(request: Request, call_next: Callable):
    """
    Middleware for structured request/response logging

    Args:
        request: HTTP request
        call_next: Next middleware/handler

    Returns:
        HTTP response
    """
    start_time = time.time()
    request_id = request.headers.get("X-Request-ID", "unknown")

    # Log request
    logger.info(json.dumps({
        "timestamp": time.time(),
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client": request.client.host if request.client else "unknown"
    }))

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log response
        logger.info(json.dumps({
            "timestamp": time.time(),
            "request_id": request_id,
            "status_code": response.status_code,
            "process_time_ms": round(process_time * 1000, 2)
        }))

        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        return response

    except Exception as e:
        process_time = time.time() - start_time

        # Log error
        logger.error(json.dumps({
            "timestamp": time.time(),
            "request_id": request_id,
            "error": str(e),
            "process_time_ms": round(process_time * 1000, 2)
        }))

        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "request_id": request_id
            }
        )


# Health check endpoint
@app.get("/health")
@xray_recorder.capture("health_check")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.API_VERSION
    }


# Status endpoint
@app.get("/status")
@xray_recorder.capture("status")
async def status():
    """Status endpoint"""
    return {
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "version": settings.API_VERSION,
        "debug": settings.DEBUG
    }


# Documentation examples endpoint
@app.get("/docs/examples")
@xray_recorder.capture("docs_examples")
async def docs_examples():
    """API usage examples and integration patterns"""
    return {
        "title": "AgentFirst2 API Examples",
        "description": "Exemplos práticos de integração com a API",
        "examples": {
            "health_check": {
                "description": "Verificar saúde da aplicação",
                "method": "GET",
                "url": "/health",
                "response": {
                    "status": "healthy",
                    "environment": "production",
                    "version": "1.0.0"
                }
            },
            "telegram_webhook": {
                "description": "Webhook do Telegram para processar mensagens",
                "method": "POST",
                "url": "/webhook/telegram",
                "request_body": {
                    "update_id": 123456789,
                    "message": {
                        "message_id": 1,
                        "from": {"id": 987654321, "first_name": "João"},
                        "chat": {"id": 987654321, "type": "private"},
                        "date": 1640995200,
                        "text": "Quantos pedidos tenho no iFood?"
                    }
                },
                "response": {"ok": True}
            },
            "ifood_webhook": {
                "description": "Webhook do iFood para receber eventos",
                "method": "POST",
                "url": "/webhook/ifood",
                "headers": {
                    "X-Signature": "sha256=<hmac_signature>"
                },
                "request_body": {
                    "eventId": "evt_123456789",
                    "eventType": "order.placed",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "merchantId": "merchant_123",
                    "data": {
                        "orderId": "order_456",
                        "totalAmount": 45.50,
                        "items": [
                            {"name": "Hambúrguer", "quantity": 1, "price": 25.00}
                        ]
                    }
                },
                "response": {"ok": True}
            },
            "supervisor_commands": {
                "description": "Comandos H.I.T.L. para supervisores",
                "examples": [
                    {
                        "command": "/approve esc_abc123",
                        "description": "Aprovar escalação"
                    },
                    {
                        "command": "/reject esc_abc123 Risco muito alto",
                        "description": "Rejeitar escalação com motivo"
                    }
                ]
            }
        },
        "integration_patterns": {
            "health_monitoring": {
                "description": "Monitoramento periódico de saúde",
                "code": "requests.get('/health')"
            },
            "webhook_retry": {
                "description": "Webhook com retry automático",
                "code": "@retry(stop=stop_after_attempt(3))"
            },
            "hmac_validation": {
                "description": "Validação de assinatura HMAC",
                "code": "hmac.compare_digest(expected, received)"
            }
        },
        "resources": {
            "openapi_spec": "/docs/openapi.yaml",
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "python_examples": "app/docs/api_examples.py"
        }
    }


# Telegram webhook endpoint
@app.post("/webhook/telegram")
@xray_recorder.capture("telegram_webhook")
async def telegram_webhook(request: Request):
    """
    Telegram webhook endpoint

    Receives updates from Telegram Bot API and processes them.

    Args:
        request: HTTP request

    Returns:
        JSON response with status
    """
    try:
        # Get request body
        body = await request.body()
        body_str = body.decode("utf-8")

        # Validate JSON
        data = RequestValidator.validate_json_body(body_str)

        logger.info(f"Received Telegram webhook: {json.dumps(data)}")

        # Extract message from update
        if "message" not in data:
            logger.warning("No message in Telegram update")
            return {"ok": True}

        message = data["message"]
        chat_id = message.get("chat", {}).get("id")
        user_id = message.get("from", {}).get("id")
        text = message.get("text", "")

        if not chat_id or not text:
            logger.warning("Missing chat_id or text in message")
            return {"ok": True}

        logger.info(f"Processing message from user {user_id}: {text}")

        # Initialize services
        telegram = TelegramService()
        
        # Send typing indicator
        await telegram.send_typing_indicator(chat_id)

        try:
            # Initialize omnichannel interface (centralized orchestrator)
            from app.omnichannel.interface import OmnichannelInterface
            from app.omnichannel.database.repositories import UserRepository
            from app.omnichannel.database.models import User, UserTier
            from app.omnichannel.models import ChannelType
            from app.core.brain import Brain
            from app.core.auditor import Auditor
            from app.core.supervisor import Supervisor
            from app.core.event_bus import EventBus
            from app.domains.retail.retail_agent import RetailAgent
            from app.domains.retail.ifood_connector_extended import iFoodConnectorExtended
            from app.config.secrets_manager import SecretsManager
            
            user_repo = UserRepository()
            
            # Check if message is email for registration
            if "@" in text and "." in text and len(text.split()) == 1:
                # User is sending email for registration
                email = text.strip().lower()
                
                # Validate email
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if re.match(email_pattern, email):
                    # Check if email already exists
                    existing_user = await user_repo.get_by_email(email)
                    
                    if existing_user:
                        # User exists, link Telegram ID
                        if not existing_user.telegram_id:
                            await user_repo.update(email, {"telegram_id": user_id})
                            response_text = (
                                f"✅ Perfeito! Vinculei seu Telegram ao email: {email}\n\n"
                                "🍔 Agora você pode usar o AgentFirst!\n\n"
                                "Experimente:\n"
                                "• 'Quantos pedidos tenho?'\n"
                                "• 'Qual meu faturamento hoje?'"
                            )
                        else:
                            response_text = (
                                f"✅ Email {email} já está cadastrado!\n\n"
                                "🍔 Você já pode usar o AgentFirst!"
                            )
                    else:
                        # Create new user
                        new_user = User(
                            email=email,
                            telegram_id=user_id,
                            tier=UserTier.FREE
                        )
                        await user_repo.create(new_user)
                        
                        response_text = (
                            f"🎉 Cadastro realizado com sucesso!\n\n"
                            f"📧 Email: {email}\n"
                            f"🎯 Tier: Gratuito (100 mensagens/mês)\n\n"
                            "🍔 Agora você pode gerenciar seus pedidos do iFood!\n\n"
                            "Experimente:\n"
                            "• 'Quantos pedidos tenho?'\n"
                            "• 'Qual meu faturamento hoje?'\n"
                            "• 'Feche a loja por 30 minutos'"
                        )
                else:
                    response_text = (
                        "❌ Email inválido!\n\n"
                        "📧 Por favor, envie um email válido no formato:\n"
                        "exemplo@dominio.com"
                    )
            else:
                # Check if user is already registered
                existing_user = await user_repo.get_by_telegram_id(user_id)
                
                if not existing_user:
                    # User not registered
                    if text.lower() in ["oi", "olá", "hello", "hi", "começar", "start"]:
                        response_text = (
                            "👋 Olá! Bem-vindo ao AgentFirst!\n\n"
                            "🍔 Sou seu assistente para gerenciar pedidos do iFood.\n\n"
                            "Para começar, preciso do seu email para identificá-lo em todos os canais.\n\n"
                            "📧 Por favor, envie seu email:"
                        )
                    else:
                        response_text = (
                            "🔐 Para usar o AgentFirst, preciso do seu email primeiro.\n\n"
                            "📧 Por favor, envie seu email:"
                        )
                else:
                    # User registered - check if it's a supervisor command first
                    if text.startswith('/approve ') or text.startswith('/reject '):
                        # Handle supervisor commands directly (bypass omnichannel for H.I.T.L.)
                        auditor = Auditor()
                        supervisor = Supervisor(auditor=auditor, telegram_service=telegram)
                        brain = Brain(auditor=auditor, supervisor=supervisor)
                        
                        # Configure supervisor
                        brain.configure_supervisor(
                            supervisor_id="default",
                            name="Supervisor Padrão",
                            telegram_chat_id=str(chat_id),
                            specialties=["retail", "general"],
                            priority_threshold=1
                        )
                        
                        parts = text.split(' ', 2)
                        command = parts[0][1:]  # Remove '/'
                        escalation_id = parts[1] if len(parts) > 1 else None
                        feedback = parts[2] if len(parts) > 2 else None
                        
                        if escalation_id:
                            success = await brain.process_human_decision(
                                escalation_id=escalation_id,
                                decision=command,
                                feedback=feedback,
                                supervisor_id="default"
                            )
                            
                            if success:
                                response_text = (
                                    f"✅ <b>Decisão processada!</b>\n\n"
                                    f"📋 Escalação: {escalation_id}\n"
                                    f"🎯 Decisão: {command.upper()}\n"
                                    f"📝 Feedback: {feedback or 'Nenhum'}"
                                )
                            else:
                                response_text = (
                                    f"❌ <b>Erro ao processar decisão</b>\n\n"
                                    f"📋 Escalação: {escalation_id}\n"
                                    f"Verifique se o ID está correto e se a escalação ainda está pendente."
                                )
                        else:
                            response_text = (
                                "❌ <b>Formato inválido</b>\n\n"
                                "Use:\n"
                                "• <code>/approve [escalation_id]</code>\n"
                                "• <code>/reject [escalation_id] [motivo]</code>"
                            )
                    else:
                        # Process normal message via OmnichannelInterface
                        # Initialize all services
                        auditor = Auditor()
                        supervisor = Supervisor(auditor=auditor, telegram_service=telegram)
                        event_bus = EventBus()
                        brain = Brain(auditor=auditor, supervisor=supervisor)
                        
                        # Initialize and register retail agent
                        retail_agent = RetailAgent(auditor=auditor)
                        secrets_manager = SecretsManager()
                        ifood_connector = iFoodConnectorExtended(secrets_manager)
                        retail_agent.register_connector('ifood', ifood_connector)
                        brain.register_agent('retail', retail_agent)
                        
                        # Configure supervisor
                        brain.configure_supervisor(
                            supervisor_id="default",
                            name="Supervisor Padrão",
                            telegram_chat_id=str(chat_id),
                            specialties=["retail", "general"],
                            priority_threshold=1
                        )
                        
                        # Initialize omnichannel interface
                        omnichannel = OmnichannelInterface(
                            brain=brain,
                            auditor=auditor,
                            supervisor=supervisor,
                            event_bus=event_bus,
                            telegram_service=telegram
                        )
                        
                        # Register user channel mapping
                        await omnichannel.register_user_channel(
                            email=existing_user.email,
                            channel=ChannelType.TELEGRAM,
                            channel_user_id=str(user_id),
                            metadata={"chat_id": str(chat_id)}
                        )
                        
                        # Process message via omnichannel interface
                        result = await omnichannel.process_message(
                            channel=ChannelType.TELEGRAM,
                            channel_user_id=str(user_id),
                            message_text=text,
                            message_id=str(message.get("message_id", "unknown")),
                            metadata={"chat_id": str(chat_id)}
                        )
                        
                        if result["success"]:
                            response_text = result["response"]
                            logger.info(f"Omnichannel processed message successfully in {result.get('processing_time_seconds', 0):.2f}s")
                        else:
                            response_text = result["response"]
                            logger.warning(f"Omnichannel processing failed: {result.get('reason', 'unknown')}")
        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            response_text = (
                "❌ Ops! Algo deu errado.\n\n"
                "🔧 Tente novamente em alguns segundos."
            )
        
        logger.info(f"Sending response to chat {chat_id}")

        # Send response
        result = await telegram.send_message(
            chat_id=chat_id,
            text=response_text,
            parse_mode="HTML",
            reply_to_message_id=message.get("message_id"),
        )

        if result.get("ok"):
            logger.info(f"Response sent successfully to chat {chat_id}")
        else:
            logger.error(f"Failed to send response to chat {chat_id}: {result.get('error')}")

        return {"ok": True}

    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid request"}
        )


# iFood webhook endpoint
@app.post("/webhook/ifood")
@xray_recorder.capture("ifood_webhook")
async def ifood_webhook(request: Request):
    """
    iFood webhook endpoint

    Receives events from iFood API and processes them.

    Args:
        request: HTTP request

    Returns:
        JSON response with status
    """
    try:
        # Get request body
        body = await request.body()
        body_str = body.decode("utf-8")

        # Get signature from headers
        signature = request.headers.get("X-Signature", "")

        # TODO: Validate HMAC signature
        # secret = await get_ifood_secret()
        # if not RequestValidator.validate_hmac_signature(body_str, signature, secret):
        #     return JSONResponse(status_code=401, content={"error": "Invalid signature"})

        # Validate JSON
        data = RequestValidator.validate_json_body(body_str)

        logger.info(f"Received iFood webhook: {json.dumps(data)}")

        # TODO: Process iFood event
        # - Extract event type (order, status, etc)
        # - Route to Retail Agent
        # - Acknowledge event
        # - Publish to Event Bus

        return {"ok": True}

    except Exception as e:
        logger.error(f"Error processing iFood webhook: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid request"}
        )


# Error handler for validation errors
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions"""
    logger.error(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "message": str(exc)
        }
    )


# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level=settings.LOG_LEVEL.lower()
    )
