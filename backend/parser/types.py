"""Type definitions and data models for the LR(1) parser."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

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
        """Return hash of the symbol."""
        return hash((self.name, self.symbol_type))

    def __eq__(self, other: object) -> bool:
        """Check equality with another symbol."""
        if not isinstance(other, Symbol):
            return False
        return self.name == other.name and self.symbol_type == other.symbol_type

    def __str__(self) -> str:
        """Return string representation of the symbol."""
        return self.name


@dataclass
class Production:
    """Represents a grammar production rule."""

    lhs: Symbol  # Left-hand side (non-terminal)
    rhs: list[Symbol]  # Right-hand side (sequence of symbols)

    def __str__(self) -> str:
        """Return string representation of the production."""
        rhs_str = " ".join(str(symbol) for symbol in self.rhs) if self.rhs else "ε"
        return f"{self.lhs} → {rhs_str}"

    def __hash__(self) -> int:
        """Return hash of the production."""
        # Hash by immutable view of fields
        return hash((self.lhs, tuple(self.rhs)))


class ParsingAction(BaseModel):
    """Represents a parsing action (shift, reduce, accept, error)."""

    action_type: ActionType
    target: int | None = None  # State number for shift, production index for reduce

    class Config:
        """Pydantic configuration for ParsingAction."""

        use_enum_values = True


class ParsingStep(BaseModel):
    """Represents one step in the parsing process."""

    step_number: int
    stack: list[tuple[int, str]]  # (state, symbol)
    input_pointer: int
    current_token: str | None
    action: ParsingAction
    explanation: str
    ast_nodes: list[dict[str, Any]] = []


class GrammarError(BaseModel):
    """Represents a grammar validation error."""

    error_type: str
    message: str
    line_number: int | None = None
    symbol: str | None = None


class ConflictInfo(BaseModel):
    """Represents a parsing table conflict."""

    state: int
    symbol: str
    actions: list[ParsingAction]
    conflict_type: str  # "shift_reduce" or "reduce_reduce"


class ASTNode(BaseModel):
    """Represents a node in the Abstract Syntax Tree."""

    id: str
    symbol: str
    symbol_type: SymbolType
    children: list[str] = []  # IDs of child nodes
    parent: str | None = None  # ID of parent node
    production_used: int | None = None  # Index of production used to create this node

    class Config:
        """Pydantic configuration for ASTNode."""

        use_enum_values = True
