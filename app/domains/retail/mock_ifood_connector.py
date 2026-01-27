"""
Mock iFood Connector - Conector simulado para desenvolvimento e testes

Este conector simula as operações do iFood para permitir desenvolvimento
e testes sem depender da API real do iFood.

Será substituído pelo iFood Connector real na Fase 7.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import random

from .base_connector import BaseConnector, Order, Revenue, StoreStatus

logger = logging.getLogger(__name__)


class MockiFoodConnector(BaseConnector):
    """
    Conector simulado do iFood para desenvolvimento
    
    Simula todas as operações necessárias:
    - Autenticação
    - Polling de pedidos
    - Confirmação/cancelamento
    - Faturamento
    - Gerenciamento da loja
    """
    
    def __init__(self):
        """Inicializa mock connector"""
        super().__init__('ifood')
        self.authenticated = False
        self.store_status = 'open'
        self.mock_orders = self._generate_mock_orders()
        self.mock_events = []
        
    def _generate_mock_orders(self) -> List[Order]:
        """Gera pedidos simulados"""
        orders = []
        
        # Pedidos de exemplo
        mock_data = [
            {
                'id': '12345',
                'status': 'pending',
                'total': 89.90,
                'customer': 'João Silva',
                'items': [
                    {'name': 'Hambúrguer Clássico', 'quantity': 2, 'price': 25.90},
                    {'name': 'Refrigerante 2L', 'quantity': 1, 'price': 12.90},
                    {'name': 'Batata Frita', 'quantity': 1, 'price': 15.90}
                ]
            },
            {
                'id': '12346',
                'status': 'confirmed',
                'total': 125.50,
                'customer': 'Maria Santos',
                'items': [
                    {'name': 'Pizza Grande Margherita', 'quantity': 1, 'price': 45.90},
                    {'name': 'Pizza Grande Calabresa', 'quantity': 1, 'price': 42.90},
                    {'name': 'Refrigerante 2L', 'quantity': 2, 'price': 12.90}
                ]
            },
            {
                'id': '12347',
                'status': 'ready',
                'total': 67.30,
                'customer': 'Pedro Costa',
                'items': [
                    {'name': 'Sanduíche Natural', 'quantity': 1, 'price': 18.90},
                    {'name': 'Suco de Laranja', 'quantity': 2, 'price': 8.90},
                    {'name': 'Salada Caesar', 'quantity': 1, 'price': 22.90}
                ]
            },
            {
                'id': '12348',
                'status': 'preparing',
                'total': 156.80,
                'customer': 'Ana Oliveira',
                'items': [
                    {'name': 'Hambúrguer Gourmet', 'quantity': 2, 'price': 35.90},
                    {'name': 'Batata Rústica', 'quantity': 2, 'price': 18.90},
                    {'name': 'Milk Shake', 'quantity': 2, 'price': 16.90}
                ]
            }
        ]
        
        for data in mock_data:
            order = Order(
                id=data['id'],
                status=data['status'],
                total=data['total'],
                customer=data['customer'],
                items=data['items'],
                created_at=datetime.now() - timedelta(minutes=random.randint(10, 120)),
                connector='ifood',
                metadata={
                    'delivery_address': f"Rua {random.choice(['A', 'B', 'C'])}, {random.randint(100, 999)}",
                    'payment_method': random.choice(['credit_card', 'cash', 'pix']),
                    'estimated_delivery': datetime.now() + timedelta(minutes=random.randint(30, 60))
                }
            )
            orders.append(order)
        
        return orders
    
    async def authenticate(self) -> bool:
        """
        Simula autenticação com iFood
        
        Returns:
            True (sempre bem-sucedida no mock)
        """
        logger.info("Mock iFood: Authenticating...")
        await asyncio.sleep(0.1)  # Simula latência
        self.authenticated = True
        logger.info("Mock iFood: Authentication successful")
        return True
    
    async def get_orders(self, status: Optional[str] = None) -> List[Order]:
        """
        Recupera pedidos simulados
        
        Args:
            status: Filtrar por status
        
        Returns:
            Lista de pedidos
        """
        if not self.authenticated:
            await self.authenticate()
        
        logger.info(f"Mock iFood: Getting orders (status: {status})")
        await asyncio.sleep(0.2)  # Simula latência
        
        orders = self.mock_orders.copy()
        
        if status:
            orders = [o for o in orders if o.status == status]
        
        logger.info(f"Mock iFood: Found {len(orders)} orders")
        return orders
    
    async def confirm_order(self, order_id: str) -> Dict[str, Any]:
        """
        Simula confirmação de pedido
        
        Args:
            order_id: ID do pedido
        
        Returns:
            Resultado da confirmação
        """
        if not self.authenticated:
            await self.authenticate()
        
        logger.info(f"Mock iFood: Confirming order {order_id}")
        await asyncio.sleep(0.3)  # Simula latência
        
        # Encontrar pedido
        order = None
        for o in self.mock_orders:
            if o.id == order_id:
                order = o
                break
        
        if not order:
            return {
                'success': False,
                'error': f'Pedido {order_id} não encontrado'
            }
        
        if order.status != 'pending':
            return {
                'success': False,
                'error': f'Pedido {order_id} não pode ser confirmado (status: {order.status})'
            }
        
        # Confirmar pedido
        order.status = 'confirmed'
        order.metadata['confirmed_at'] = datetime.now().isoformat()
        
        # Gerar evento
        self.mock_events.append({
            'id': f'event_{len(self.mock_events) + 1}',
            'type': 'order_confirmed',
            'order_id': order_id,
            'timestamp': datetime.now().isoformat(),
            'data': {
                'order_id': order_id,
                'status': 'confirmed',
                'confirmed_at': datetime.now().isoformat()
            }
        })
        
        logger.info(f"Mock iFood: Order {order_id} confirmed successfully")
        return {
            'success': True,
            'order_id': order_id,
            'status': 'confirmed',
            'confirmed_at': datetime.now().isoformat(),
            'estimated_preparation_time': '25 minutes'
        }
    
    async def cancel_order(self, order_id: str, reason: str) -> Dict[str, Any]:
        """
        Simula cancelamento de pedido
        
        Args:
            order_id: ID do pedido
            reason: Motivo do cancelamento
        
        Returns:
            Resultado do cancelamento
        """
        if not self.authenticated:
            await self.authenticate()
        
        logger.info(f"Mock iFood: Cancelling order {order_id}, reason: {reason}")
        await asyncio.sleep(0.3)  # Simula latência
        
        # Encontrar pedido
        order = None
        for o in self.mock_orders:
            if o.id == order_id:
                order = o
                break
        
        if not order:
            return {
                'success': False,
                'error': f'Pedido {order_id} não encontrado'
            }
        
        if order.status in ['delivered', 'cancelled']:
            return {
                'success': False,
                'error': f'Pedido {order_id} não pode ser cancelado (status: {order.status})'
            }
        
        # Cancelar pedido
        order.status = 'cancelled'
        order.metadata['cancelled_at'] = datetime.now().isoformat()
        order.metadata['cancellation_reason'] = reason
        
        # Gerar evento
        self.mock_events.append({
            'id': f'event_{len(self.mock_events) + 1}',
            'type': 'order_cancelled',
            'order_id': order_id,
            'timestamp': datetime.now().isoformat(),
            'data': {
                'order_id': order_id,
                'status': 'cancelled',
                'reason': reason,
                'cancelled_at': datetime.now().isoformat()
            }
        })
        
        logger.info(f"Mock iFood: Order {order_id} cancelled successfully")
        return {
            'success': True,
            'order_id': order_id,
            'status': 'cancelled',
            'reason': reason,
            'cancelled_at': datetime.now().isoformat()
        }
    
    async def get_revenue(self, period: str = 'today') -> Revenue:
        """
        Simula dados de faturamento
        
        Args:
            period: Período (today, week, month)
        
        Returns:
            Dados de faturamento
        """
        if not self.authenticated:
            await self.authenticate()
        
        logger.info(f"Mock iFood: Getting revenue for period: {period}")
        await asyncio.sleep(0.2)  # Simula latência
        
        # Dados simulados baseados no período
        if period == 'today':
            total_revenue = 2847.50
            total_orders = 23
        elif period == 'week':
            total_revenue = 18650.30
            total_orders = 156
        elif period == 'month':
            total_revenue = 78420.80
            total_orders = 642
        else:
            total_revenue = 2847.50
            total_orders = 23
        
        average_ticket = total_revenue / total_orders if total_orders > 0 else 0
        
        top_items = [
            {'name': 'Hambúrguer Clássico', 'quantity': int(total_orders * 0.4), 'revenue': total_revenue * 0.25},
            {'name': 'Pizza Grande', 'quantity': int(total_orders * 0.3), 'revenue': total_revenue * 0.35},
            {'name': 'Refrigerante 2L', 'quantity': int(total_orders * 0.8), 'revenue': total_revenue * 0.15},
            {'name': 'Batata Frita', 'quantity': int(total_orders * 0.5), 'revenue': total_revenue * 0.12},
            {'name': 'Sobremesa', 'quantity': int(total_orders * 0.2), 'revenue': total_revenue * 0.13}
        ]
        
        revenue = Revenue(
            period=period,
            total_revenue=total_revenue,
            total_orders=total_orders,
            average_ticket=average_ticket,
            top_items=top_items,
            connector='ifood',
            generated_at=datetime.now()
        )
        
        logger.info(f"Mock iFood: Revenue for {period}: R$ {total_revenue:.2f}")
        return revenue
    
    async def manage_store(self, action: str, duration: Optional[str] = None) -> StoreStatus:
        """
        Simula gerenciamento da loja
        
        Args:
            action: Ação (open, close, pause)
            duration: Duração (opcional)
        
        Returns:
            Status da loja
        """
        if not self.authenticated:
            await self.authenticate()
        
        logger.info(f"Mock iFood: Managing store - action: {action}, duration: {duration}")
        await asyncio.sleep(0.2)  # Simula latência
        
        if action == 'close':
            self.store_status = 'closed'
            reason = 'Fechado pelo restaurante'
        elif action == 'open':
            self.store_status = 'open'
            reason = 'Aberto pelo restaurante'
        elif action == 'pause':
            self.store_status = 'paused'
            reason = 'Pausado temporariamente'
        else:
            reason = None
        
        status = StoreStatus(
            status=self.store_status,
            connector='ifood',
            updated_at=datetime.now(),
            reason=reason,
            duration=duration
        )
        
        # Gerar evento
        self.mock_events.append({
            'id': f'event_{len(self.mock_events) + 1}',
            'type': 'store_status_changed',
            'timestamp': datetime.now().isoformat(),
            'data': {
                'status': self.store_status,
                'action': action,
                'duration': duration,
                'reason': reason
            }
        })
        
        logger.info(f"Mock iFood: Store status changed to: {self.store_status}")
        return status
    
    async def update_inventory(self, item: str, quantity: int) -> Dict[str, Any]:
        """
        Simula atualização de estoque
        
        Args:
            item: Nome do item
            quantity: Nova quantidade
        
        Returns:
            Status da atualização
        """
        if not self.authenticated:
            await self.authenticate()
        
        logger.info(f"Mock iFood: Updating inventory - {item}: {quantity}")
        await asyncio.sleep(0.2)  # Simula latência
        
        result = {
            'success': True,
            'item': item,
            'quantity': quantity,
            'previous_quantity': random.randint(0, 50),
            'updated_at': datetime.now().isoformat(),
            'status': 'available' if quantity > 0 else 'unavailable'
        }
        
        logger.info(f"Mock iFood: Inventory updated for {item}")
        return result
    
    async def forecast_demand(self, period: str = 'week') -> Dict[str, Any]:
        """
        Simula previsão de demanda
        
        Args:
            period: Período de previsão
        
        Returns:
            Previsão de demanda
        """
        if not self.authenticated:
            await self.authenticate()
        
        logger.info(f"Mock iFood: Forecasting demand for period: {period}")
        await asyncio.sleep(0.5)  # Simula latência (ML processing)
        
        # Dados simulados baseados no período
        if period == 'week':
            predicted_orders = 150
            predicted_revenue = 12500.00
        elif period == 'month':
            predicted_orders = 650
            predicted_revenue = 54000.00
        else:
            predicted_orders = 25
            predicted_revenue = 2100.00
        
        forecast = {
            'period': period,
            'predicted_orders': predicted_orders,
            'predicted_revenue': predicted_revenue,
            'confidence': 0.85,
            'top_items_forecast': [
                {'item': 'Hambúrguer Clássico', 'predicted_quantity': int(predicted_orders * 0.4)},
                {'item': 'Pizza Grande', 'predicted_quantity': int(predicted_orders * 0.3)},
                {'item': 'Refrigerante 2L', 'predicted_quantity': int(predicted_orders * 0.8)},
                {'item': 'Batata Frita', 'predicted_quantity': int(predicted_orders * 0.5)}
            ],
            'recommendations': [
                'Aumentar estoque de Refrigerante 2L',
                'Preparar ingredientes para Hambúrguer Clássico',
                'Considerar promoção para Pizza Grande'
            ],
            'generated_at': datetime.now().isoformat()
        }
        
        logger.info(f"Mock iFood: Forecast generated - {predicted_orders} orders predicted")
        return forecast
    
    async def get_store_status(self) -> StoreStatus:
        """
        Recupera status atual da loja
        
        Returns:
            Status da loja
        """
        if not self.authenticated:
            await self.authenticate()
        
        return StoreStatus(
            status=self.store_status,
            connector='ifood',
            updated_at=datetime.now()
        )
    
    async def poll_events(self) -> List[Dict[str, Any]]:
        """
        Simula polling de eventos
        
        Returns:
            Lista de eventos
        """
        if not self.authenticated:
            await self.authenticate()
        
        logger.info("Mock iFood: Polling events...")
        await asyncio.sleep(0.1)  # Simula latência
        
        # Retornar eventos não processados
        events = self.mock_events.copy()
        
        # Simular novos eventos ocasionalmente
        if random.random() < 0.1:  # 10% chance
            new_event = {
                'id': f'event_{len(self.mock_events) + 1}',
                'type': 'order_received',
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'order_id': f'new_{random.randint(10000, 99999)}',
                    'customer': f'Cliente {random.randint(1, 100)}',
                    'total': round(random.uniform(30, 200), 2)
                }
            }
            self.mock_events.append(new_event)
            events.append(new_event)
        
        logger.info(f"Mock iFood: Found {len(events)} events")
        return events
    
    async def acknowledge_event(self, event_id: str) -> bool:
        """
        Simula reconhecimento de evento
        
        Args:
            event_id: ID do evento
        
        Returns:
            True se bem-sucedido
        """
        logger.info(f"Mock iFood: Acknowledging event {event_id}")
        await asyncio.sleep(0.1)  # Simula latência
        
        # Remover evento da lista (simulando processamento)
        self.mock_events = [e for e in self.mock_events if e['id'] != event_id]
        
        logger.info(f"Mock iFood: Event {event_id} acknowledged")
        return True