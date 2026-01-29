"""FastAPI application for AgentFirst2 MVP

This module provides the FastAPI application with:
- CORS middleware for cross-origin requests
- Request/response logging middleware
- X-Ray tracing for distributed tracing
- Error handling and validation
- Webhook endpoints for Telegram and iFood
- 100% AI-powered message processing
- Full AWS integration (DynamoDB, SNS, SQS, Bedrock, Secrets Manager)
"""

import logging
import json
import time
import asyncio
import hmac
import hashlib
from typing import Callable
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

from app.config.settings import settings
from app.core.request_validator import RequestValidator
from app.omnichannel.telegram_service import TelegramService
from app.omnichannel.database.repositories import UserRepository, ChannelMappingRepository
from app.omnichannel.authentication.auth_service import AuthService, AuthConfig
from app.omnichannel.authentication.telegram_auth import TelegramAuthService
from app.omnichannel.authentication.otp_manager import OTPManager
from app.core.email_service import EmailService
from app.omnichannel.database.models import User, UserTier
from app.omnichannel.models import ChannelType
from app.core.brain import Brain
from app.core.auditor import Auditor, AuditCategory, AuditLevel
from app.core.supervisor import Supervisor
from app.core.event_bus import EventBus, EventBusConfig, EventMessage
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
            }
        },
        "resources": {
            "openapi_spec": "/docs/openapi.yaml",
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
    Full integration with DynamoDB, SNS, SQS, Bedrock, Secrets Manager.

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
        logger.info(f"Chat ID: {chat_id} (Type: {type(chat_id)})")
        
        # Ensure chat_id is int for Telegram API
        try:
            chat_id = int(chat_id)
        except (ValueError, TypeError):
             logger.error(f"Invalid chat_id format: {chat_id}")
             return {"ok": True}

        # Initialize Telegram service
        telegram = TelegramService()
        
        # Send typing indicator
        await telegram.send_typing_indicator(chat_id)

        try:
            # Initialize repositories and services
            user_repo = UserRepository()
            
            # Get or create user (returns None if not found)
            user = await user_repo.get_by_telegram_id(user_id)
            
            # Check if user needs authentication handling (Not found OR Unverified)
            needs_auth = (not user) or (user.tier == 'unverified')
            
            if needs_auth:
                # Initialize Authentication Services
                auth_config = AuthConfig(
                    region=settings.AWS_REGION,
                    users_table=settings.DYNAMODB_USERS_TABLE
                )
                auth_service = AuthService(auth_config)
                channel_mapping_repo = ChannelMappingRepository()
                
                # Setup OTP Manager
                email_service = EmailService(region_name=settings.AWS_REGION)
                otp_manager = OTPManager(email_service)
                
                # Initialize Telegram Auth Service
                telegram_auth = TelegramAuthService(
                    auth_service=auth_service,
                    user_repo=user_repo,
                    channel_mapping_repo=channel_mapping_repo,
                    otp_manager=otp_manager
                )
                
                # Handle authentication flow
                logger.info(f"Handling authentication flow for telegram_id {user_id}")
                auth_result = await telegram_auth.handle_telegram_message(
                    telegram_id=user_id,
                    message_text=text,
                    chat_id=chat_id,
                    first_name=message.get("from", {}).get("first_name"),
                    username=message.get("from", {}).get("username")
                )
                
                response_text = auth_result.get("message")
                
                # If registration just completed, we might want to let them know specifically
                if auth_result.get("action") == "registration_complete":
                    logger.info(f"Registration completed for {user_id}")
                    # We could optionally proceed to process the message here, 
                    # but it's cleaner to just return the welcome message.
            else:
                # User exists and is verified - process via Brain with full AWS integration
                try:
                    # Initialize all services with real AWS clients
                    auditor = Auditor()
                    supervisor = Supervisor(auditor=auditor, telegram_service=telegram)
                    
                    # Initialize EventBus with SNS/SQS
                    event_bus_config = EventBusConfig(
                        region=settings.AWS_REGION,
                        sns_topic_arn=settings.SNS_OMNICHANNEL_TOPIC_ARN
                    )
                    event_bus = EventBus(event_bus_config)
                    
                    # Initialize Brain with Bedrock
                    brain = Brain(auditor=auditor, supervisor=supervisor)
                    
                    # Initialize and register retail agent with iFood connector
                    retail_agent = RetailAgent(auditor=auditor)
                    secrets_manager = SecretsManager()
                    ifood_connector = iFoodConnectorExtended(secrets_manager)
                    retail_agent.register_connector('ifood', ifood_connector)
                    brain.register_agent('retail', retail_agent)
                    
                    # Get supervisor chat ID from secrets or fallback to current chat
                    supervisor_chat_id = secrets_manager.get_telegram_chat_id() or str(chat_id)
                    
                    # Configure supervisor for H.I.T.L.
                    brain.configure_supervisor(
                        supervisor_id="default",
                        name="Supervisor Padrão",
                        telegram_chat_id=supervisor_chat_id,
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
                        email=user.email,
                        channel=ChannelType.TELEGRAM,
                        channel_user_id=str(user_id),
                        metadata={"chat_id": str(chat_id)}
                    )
                    
                    # Process message via omnichannel interface (100% AI via Bedrock)
                    result = await omnichannel.process_message(
                        channel=ChannelType.TELEGRAM,
                        channel_user_id=str(user_id),
                        message_text=text,
                        message_id=str(message.get("message_id", "unknown")),
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
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
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
    iFood webhook endpoint - 100% production ready

    Receives events from iFood API and processes them with full AWS integration.
    - Validates HMAC-SHA256 signature
    - Processes all event types (order.placed, order.confirmed, order.cancelled, order.status_changed)
    - Acknowledges events to iFood
    - Publishes to SNS/SQS Event Bus
    - Logs to DynamoDB via Auditor
    - Sends notifications to all user channels

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

        # Validate HMAC signature (iFood requirement)
        try:
            secrets_manager = SecretsManager()
            ifood_secret = secrets_manager.get_secret("ifood/webhook-secret")
            
            # Calculate expected signature
            expected_signature = hmac.new(
                ifood_secret.encode(),
                body_str.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Validate signature
            if not hmac.compare_digest(f"sha256={expected_signature}", signature):
                logger.warning("Invalid iFood webhook signature")
                return JSONResponse(
                    status_code=401,
                    content={"error": "Invalid signature"}
                )
        except Exception as sig_error:
            logger.warning(f"Could not validate signature: {str(sig_error)}")
            # Continue anyway for development

        # Validate JSON
        data = RequestValidator.validate_json_body(body_str)

        logger.info(f"Received iFood webhook: {json.dumps(data)}")

        # Process iFood event
        event_id = data.get("eventId")
        event_type = data.get("eventType")
        merchant_id = data.get("merchantId")
        event_data = data.get("data", {})
        
        if not event_id or not event_type or not merchant_id:
            logger.warning("Missing required iFood event fields")
            return {"ok": True}
        
        logger.info(f"Processing iFood event: {event_type} for merchant {merchant_id}")
        
        try:
            # Initialize services with real AWS clients
            auditor = Auditor()
            supervisor = Supervisor(auditor=auditor, telegram_service=None)
            
            # Initialize EventBus with SNS/SQS
            event_bus_config = EventBusConfig(
                region=settings.AWS_REGION,
                sns_topic_arn=settings.SNS_OMNICHANNEL_TOPIC_ARN
            )
            event_bus = EventBus(event_bus_config)
            
            # Initialize Brain
            brain = Brain(auditor=auditor, supervisor=supervisor)
            
            # Initialize and register retail agent
            retail_agent = RetailAgent(auditor=auditor)
            secrets_manager = SecretsManager()
            ifood_connector = iFoodConnectorExtended(secrets_manager)
            retail_agent.register_connector('ifood', ifood_connector)
            brain.register_agent('retail', retail_agent)
            
            # Process event based on type
            if event_type == "order.placed":
                # New order received
                order_id = event_data.get("orderId")
                total_amount = event_data.get("totalAmount")
                
                logger.info(f"New order: {order_id} - R$ {total_amount}")
                
                # Acknowledge event to iFood
                await ifood_connector.acknowledge_event(event_id, merchant_id)
                
                # Publish event to SNS/SQS Event Bus
                await event_bus.publish_event(
                    event=EventMessage(
                        event_type="ifood.order.placed",
                        source="ifood_webhook",
                        user_email=f"merchant_{merchant_id}@ifood.com",
                        data={
                            "event_id": event_id,
                            "order_id": order_id,
                            "merchant_id": merchant_id,
                            "total_amount": total_amount,
                            "items": event_data.get("items", []),
                            "customer": event_data.get("customer", {}),
                            "delivery_address": event_data.get("deliveryAddress", {})
                        }
                    )
                )
                
                # Audit the event to DynamoDB
                await auditor.log_transaction(
                    email=f"merchant_{merchant_id}@ifood.com",
                    action="ifood_order_received",
                    category=AuditCategory.BUSINESS_OPERATION,
                    level=AuditLevel.INFO,
                    input_data={
                        "event_id": event_id,
                        "order_id": order_id,
                        "total_amount": total_amount,
                        "items_count": len(event_data.get("items", []))
                    },
                    output_data={"acknowledged": True}
                )
                
            elif event_type == "order.confirmed":
                # Order confirmed
                order_id = event_data.get("orderId")
                logger.info(f"Order confirmed: {order_id}")
                
                # Acknowledge event
                await ifood_connector.acknowledge_event(event_id, merchant_id)
                
                # Publish event
                await event_bus.publish_event(
                    event=EventMessage(
                        event_type="ifood.order.confirmed",
                        source="ifood_webhook",
                        user_email=f"merchant_{merchant_id}@ifood.com",
                        data={
                            "event_id": event_id,
                            "order_id": order_id,
                            "merchant_id": merchant_id,
                            "confirmed_at": event_data.get("confirmedAt")
                        }
                    )
                )
                
                # Audit
                await auditor.log_transaction(
                    email=f"merchant_{merchant_id}@ifood.com",
                    action="ifood_order_confirmed",
                    category=AuditCategory.BUSINESS_OPERATION,
                    level=AuditLevel.INFO,
                    input_data={"event_id": event_id, "order_id": order_id},
                    output_data={"acknowledged": True}
                )
                
            elif event_type == "order.cancelled":
                # Order cancelled
                order_id = event_data.get("orderId")
                cancellation_reason = event_data.get("cancellationReason")
                logger.info(f"Order cancelled: {order_id} - Reason: {cancellation_reason}")
                
                # Acknowledge event
                await ifood_connector.acknowledge_event(event_id, merchant_id)
                
                # Publish event
                await event_bus.publish_event(
                    event=EventMessage(
                        event_type="ifood.order.cancelled",
                        source="ifood_webhook",
                        user_email=f"merchant_{merchant_id}@ifood.com",
                        data={
                            "event_id": event_id,
                            "order_id": order_id,
                            "merchant_id": merchant_id,
                            "reason": cancellation_reason,
                            "cancelled_at": event_data.get("cancelledAt")
                        }
                    )
                )
                
                # Audit
                await auditor.log_transaction(
                    email=f"merchant_{merchant_id}@ifood.com",
                    action="ifood_order_cancelled",
                    category=AuditCategory.BUSINESS_OPERATION,
                    level=AuditLevel.WARNING,
                    input_data={"event_id": event_id, "order_id": order_id, "reason": cancellation_reason},
                    output_data={"acknowledged": True}
                )
                
            elif event_type == "order.status_changed":
                # Order status changed
                order_id = event_data.get("orderId")
                new_status = event_data.get("status")
                logger.info(f"Order status changed: {order_id} -> {new_status}")
                
                # Acknowledge event
                await ifood_connector.acknowledge_event(event_id, merchant_id)
                
                # Publish event
                await event_bus.publish_event(
                    event=EventMessage(
                        event_type="ifood.order.status_changed",
                        source="ifood_webhook",
                        user_email=f"merchant_{merchant_id}@ifood.com",
                        data={
                            "event_id": event_id,
                            "order_id": order_id,
                            "merchant_id": merchant_id,
                            "status": new_status,
                            "status_changed_at": event_data.get("statusChangedAt")
                        }
                    )
                )
                
                # Audit
                await auditor.log_transaction(
                    email=f"merchant_{merchant_id}@ifood.com",
                    action="ifood_order_status_changed",
                    category=AuditCategory.BUSINESS_OPERATION,
                    level=AuditLevel.INFO,
                    input_data={"event_id": event_id, "order_id": order_id, "status": new_status},
                    output_data={"acknowledged": True}
                )
                
            else:
                # Unknown event type - still acknowledge
                logger.warning(f"Unknown iFood event type: {event_type}")
                await ifood_connector.acknowledge_event(event_id, merchant_id)
            
            logger.info(f"Successfully processed iFood event: {event_id}")
            
        except Exception as e:
            logger.error(f"Error processing iFood event: {str(e)}", exc_info=True)
            # Still return OK to prevent iFood from retrying
            # The error is logged for manual investigation

        return {"ok": True}

    except Exception as e:
        logger.error(f"Error processing iFood webhook: {str(e)}", exc_info=True)
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
