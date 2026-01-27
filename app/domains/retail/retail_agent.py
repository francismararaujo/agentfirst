"""
Retail Agent (Strands) - Agente especializado em operações de varejo

Responsabilidades:
1. Gerenciar pedidos (check, confirm, cancel)
2. Gerenciar estoque (update, forecast)
3. Integrar com conectores (iFood, 99food, etc)
4. Processar eventos de negócio
5. Manter estado da conversa

Padrão Strands:
- Tools específicas para cada ação
- State management para contexto
- Error handling com retry
- Event publishing
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import asyncio

from app.core.brain import Intent, Context

logger = logging.getLogger(__name__)


@dataclass
class RetailState:
    """Estado do agente retail"""
    last_connector: Optional[str] = None
    last_orders: List[Dict[str, Any]] = None
    last_revenue: Optional[Dict[str, Any]] = None
    store_status: str = "open"  # open, closed, paused
    
    def __post_init__(self):
        if self.last_orders is None:
            self.last_orders = []


class RetailAgent:
    """
    Agente Retail seguindo padrão Strands
    
    Gerencia operações de varejo:
    - Pedidos (iFood, 99food, etc)
    - Estoque
    - Faturamento
    - Status da loja
    """
    
    def __init__(self, event_bus=None, auditor=None):
        """
        Inicializa Retail Agent
        
        Args:
            event_bus: Event bus para publicar eventos
            auditor: Serviço de auditoria
        """
        self.event_bus = event_bus
        self.auditor = auditor
        self.state = RetailState()
        self.connectors = {}  # Conectores por tipo (ifood, 99food, etc)
        
        # Tools disponíveis
        self.tools = {
            'check_orders': self.check_orders,
            'confirm_order': self.confirm_order,
            'cancel_order': self.cancel_order,
            'check_revenue': self.check_revenue,
            'manage_store': self.manage_store,
            'update_inventory': self.update_inventory,
            'forecast_demand': self.forecast_demand
        }
    
    def register_connector(self, connector_type: str, connector):
        """
        Registra conector para tipo específico
        
        Args:
            connector_type: Tipo do conector (ifood, 99food, etc)
            connector: Instância do conector
        """
        self.connectors[connector_type] = connector
        logger.info(f"Registered connector: {connector_type}")
    
    async def execute(self, intent: Intent, context: Context) -> Dict[str, Any]:
        """
        Executa ação baseada na intenção
        
        Args:
            intent: Intenção classificada pelo Brain
            context: Contexto da conversa
        
        Returns:
            Resultado da execução
        """
        try:
            # Verificar se tool existe
            if intent.action not in self.tools:
                return {
                    'success': False,
                    'error': f"Ação '{intent.action}' não suportada",
                    'available_actions': list(self.tools.keys())
                }
            
            # Executar tool
            tool = self.tools[intent.action]
            result = await tool(intent, context)
            
            # Publicar evento
            if self.event_bus:
                await self.event_bus.publish(
                    topic=f"retail.{intent.action}",
                    message={
                        'email': context.email,
                        'action': intent.action,
                        'connector': intent.connector,
                        'result': result,
                        'timestamp': datetime.now().isoformat()
                    }
                )
            
            # Registrar auditoria
            if self.auditor:
                await self.auditor.log_transaction(
                    email=context.email,
                    action=f"retail.{intent.action}",
                    input_data={
                        'intent': intent.action,
                        'connector': intent.connector,
                        'entities': intent.entities
                    },
                    output_data=result
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing retail action {intent.action}: {str(e)}")
            
            error_result = {
                'success': False,
                'error': str(e),
                'action': intent.action
            }
            
            # Registrar erro na auditoria
            if self.auditor:
                await self.auditor.log_transaction(
                    email=context.email,
                    action=f"retail.{intent.action}.error",
                    input_data={
                        'intent': intent.action,
                        'connector': intent.connector
                    },
                    output_data=error_result
                )
            
            return error_result
    
    async def check_orders(self, intent: Intent, context: Context) -> Dict[str, Any]:
        """
        Verifica pedidos nos conectores
        
        Args:
            intent: Intenção com parâmetros
            context: Contexto da conversa
        
        Returns:
            Lista de pedidos
        """
        try:
            connector_type = intent.connector or 'ifood'  # Default para iFood
            
            if connector_type not in self.connectors:
                # Mock response para desenvolvimento
                mock_orders = [
                    {
                        'id': '12345',
                        'status': 'pending',
                        'total': 89.90,
                        'customer': 'João Silva',
                        'items': ['2x Hambúrguer', '1x Refrigerante'],
                        'created_at': '2025-01-26T10:30:00Z'
                    },
                    {
                        'id': '12346',
                        'status': 'confirmed',
                        'total': 125.50,
                        'customer': 'Maria Santos',
                        'items': ['1x Pizza Grande', '2x Refrigerante'],
                        'created_at': '2025-01-26T11:15:00Z'
                    },
                    {
                        'id': '12347',
                        'status': 'ready',
                        'total': 67.30,
                        'customer': 'Pedro Costa',
                        'items': ['1x Sanduíche', '1x Suco'],
                        'created_at': '2025-01-26T11:45:00Z'
                    }
                ]
                
                # Atualizar estado
                self.state.last_connector = connector_type
                self.state.last_orders = mock_orders
                
                return {
                    'success': True,
                    'connector': connector_type,
                    'orders': mock_orders,
                    'total_orders': len(mock_orders),
                    'pending_orders': len([o for o in mock_orders if o['status'] == 'pending']),
                    'message': f"Encontrados {len(mock_orders)} pedidos no {connector_type.upper()}"
                }
            
            # Usar conector real
            connector = self.connectors[connector_type]
            orders = await connector.get_orders()
            
            # Atualizar estado
            self.state.last_connector = connector_type
            self.state.last_orders = orders
            
            return {
                'success': True,
                'connector': connector_type,
                'orders': orders,
                'total_orders': len(orders),
                'pending_orders': len([o for o in orders if o.get('status') == 'pending'])
            }
            
        except Exception as e:
            logger.error(f"Error checking orders: {str(e)}")
            return {
                'success': False,
                'error': f"Erro ao verificar pedidos: {str(e)}"
            }
    
    async def confirm_order(self, intent: Intent, context: Context) -> Dict[str, Any]:
        """
        Confirma pedido específico
        
        Args:
            intent: Intenção com order_id
            context: Contexto da conversa
        
        Returns:
            Resultado da confirmação
        """
        try:
            order_id = intent.entities.get('order_id')
            connector_type = intent.connector or self.state.last_connector or 'ifood'
            
            if not order_id:
                # Tentar pegar o primeiro pedido pendente
                if self.state.last_orders:
                    pending_orders = [o for o in self.state.last_orders if o.get('status') == 'pending']
                    if pending_orders:
                        order_id = pending_orders[0]['id']
                    else:
                        return {
                            'success': False,
                            'error': 'Nenhum pedido pendente encontrado'
                        }
                else:
                    return {
                        'success': False,
                        'error': 'ID do pedido não especificado'
                    }
            
            if connector_type not in self.connectors:
                # Mock response para desenvolvimento
                return {
                    'success': True,
                    'order_id': order_id,
                    'connector': connector_type,
                    'message': f"Pedido {order_id} confirmado no {connector_type.upper()}",
                    'confirmed_at': datetime.now().isoformat()
                }
            
            # Usar conector real
            connector = self.connectors[connector_type]
            result = await connector.confirm_order(order_id)
            
            return {
                'success': True,
                'order_id': order_id,
                'connector': connector_type,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Error confirming order: {str(e)}")
            return {
                'success': False,
                'error': f"Erro ao confirmar pedido: {str(e)}"
            }
    
    async def cancel_order(self, intent: Intent, context: Context) -> Dict[str, Any]:
        """
        Cancela pedido específico
        
        Args:
            intent: Intenção com order_id e reason
            context: Contexto da conversa
        
        Returns:
            Resultado do cancelamento
        """
        try:
            order_id = intent.entities.get('order_id')
            reason = intent.entities.get('reason', 'Cancelado pelo restaurante')
            connector_type = intent.connector or self.state.last_connector or 'ifood'
            
            if not order_id:
                return {
                    'success': False,
                    'error': 'ID do pedido não especificado'
                }
            
            if connector_type not in self.connectors:
                # Mock response para desenvolvimento
                return {
                    'success': True,
                    'order_id': order_id,
                    'reason': reason,
                    'connector': connector_type,
                    'message': f"Pedido {order_id} cancelado no {connector_type.upper()}",
                    'cancelled_at': datetime.now().isoformat()
                }
            
            # Usar conector real
            connector = self.connectors[connector_type]
            result = await connector.cancel_order(order_id, reason)
            
            return {
                'success': True,
                'order_id': order_id,
                'reason': reason,
                'connector': connector_type,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return {
                'success': False,
                'error': f"Erro ao cancelar pedido: {str(e)}"
            }
    
    async def check_revenue(self, intent: Intent, context: Context) -> Dict[str, Any]:
        """
        Verifica faturamento
        
        Args:
            intent: Intenção com período
            context: Contexto da conversa
        
        Returns:
            Dados de faturamento
        """
        try:
            time_period = intent.entities.get('time_period', 'today')
            connector_type = intent.connector or 'ifood'
            
            if connector_type not in self.connectors:
                # Mock response para desenvolvimento
                mock_revenue = {
                    'period': time_period,
                    'total_revenue': 2847.50,
                    'total_orders': 23,
                    'average_ticket': 123.80,
                    'top_items': [
                        {'name': 'Hambúrguer Clássico', 'quantity': 45, 'revenue': 1125.00},
                        {'name': 'Refrigerante 2L', 'quantity': 38, 'revenue': 456.00},
                        {'name': 'Batata Frita', 'quantity': 35, 'revenue': 525.00}
                    ]
                }
                
                # Atualizar estado
                self.state.last_revenue = mock_revenue
                
                return {
                    'success': True,
                    'connector': connector_type,
                    'revenue': mock_revenue,
                    'message': f"Faturamento {time_period}: R$ {mock_revenue['total_revenue']:.2f}"
                }
            
            # Usar conector real
            connector = self.connectors[connector_type]
            revenue = await connector.get_revenue(time_period)
            
            # Atualizar estado
            self.state.last_revenue = revenue
            
            return {
                'success': True,
                'connector': connector_type,
                'revenue': revenue
            }
            
        except Exception as e:
            logger.error(f"Error checking revenue: {str(e)}")
            return {
                'success': False,
                'error': f"Erro ao verificar faturamento: {str(e)}"
            }
    
    async def manage_store(self, intent: Intent, context: Context) -> Dict[str, Any]:
        """
        Gerencia status da loja
        
        Args:
            intent: Intenção com ação (open, close, pause)
            context: Contexto da conversa
        
        Returns:
            Status da loja
        """
        try:
            action = intent.entities.get('action', 'status')
            duration = intent.entities.get('duration')
            connector_type = intent.connector or 'ifood'
            
            if connector_type not in self.connectors:
                # Mock response para desenvolvimento
                if action == 'close':
                    self.state.store_status = 'closed'
                    message = f"Loja fechada no {connector_type.upper()}"
                    if duration:
                        message += f" por {duration}"
                elif action == 'open':
                    self.state.store_status = 'open'
                    message = f"Loja aberta no {connector_type.upper()}"
                elif action == 'pause':
                    self.state.store_status = 'paused'
                    message = f"Pedidos pausados no {connector_type.upper()}"
                    if duration:
                        message += f" por {duration}"
                else:
                    message = f"Status atual: {self.state.store_status}"
                
                return {
                    'success': True,
                    'connector': connector_type,
                    'action': action,
                    'status': self.state.store_status,
                    'duration': duration,
                    'message': message,
                    'updated_at': datetime.now().isoformat()
                }
            
            # Usar conector real
            connector = self.connectors[connector_type]
            result = await connector.manage_store(action, duration)
            
            return {
                'success': True,
                'connector': connector_type,
                'action': action,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Error managing store: {str(e)}")
            return {
                'success': False,
                'error': f"Erro ao gerenciar loja: {str(e)}"
            }
    
    async def update_inventory(self, intent: Intent, context: Context) -> Dict[str, Any]:
        """
        Atualiza estoque
        
        Args:
            intent: Intenção com item e quantidade
            context: Contexto da conversa
        
        Returns:
            Status do estoque
        """
        try:
            item = intent.entities.get('item')
            quantity = intent.entities.get('quantity')
            connector_type = intent.connector or 'ifood'
            
            if connector_type not in self.connectors:
                # Mock response para desenvolvimento
                return {
                    'success': True,
                    'connector': connector_type,
                    'item': item,
                    'quantity': quantity,
                    'message': f"Estoque atualizado: {item} = {quantity}",
                    'updated_at': datetime.now().isoformat()
                }
            
            # Usar conector real
            connector = self.connectors[connector_type]
            result = await connector.update_inventory(item, quantity)
            
            return {
                'success': True,
                'connector': connector_type,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Error updating inventory: {str(e)}")
            return {
                'success': False,
                'error': f"Erro ao atualizar estoque: {str(e)}"
            }
    
    async def forecast_demand(self, intent: Intent, context: Context) -> Dict[str, Any]:
        """
        Prevê demanda
        
        Args:
            intent: Intenção com período
            context: Contexto da conversa
        
        Returns:
            Previsão de demanda
        """
        try:
            period = intent.entities.get('period', 'week')
            connector_type = intent.connector or 'ifood'
            
            if connector_type not in self.connectors:
                # Mock response para desenvolvimento
                mock_forecast = {
                    'period': period,
                    'predicted_orders': 150,
                    'predicted_revenue': 12500.00,
                    'top_items_forecast': [
                        {'item': 'Hambúrguer', 'predicted_quantity': 80},
                        {'item': 'Refrigerante', 'predicted_quantity': 120},
                        {'item': 'Batata Frita', 'predicted_quantity': 60}
                    ],
                    'recommendations': [
                        'Aumentar estoque de Refrigerante',
                        'Preparar ingredientes para Hambúrguer'
                    ]
                }
                
                return {
                    'success': True,
                    'connector': connector_type,
                    'forecast': mock_forecast,
                    'message': f"Previsão para {period}: {mock_forecast['predicted_orders']} pedidos"
                }
            
            # Usar conector real
            connector = self.connectors[connector_type]
            forecast = await connector.forecast_demand(period)
            
            return {
                'success': True,
                'connector': connector_type,
                'forecast': forecast
            }
            
        except Exception as e:
            logger.error(f"Error forecasting demand: {str(e)}")
            return {
                'success': False,
                'error': f"Erro ao prever demanda: {str(e)}"
            }
    
    async def handle_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Processa eventos do Event Bus
        
        Args:
            event_type: Tipo de evento
            event_data: Dados do evento
        """
        try:
            logger.info(f"Handling retail event: {event_type}")
            
            if event_type == 'order_received':
                # Novo pedido recebido
                await self._handle_new_order(event_data)
            elif event_type == 'order_confirmed':
                # Pedido confirmado
                await self._handle_order_confirmed(event_data)
            elif event_type == 'order_cancelled':
                # Pedido cancelado
                await self._handle_order_cancelled(event_data)
            else:
                logger.warning(f"Unknown event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error handling event {event_type}: {str(e)}")
    
    async def _handle_new_order(self, event_data: Dict[str, Any]) -> None:
        """Processa novo pedido"""
        order_id = event_data.get('order_id')
        connector = event_data.get('connector')
        
        logger.info(f"New order received: {order_id} from {connector}")
        
        # TODO: Notificar usuário em todos os canais
        # TODO: Atualizar estatísticas
        # TODO: Verificar se requer atenção especial
    
    async def _handle_order_confirmed(self, event_data: Dict[str, Any]) -> None:
        """Processa confirmação de pedido"""
        order_id = event_data.get('order_id')
        connector = event_data.get('connector')
        
        logger.info(f"Order confirmed: {order_id} from {connector}")
        
        # TODO: Atualizar status interno
        # TODO: Iniciar preparação
    
    async def _handle_order_cancelled(self, event_data: Dict[str, Any]) -> None:
        """Processa cancelamento de pedido"""
        order_id = event_data.get('order_id')
        reason = event_data.get('reason')
        connector = event_data.get('connector')
        
        logger.info(f"Order cancelled: {order_id} from {connector}, reason: {reason}")
        
        # TODO: Atualizar estatísticas
        # TODO: Analisar motivo do cancelamento