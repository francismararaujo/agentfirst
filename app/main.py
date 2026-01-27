"""FastAPI application for AgentFirst2 MVP

This module provides the FastAPI application with:
- CORS middleware for cross-origin requests
- Request/response logging middleware
- X-Ray tracing for distributed tracing
- Error handling and validation
- Webhook endpoints for Telegram and iFood
- 100% AI-powered message processing
"""

import logging
import json
import time
import asyncio
from typing import Callable
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

from app.config.settings import settings
from app.core.request_validator import RequestValidator
from app.omnichannel.telegram_service import TelegramService
from app.omnichannel.database.repositories import UserRepository
from app.omnichannel.database.models import User, UserTier
from app.omnichannel.models import ChannelType
from app.core.brain import Brain
from app.core.auditor import Auditor
from app.core.supervisor import Supervisor
 EventBusConfig
from app.domains.retail.retail_agent import RetailAgent
from app.domains.retail.ifood_connector_extended import iFoodConnectorExtended
from app.config.secrets_manager import SecretsManager
from app.omnichannel.interface import OmnichannelInterface

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
- 🧠 **Linguagem Natural**: Processamento 100% via Claude 3.5 Sonnet
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
e):
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
                "reque: {
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
            }
        },
        "resources": {
penapi_spec": "/docs/openapi.yaml",
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        }
    }


# Telegram webhook endpoint
@app.post("/webhook/telegram")
@xray_recorder.capture("telegram_webhook")
async def telegram_webhook(request: Request):
    """
    Telegram webhook endpoint - 100% AI-powered message processing

    Receives updates from Telegram Bot API and processes them via Brain.

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
        chat_id = message.get("id")
        user_id = message.get("from", {}).get("id")
        text = message.get("text", "")

        if not chat_id or not text:
            logger.warning("Missing chat_id or text in message")
            return {"ok": True}

        logger.info(f"Processing message from user {user_id}: {text}")

        # Initialize Telegram service
        telegram = TelegramService()
        
        # Send typing indicator
        await telegram.send_typing_indicator(chat_id)

        try:
            # Initiatories and services
            user_repo = UserRepository()
            
            # Get or create user
            user = await user_repo.get_by_telegram_id(user_id)
            
            if not user:
                # New user - ask for email
                response_text = (
                    "👋 Olá! Bem-vindo ao AgentFirst!\n\n"
                    "🍔 Sou seu assistente para gerenciar pedidos do iFood.\n\n"
                    "Para começar, preciso do seais.\n\n"
                    "📧 Por favor, envie seu email (ex: seu@email.com):"
                )
            else:
                # User exists - process via Brain
                try:
                    # Initialize all services
                    auditor = Auditor()
                    supervisor = Supervisor(auditor=auditor, telegram_service=telegram)
                    
                    # Initialize EventBus
                    event_bus_config = EventBusConfig(region=settings.AWS_REGION)
                    event_bus = EventBus(event_bus_config)
                    
                    # Initialize Brain
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
                    
                    #nitialize omnichannel interface
                    omnichannel = OmnichannelInterface(
                        brain=brain,
                        auditor=auditor,
                        supervisor=supervisor,
                        event_bus=event_bus,
                        telegram_service=telegram
                    )
                    
                    # Register user channel mapping
                    await omnichannel.register_user_channel(
                        email=user.email,
                        channel=ChannelType.TELEGRAM,
                        channel_user_id=str(user_id),
                        metadata={"chat_id": str(chat_id)}
                    )
                    
                    # Process message via omnichannel interface (100% AI)
                    result = await omnichannel.process_message(
                        channel=ChannelType.TELEGRAM,
                        channel_user_id=str(user_id),
                        message_text=text,
                     e_id=str(message.get("message_id", "unknown")),
                        metadata={"chat_id": str(chat_id)}
                    )
                    
                    if result["success"]:
                        response_text = result["response"]
                        logger.info(f"Brain processed message successfully in {result.get('processing_time_seconds', 0):.2f}s")
                    else:
                        response_text = result["response"]
                        logger.warning(f"Brain processing failed: {result.get('reason', 'unknown')}")
                        
                except Exception as brain_error:
                    logger.error(f"Error processing via Brain: {str(brain_error)}", exc_info=True)
                    response_text = (
                        "❌ Erro ao processar sua mensagem.\n\n"
                        "🔧 Tente novamente em alguns segundos."
                    )
        
        except Exception as e:
            logger.error(f"E", exc_info=True)
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
        logger.error(f"Error processing Telegram webhook: {str(e)}", exc_info=True)
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
uest, exc: ValueError):
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
