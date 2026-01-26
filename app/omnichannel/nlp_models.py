"""
NLP models for intent classification and entity extraction.

Defines data structures for representing intents, entities, and classifications
in natural language understanding.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
from enum import Enum


class IntentType(str, Enum):
    """Supported intent types"""
    CHECK_ORDERS = "check_orders"
    CONFIRM_ORDER = "confirm_order"
    CANCEL_ORDER = "cancel_order"
    CLOSE_STORE = "close_store"
    OPEN_STORE = "open_store"
    GET_REVENUE = "get_revenue"
    GET_TOP_ITEMS = "get_top_items"
    UPDATE_INVENTORY = "update_inventory"
    FORECAST_DEMAND = "forecast_demand"
    UNKNOWN = "unknown"


class EntityType(str, Enum):
    """Supported entity types"""
    ORDER_ID = "order_id"
    CONNECTOR = "connector"
    DURATION = "duration"
    DATE = "date"
    ITEM_NAME = "item_name"
    QUANTITY = "quantity"
    PRICE = "price"
    REASON = "reason"
    UNKNOWN = "unknown"


@dataclass
class Entity:
    """
    Extracted entity from user message.
    
    Represents a named entity extracted from natural language text,
    such as order IDs, connectors, durations, etc.
    """
    
    type: EntityType
    value: str
    confidence: float  # 0.0 to 1.0
    start_pos: Optional[int] = None  # Position in original text
    end_pos: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'type': self.type.value,
            'value': self.value,
            'confidence': self.confidence,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entity':
        """Create from dictionary"""
        data = data.copy()
        data['type'] = EntityType(data['type'])
        return cls(**data)


@dataclass
class IntentClassification:
    """
    Result of intent classification.
    
    Contains the classified intent, confidence score, extracted entities,
    and domain routing information.
    """
    
    intent: IntentType
    confidence: float  # 0.0 to 1.0
    entities: List[Entity] = field(default_factory=list)
    domain: str = "retail"  # Domain to route to (retail, tax, finance, etc)
    connector: Optional[str] = None  # Connector to use (ifood, 99food, etc)
    raw_text: Optional[str] = None  # Original user text
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'intent': self.intent.value,
            'confidence': self.confidence,
            'entities': [e.to_dict() for e in self.entities],
            'domain': self.domain,
            'connector': self.connector,
            'raw_text': self.raw_text
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IntentClassification':
        """Create from dictionary"""
        data = data.copy()
        data['intent'] = IntentType(data['intent'])
        data['entities'] = [Entity.from_dict(e) for e in data.get('entities', [])]
        return cls(**data)


@dataclass
class NLPResult:
    """
    Complete NLP processing result.
    
    Contains intent classification, extracted entities, and confidence scores.
    """
    
    classification: IntentClassification
    language: str = "pt-BR"  # Detected language
    confidence_overall: float = 0.0  # Overall confidence (0.0 to 1.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'classification': self.classification.to_dict(),
            'language': self.language,
            'confidence_overall': self.confidence_overall
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NLPResult':
        """Create from dictionary"""
        data = data.copy()
        data['classification'] = IntentClassification.from_dict(data['classification'])
        return cls(**data)
