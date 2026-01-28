"""Telegram Authentication Integration for AgentFirst2 MVP

This module provides complete Telegram authentication:
- Link Telegram ID to email
- Retrieve user by Telegram ID
- Manage channel mappings
- Handle registration flow
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

from app.omnichannel.authentication.auth_service import AuthService, AuthConfig
from app.omnichannel.database.repositories import UserRepository, ChannelMappingRepository
from app.omnichannel.models import ChannelType

logger = logging.getLogger(__name__)


class TelegramAuthService:
    """Telegram-specific authentication service"""

    def __init__(
        self,
        auth_service: AuthService,
        user_repo: UserRepository,
        channel_mapping_repo: ChannelMappingRepository,
    ):
        self.auth_service = auth_service
        self.user_repo = user_repo
        self.channel_mapping_repo = channel_mapping_repo

    async def register_telegram_user(
        self,
        telegram_id: int,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register or link Telegram user to email

        Args:
            telegram_id: Telegram user ID
            email: User email
            first_name: User first name
            last_name: User last name
            username: Telegram username

        Returns:
            Dict with registration result

        Raises:
            Exception: If registration fails
        """
        try:
            logger.info(
                json.dumps({
                    "event": "telegram_registration_started",
                    "telegram_id": telegram_id,
                    "email": email,
                })
            )

            # Authenticate/create user by email
            user = await self.auth_service.authenticate_user(email)

            logger.info(
                json.dumps({
                    "event": "user_authenticated_for_telegram",
                    "email": email,
                    "tier": user.tier,
                })
            )

            # Update user with Telegram ID
            await self.user_repo.update(
                email,
                {
                    "telegram_id": telegram_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "username": username,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
            )

            logger.info(
                json.dumps({
                    "event": "user_updated_with_telegram_id",
                    "email": email,
                    "telegram_id": telegram_id,
                })
            )

            # Create channel mapping
            await self.channel_mapping_repo.create_mapping(
                email=email,
                channel=ChannelType.TELEGRAM.value,
                channel_user_id=str(telegram_id),
                metadata={
                    "first_name": first_name,
                    "last_name": last_name,
                    "username": username,
                    "registered_at": datetime.now(timezone.utc).isoformat(),
                },
            )

            logger.info(
                json.dumps({
                    "event": "telegram_channel_mapping_created",
                    "email": email,
                    "telegram_id": telegram_id,
                })
            )

            return {
                "success": True,
                "email": email,
                "telegram_id": telegram_id,
                "tier": user.tier,
                "is_new_user": True,
                "message": f"✅ Cadastro realizado com sucesso!\n\n📧 Email: {email}\n🎯 Tier: {user.tier.upper()} (100 mensagens/mês)\n\n🍔 Agora você pode gerenciar seus pedidos do iFood!",
            }

        except Exception as e:
            logger.error(
                json.dumps({
                    "event": "telegram_registration_failed",
                    "error": str(e),
                    "telegram_id": telegram_id,
                    "email": email,
                })
            )
            raise

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user by Telegram ID

        Args:
            telegram_id: Telegram user ID

        Returns:
            User data if found, None otherwise
        """
        try:
            user = await self.user_repo.get_by_telegram_id(telegram_id)

            if user:
                logger.info(
                    json.dumps({
                        "event": "user_found_by_telegram_id",
                        "telegram_id": telegram_id,
                        "email": user.email,
                    })
                )
                return user

            logger.info(
                json.dumps({
                    "event": "user_not_found_by_telegram_id",
                    "telegram_id": telegram_id,
                })
            )
            return None

        except Exception as e:
            logger.error(
                json.dumps({
                    "event": "get_user_by_telegram_id_failed",
                    "error": str(e),
                    "telegram_id": telegram_id,
                })
            )
            raise

    async def handle_telegram_message(
        self,
        telegram_id: int,
        message_text: str,
        chat_id: int,
        first_name: Optional[str] = None,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle incoming Telegram message

        Determines if message is email registration or regular message

        Args:
            telegram_id: Telegram user ID
            message_text: Message text
            chat_id: Telegram chat ID
            first_name: User first name
            username: Telegram username

        Returns:
            Dict with handling result
        """
        try:
            logger.info(
                json.dumps({
                    "event": "telegram_message_received",
                    "telegram_id": telegram_id,
                    "message_length": len(message_text),
                })
            )

            # Check if user already exists
            existing_user = await self.get_user_by_telegram_id(telegram_id)

            if existing_user:
                # User already registered
                logger.info(
                    json.dumps({
                        "event": "telegram_user_already_registered",
                        "telegram_id": telegram_id,
                        "email": existing_user.get("email"),
                    })
                )

                return {
                    "success": True,
                    "user_exists": True,
                    "email": existing_user.get("email"),
                    "tier": existing_user.get("tier"),
                    "message_text": message_text,
                    "action": "process_message",
                }

            # Check if message is email for registration
            if self._is_email(message_text):
                # Register new user
                email = message_text.strip().lower()

                logger.info(
                    json.dumps({
                        "event": "email_registration_detected",
                        "telegram_id": telegram_id,
                        "email": email,
                    })
                )

                result = await self.register_telegram_user(
                    telegram_id=telegram_id,
                    email=email,
                    first_name=first_name,
                    username=username,
                )

                return {
                    "success": True,
                    "user_exists": False,
                    "email": email,
                    "tier": result["tier"],
                    "message": result["message"],
                    "action": "registration_complete",
                }

            else:
                # User not registered and message is not email
                logger.info(
                    json.dumps({
                        "event": "unregistered_user_non_email_message",
                        "telegram_id": telegram_id,
                    })
                )

                return {
                    "success": False,
                    "user_exists": False,
                    "action": "ask_for_email",
                    "message": (
                        "👋 Olá! Bem-vindo ao AgentFirst!\n\n"
                        "🍔 Sou seu assistente para gerenciar pedidos do iFood.\n\n"
                        "Para começar, preciso do seu email para identificá-lo em todos os canais.\n\n"
                        "📧 Por favor, envie seu email (ex: seu@email.com):"
                    ),
                }

        except Exception as e:
            logger.error(
                json.dumps({
                    "event": "handle_telegram_message_failed",
                    "error": str(e),
                    "telegram_id": telegram_id,
                })
            )
            raise

    @staticmethod
    def _is_email(text: str) -> bool:
        """
        Check if text is an email address

        Args:
            text: Text to check

        Returns:
            True if text is email, False otherwise
        """
        import re

        # Simple email validation
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, text.strip()))

    async def link_telegram_to_existing_user(
        self,
        telegram_id: int,
        email: str,
        first_name: Optional[str] = None,
        username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Link Telegram ID to existing user

        Args:
            telegram_id: Telegram user ID
            email: User email
            first_name: User first name
            username: Telegram username

        Returns:
            Dict with linking result
        """
        try:
            logger.info(
                json.dumps({
                    "event": "linking_telegram_to_existing_user",
                    "telegram_id": telegram_id,
                    "email": email,
                })
            )

            # Verify user exists
            user = await self.auth_service.get_user(email)
            if not user:
                raise ValueError(f"User {email} not found")

            # Update user with Telegram ID
            await self.user_repo.update(
                email,
                {
                    "telegram_id": telegram_id,
                    "first_name": first_name,
                    "username": username,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
            )

            # Create channel mapping
            await self.channel_mapping_repo.create_mapping(
                email=email,
                channel=ChannelType.TELEGRAM.value,
                channel_user_id=str(telegram_id),
                metadata={
                    "first_name": first_name,
                    "username": username,
                    "linked_at": datetime.now(timezone.utc).isoformat(),
                },
            )

            logger.info(
                json.dumps({
                    "event": "telegram_linked_to_existing_user",
                    "email": email,
                    "telegram_id": telegram_id,
                })
            )

            return {
                "success": True,
                "email": email,
                "telegram_id": telegram_id,
                "message": f"✅ Perfeito! Vinculei seu Telegram ao email: {email}\n\n🍔 Agora você pode usar o AgentFirst!",
            }

        except Exception as e:
            logger.error(
                json.dumps({
                    "event": "link_telegram_to_existing_user_failed",
                    "error": str(e),
                    "telegram_id": telegram_id,
                    "email": email,
                })
            )
            raise
