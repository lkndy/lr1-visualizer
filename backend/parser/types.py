"""Type definitions and data models for the LR(1) parser."""

from typing import List, Dict, Set, Optional, Union, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel


class SymbolType(Enum):
    """Types of grammar symbols."""
    TERMINAL = "terminal"
    NON_TERMINAL = "non_terminal"
    EPSILON = "epsilon"


class ActionType(Enum):
    """Types of parsing actions."""
    SHIFT = "shift"
    REDUCE = "reduce"
    ACCEPT = "accept"
    ERROR = "error"


@dataclass
class Symbol:
    """Represents a grammar symbol (terminal or non-terminal)."""
    name: str
    symbol_type: SymbolType
    
    def __hash__(self) -> int:
        return hash((self.name, self.symbol_type))
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Symbol):
            return False
        return self.name == other.name and self.symbol_type == other.symbol_type
    
    def __str__(self) -> str:
        return self.name


@dataclass
class Production:
    """Represents a grammar production rule."""
    lhs: Symbol  # Left-hand side (non-terminal)
    rhs: List[Symbol]  # Right-hand side (sequence of symbols)
    
    def __str__(self) -> str:
        rhs_str = " ".join(str(symbol) for symbol in self.rhs) if self.rhs else "ε"
        return f"{self.lhs} → {rhs_str}"


class ParsingAction(BaseModel):
    """Represents a parsing action (shift, reduce, accept, error)."""
    action_type: ActionType
    target: Optional[int] = None  # State number for shift, production index for reduce
    
    class Config:
        use_enum_values = True


class ParsingStep(BaseModel):
    """Represents one step in the parsing process."""
    step_number: int
    stack: List[Tuple[int, str]]  # (state, symbol)
    input_pointer: int
    current_token: Optional[str]
    action: ParsingAction
    explanation: str
    ast_nodes: List[Dict[str, Any]] = []


class GrammarError(BaseModel):
    """Represents a grammar validation error."""
    error_type: str
    message: str
    line_number: Optional[int] = None
    symbol: Optional[str] = None


class ConflictInfo(BaseModel):
    """Represents a parsing table conflict."""
    state: int
    symbol: str
    actions: List[ParsingAction]
    conflict_type: str  # "shift_reduce" or "reduce_reduce"


class ASTNode(BaseModel):
    """Represents a node in the Abstract Syntax Tree."""
    id: str
    symbol: str
    symbol_type: SymbolType
    children: List[str] = []  # IDs of child nodes
    parent: Optional[str] = None  # ID of parent node
    production_used: Optional[int] = None  # Index of production used to create this node
    
    class Config:
        use_enum_values = True
