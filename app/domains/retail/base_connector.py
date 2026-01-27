"""
Base Connector Interface - Interface base para conectores de marketplace

Define a interface padrão que todos os conectores devem implementar:
- iFood Connector
- 99food Connector  
- Shoppe Connector
- Amazon Connector
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Order:
    """Modelo padrão de pedido"""
    id: str
    status: str  # pending, confirmed, preparing, ready, delivered, cancelled
    total: float
    customer: str
    items: List[Dict[str, Any]]
    created_at: datetime
    connector: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Revenue:
    """Modelo padrão de faturamento"""
    period: str
    total_revenue: float
    total_orders: int
    average_ticket: float
    top_items: List[Dict[str, Any]]
    connector: str
    generated_at: datetime


@dataclass
class StoreStatus:
    """Status da loja"""
    status: str  # open, closed, paused
    connector: str
    updated_at: datetime
    reason: Optional[str] = None
    duration: Optional[str] = None


class BaseConnector(ABC):
    """
    Interface base para conectores de marketplace
    
    Todos os conectores devem implementar estes métodos
    """
    
    def __init__(self, connector_type: str):
        """
        Inicializa conector
        
        Args:
            connector_type: Tipo do conector (ifood, 99food, etc)
        """
        self.connector_type = connector_type
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Autentica com o marketplace
        
        Returns:
            True se autenticação bem-sucedida
        """
        pass
    
    @abstractmethod
    async def get_orders(self, status: Optional[str] = None) -> List[Order]:
        """
        Recupera pedidos do marketplace
        
        Args:
            status: Filtrar por status (opcional)
        
        Returns:
            Lista de pedidos
        """
        pass
    
    @abstractmethod
    async def confirm_order(self, order_id: str) -> Dict[str, Any]:
        """
        Confirma pedido no marketplace
        
        Args:
            order_id: ID do pedido
        
        Returns:
            Resultado da confirmação
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, reason: str) -> Dict[str, Any]:
        """
        Cancela pedido no marketplace
        
        Args:
            order_id: ID do pedido
            reason: Motivo do cancelamento
        
        Returns:
            Resultado do cancelamento
        """
        pass
    
    @abstractmethod
    async def get_revenue(self, period: str = 'today') -> Revenue:
        """
        Recupera dados de faturamento
        
        Args:
            period: Período (today, week, month)
        
        Returns:
            Dados de faturamento
        """
        pass
    
    @abstractmethod
    async def manage_store(self, action: str, duration: Optional[str] = None) -> StoreStatus:
        """
        Gerencia status da loja
        
        Args:
            action: Ação (open, close, pause)
            duration: Duração (opcional)
        
        Returns:
            Status da loja
        """
        pass
    
    @abstractmethod
    async def update_inventory(self, item: str, quantity: int) -> Dict[str, Any]:
        """
        Atualiza estoque de item
        
        Args:
            item: Nome do item
            quantity: Nova quantidade
        
        Returns:
            Status da atualização
        """
        pass
    
    @abstractmethod
    async def forecast_demand(self, period: str = 'week') -> Dict[str, Any]:
        """
        Prevê demanda para período
        
        Args:
            period: Período de previsão
        
        Returns:
            Previsão de demanda
        """
        pass
    
    @abstractmethod
    async def get_store_status(self) -> StoreStatus:
        """
        Recupera status atual da loja
        
        Returns:
            Status da loja
        """
        pass
    
    @abstractmethod
    async def poll_events(self) -> List[Dict[str, Any]]:
        """
        Faz polling de eventos do marketplace
        
        Returns:
            Lista de eventos
        """
        pass
    
    @abstractmethod
    async def acknowledge_event(self, event_id: str) -> bool:
        """
        Reconhece evento processado
        
        Args:
            event_id: ID do evento
        
        Returns:
            True se reconhecimento bem-sucedido
        """
        pass