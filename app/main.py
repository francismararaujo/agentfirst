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
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

from app.config.settings import settings
from app.core.request_validator import RequestValidator
from app.omnichannel.telegram_service import TelegramService

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Patch AWS SDK for X-Ray tracing
if settings.XRAY_ENABLED:
    patch_all()

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    debug=settings.DEBUG
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

        # Initialize Telegram service
        telegram = TelegramService()

        # Send typing indicator
        await telegram.send_typing_indicator(chat_id)

        # TODO: Full implementation
        # 1. Authenticate user by Telegram ID → email
        # 2. Create/retrieve session
        # 3. Process message through Brain
        # 4. Send response back to Telegram

        # For now, send a simple acknowledgment
        if text.lower() in ["oi", "olá", "hello", "hi"]:
            response_text = (
                "👋 Olá! Eu sou o AgentFirst!\n\n"
                "🍔 Sou seu assistente para gerenciar pedidos do iFood.\n\n"
                "⚙️ Sistema em desenvolvimento...\n"
                "Em breve você poderá:\n"
                "• Verificar pedidos pendentes\n"
                "• Confirmar pedidos automaticamente\n"
                "• Ver faturamento em tempo real"
            )
        elif "@" in text and "." in text:
            # Usuário enviou um email
            response_text = (
                f"📧 Recebi seu email: {text}\n\n"
                "✅ Em breve implementaremos o cadastro completo!\n\n"
                "🔧 Por enquanto, continue testando o bot..."
            )
        else:
            response_text = f"✅ Recebi sua mensagem: <b>{text}</b>\n\n⚙️ Sistema em desenvolvimento..."
        
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
