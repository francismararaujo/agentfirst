"""Authentication module for AgentFirst2 MVP"""

from .auth_service import AuthService, AuthConfig, User as AuthUser
from .channel_mapping import ChannelMappingService, ChannelMapping, ChannelMappingConfig
from .session_manager import SessionManager, Session, SessionConfig
from .user_repository import UserRepository, User, UserRepositoryConfig

__all__ = [
    "AuthService",
    "AuthConfig",
    "AuthUser",
    "ChannelMappingService",
    "ChannelMapping",
    "ChannelMappingConfig",
    "SessionManager",
    "Session",
    "SessionConfig",
    "UserRepository",
    "User",
    "UserRepositoryConfig",
]
