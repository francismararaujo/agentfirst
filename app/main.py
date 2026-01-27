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

        # Initialize services
        telegram = TelegramService()
        
        # Send typing indicator
        await telegram.send_typing_indicator(chat_id)

        try:
            # 1. AUTENTICAÇÃO COM COMPONENTES EXISTENTES
            from app.omnichannel.database.repositories import UserRepository
            from app.omnichannel.database.models import User, UserTier
            
            user_repo = UserRepository()
            
            # Verificar se usuário existe por Telegram ID
            # Primeiro, vamos buscar na tabela se já existe um usuário com este telegram_id
            # Como não temos método direto, vamos implementar a lógica de cadastro
            
            # Verificar se a mensagem é um email para cadastro
            if "@" in text and "." in text and len(text.split()) == 1:
                # Usuário está enviando email para cadastro
                email = text.strip().lower()
                
                # Validar email
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if re.match(email_pattern, email):
                    # Verificar se email já existe
                    existing_user = await user_repo.get_by_email(email)
                    
                    if existing_user:
                        # Usuário existe, vincular Telegram ID
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
                        # Criar novo usuário
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
                # Verificar se usuário já está cadastrado
                existing_user = await user_repo.get_by_telegram_id(user_id)
                
                if not existing_user:
                    # Usuário não cadastrado
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
                    # Usuário já cadastrado - processar comando
                    from app.core.brain import Brain, Context
                    from app.domains.retail.retail_agent import RetailAgent
                    from app.domains.retail.mock_ifood_connector import MockiFoodConnector
                    from app.omnichannel.models import ChannelType
                    
                    # Inicializar Brain e Retail Agent
                    brain = Brain()
                    retail_agent = RetailAgent()
                    
                    # Registrar mock iFood connector
                    mock_ifood = MockiFoodConnector()
                    retail_agent.register_connector('ifood', mock_ifood)
                    
                    # Registrar Retail Agent no Brain
                    brain.register_agent('retail', retail_agent)
                    
                    # Criar contexto
                    context = Context(
                        email=existing_user.email,
                        channel=ChannelType.TELEGRAM,
                        session_id=f"telegram_{user_id}",
                        user_profile={
                            'tier': existing_user.tier.value,
                            'telegram_id': user_id
                        }
                    )
                    
                    # Classificar intenção
                    intent = await brain.classify_intent(text, existing_user.email)
                    
                    if intent.domain == "retail":
                        # Executar via Retail Agent
                        result = await retail_agent.execute(intent, context)
                        
                        if result.get('success'):
                            if intent.action == "check_orders":
                                orders = result.get('orders', [])
                                if orders:
                                    response_text = f"🍔 <b>Seus pedidos no iFood:</b>\n\n"
                                    for i, order in enumerate(orders, 1):
                                        status_emoji = {
                                            'pending': '⏳',
                                            'confirmed': '✅',
                                            'preparing': '👨‍🍳',
                                            'ready': '🍽️',
                                            'delivered': '🚚',
                                            'cancelled': '❌'
                                        }.get(order.get('status', 'unknown'), '❓')
                                        
                                        response_text += (
                                            f"{status_emoji} <b>Pedido #{order.get('id')}</b>\n"
                                            f"💰 R$ {order.get('total', 0):.2f}\n"
                                            f"👤 {order.get('customer', 'Cliente')}\n"
                                            f"📦 {len(order.get('items', []))} itens\n\n"
                                        )
                                    
                                    pending_count = result.get('pending_orders', 0)
                                    if pending_count > 0:
                                        response_text += f"⚠️ <b>{pending_count} pedidos precisam de confirmação!</b>"
                                else:
                                    response_text = "🍔 Nenhum pedido encontrado no iFood."
                                    
                            elif intent.action == "check_revenue":
                                revenue = result.get('revenue', {})
                                response_text = (
                                    f"💰 <b>Faturamento iFood</b>\n\n"
                                    f"📊 <b>Período:</b> {revenue.get('period', 'hoje')}\n"
                                    f"💵 <b>Total:</b> R$ {revenue.get('total_revenue', 0):.2f}\n"
                                    f"📦 <b>Pedidos:</b> {revenue.get('total_orders', 0)}\n"
                                    f"🎯 <b>Ticket médio:</b> R$ {revenue.get('average_ticket', 0):.2f}\n\n"
                                )
                                
                                top_items = revenue.get('top_items', [])[:3]
                                if top_items:
                                    response_text += "<b>🏆 Top 3 itens:</b>\n"
                                    for i, item in enumerate(top_items, 1):
                                        response_text += f"{i}. {item.get('name')} - {item.get('quantity')} vendas\n"
                                        
                            elif intent.action == "manage_store":
                                store_result = result.get('result', result)
                                action = result.get('action', 'status')
                                status = store_result.get('status', 'unknown')
                                
                                status_emoji = {
                                    'open': '🟢',
                                    'closed': '🔴',
                                    'paused': '🟡'
                                }.get(status, '❓')
                                
                                response_text = (
                                    f"🏪 <b>Status da Loja iFood</b>\n\n"
                                    f"{status_emoji} <b>Status:</b> {status.upper()}\n"
                                )
                                
                                if action != 'status':
                                    response_text += f"✅ <b>Ação:</b> {action}\n"
                                
                                duration = result.get('duration')
                                if duration:
                                    response_text += f"⏰ <b>Duração:</b> {duration}\n"
                                    
                            elif intent.action == "confirm_order":
                                order_id = result.get('order_id')
                                response_text = (
                                    f"✅ <b>Pedido Confirmado!</b>\n\n"
                                    f"📦 <b>Pedido:</b> #{order_id}\n"
                                    f"🕐 <b>Confirmado em:</b> {datetime.now().strftime('%H:%M')}\n"
                                    f"⏱️ <b>Tempo estimado:</b> 25 minutos"
                                )
                                
                            elif intent.action == "cancel_order":
                                order_id = result.get('order_id')
                                reason = result.get('reason', 'Cancelado pelo restaurante')
                                response_text = (
                                    f"❌ <b>Pedido Cancelado</b>\n\n"
                                    f"📦 <b>Pedido:</b> #{order_id}\n"
                                    f"📝 <b>Motivo:</b> {reason}\n"
                                    f"🕐 <b>Cancelado em:</b> {datetime.now().strftime('%H:%M')}"
                                )
                                
                            else:
                                response_text = (
                                    f"✅ <b>Ação executada:</b> {intent.action}\n\n"
                                    f"📋 <b>Resultado:</b> {result.get('message', 'Sucesso')}"
                                )
                        else:
                            # Erro na execução
                            error = result.get('error', 'Erro desconhecido')
                            response_text = (
                                f"❌ <b>Erro ao executar ação</b>\n\n"
                                f"🔧 <b>Ação:</b> {intent.action}\n"
                                f"📝 <b>Erro:</b> {error}\n\n"
                                "Tente novamente em alguns segundos."
                            )
                    elif intent.domain == "general":
                        if intent.action == "greeting":
                            response_text = (
                                f"👋 Olá {existing_user.email}!\n\n"
                                "🍔 Como posso ajudar com seus pedidos do iFood hoje?\n\n"
                                "Experimente:\n"
                                "• 'Quantos pedidos tenho?'\n"
                                "• 'Qual meu faturamento hoje?'\n"
                                "• 'Feche a loja por 30 minutos'"
                            )
                        elif intent.action == "help":
                            response_text = (
                                "🆘 AJUDA - AgentFirst\n\n"
                                "🍔 PEDIDOS:\n"
                                "• 'Quantos pedidos tenho?'\n"
                                "• 'Confirme o pedido 123'\n"
                                "• 'Cancele o último pedido'\n\n"
                                "💰 FATURAMENTO:\n"
                                "• 'Qual meu faturamento hoje?'\n"
                                "• 'Relatório da semana'\n\n"
                                "🏪 LOJA:\n"
                                "• 'Feche a loja por 30min'\n"
                                "• 'Abra a loja'"
                            )
                        else:
                            response_text = (
                                f"🤖 Olá {existing_user.email}!\n\n"
                                f"Recebi: <b>{text}</b>\n\n"
                                "🔧 Brain funcionando! Classificação:\n"
                                f"📋 Domínio: {intent.domain}\n"
                                f"⚡ Ação: {intent.action}\n"
                                f"🎯 Confiança: {intent.confidence:.0%}"
                            )
                    else:
                        response_text = (
                            f"🤖 Brain classificou como: {intent.domain}.{intent.action}\n\n"
                            "🔧 Este domínio ainda não foi implementado."
                        )
        
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
