"""LR(1) item generation with closure and goto operations."""

from typing import List, Dict, Set, FrozenSet
from dataclasses import dataclass
from functools import lru_cache

from .types import Symbol, SymbolType, Production
from .grammar import Grammar


@dataclass(frozen=True)
class LR1Item:
    """Represents an LR(1) item: [A -> α·β, a] where · marks position and a is lookahead."""
    
    production: Production
    dot_position: int  # Position of the dot (0 means before first symbol)
    lookahead: Symbol  # Lookahead symbol (terminal)
    
    def __post_init__(self):
        """Validate item after initialization."""
        if self.dot_position < 0 or self.dot_position > len(self.production.rhs):
            raise ValueError(f"Invalid dot position {self.dot_position} for production {self.production}")
        
        if self.lookahead.symbol_type != SymbolType.TERMINAL:
            raise ValueError(f"Lookahead must be a terminal, got {self.lookahead}")
    
    @property
    def symbol_after_dot(self) -> Symbol:
        """Get the symbol immediately after the dot."""
        if self.dot_position >= len(self.production.rhs):
            return None
        return self.production.rhs[self.dot_position]
    
    @property
    def is_complete(self) -> bool:
        """Check if this is a complete item (dot at the end)."""
        return self.dot_position >= len(self.production.rhs)
    
    @property
    def is_reduce_item(self) -> bool:
        """Check if this is a reduce item (complete item)."""
        return self.is_complete
    
    @property
    def alpha(self) -> List[Symbol]:
        """Get the symbols before the dot (α in A -> α·β)."""
        return self.production.rhs[:self.dot_position]
    
    @property
    def beta(self) -> List[Symbol]:
        """Get the symbols after the dot (β in A -> α·β)."""
        return self.production.rhs[self.dot_position:]
    
    def advance_dot(self) -> 'LR1Item':
        """Create a new item with the dot advanced by one position."""
        if self.is_complete:
            raise ValueError("Cannot advance dot in complete item")
        
        return LR1Item(
            production=self.production,
            dot_position=self.dot_position + 1,
            lookahead=self.lookahead
        )
    
    def __str__(self) -> str:
        """String representation of the item."""
        rhs = self.production.rhs
        if not rhs:
            rhs_str = "·ε"
        else:
            rhs_list = []
            for i, symbol in enumerate(rhs):
                if i == self.dot_position:
                    rhs_list.append("·")
                rhs_list.append(str(symbol))
            if self.dot_position == len(rhs):
                rhs_list.append("·")
            rhs_str = " ".join(rhs_list)
        
        return f"[{self.production.lhs} → {rhs_str}, {self.lookahead}]"
    
    def __repr__(self) -> str:
        return self.__str__()


class ItemSet:
    """Represents a set of LR(1) items with closure and goto operations."""
    
    def __init__(self, items: Set[LR1Item]):
        """Initialize item set with a set of LR(1) items."""
        self.items = frozenset(items)  # Use frozenset for hashability
    
    @classmethod
    def from_initial_item(cls, item: LR1Item, grammar: Grammar) -> 'ItemSet':
        """Create item set starting with a single item and computing its closure."""
        items = {item}
        return cls(items).closure(grammar)
    
    def closure(self, grammar: Grammar) -> 'ItemSet':
        """Compute the closure of this item set.
        
        The closure of a set of items is the set of all items that can be derived
        from the items in the set by repeatedly applying the closure rule:
        If [A -> α·Bβ, a] is in the closure and B -> γ is a production,
        then [B -> ·γ, b] is in the closure for all terminals b in FIRST(βa).
        """
        items = set(self.items)
        changed = True
        
        while changed:
            changed = False
            new_items = set()
            
            for item in items:
                # If item is [A -> α·Bβ, a] and B is a non-terminal
                symbol_after_dot = item.symbol_after_dot
                if symbol_after_dot and grammar.is_non_terminal(symbol_after_dot):
                    B = symbol_after_dot
                    beta = item.beta[1:]  # β (symbols after B)
                    
                    # Compute FIRST(βa)
                    first_beta_a = grammar.first(beta + [item.lookahead])
                    
                    # For each production B -> γ
                    for production in grammar.get_productions_for_symbol(B):
                        # For each terminal b in FIRST(βa)
                        for terminal in first_beta_a:
                            if terminal.symbol_type == SymbolType.TERMINAL:
                                new_item = LR1Item(
                                    production=production,
                                    dot_position=0,
                                    lookahead=terminal
                                )
                                if new_item not in items:
                                    new_items.add(new_item)
                                    changed = True
            
            items.update(new_items)
        
        return ItemSet(items)
    
    def goto(self, grammar: Grammar, symbol: Symbol) -> 'ItemSet':
        """Compute GOTO(I, X) where I is this item set and X is a symbol.
        
        GOTO(I, X) = CLOSURE({[A -> αX·β, a] | [A -> α·Xβ, a] ∈ I})
        """
        goto_items = set()
        
        for item in self.items:
            if item.symbol_after_dot == symbol:
                advanced_item = item.advance_dot()
                goto_items.add(advanced_item)
        
        if not goto_items:
            return None
        
        return ItemSet(goto_items).closure(grammar)
    
    def get_reduce_items(self) -> List[LR1Item]:
        """Get all reduce items (complete items) in this set."""
        return [item for item in self.items if item.is_reduce_item]
    
    def get_shift_symbols(self) -> Set[Symbol]:
        """Get all symbols that can be shifted from this item set."""
        symbols = set()
        for item in self.items:
            if not item.is_complete:
                symbol = item.symbol_after_dot
                if symbol:
                    symbols.add(symbol)
        return symbols
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, ItemSet):
            return False
        return self.items == other.items
    
    def __hash__(self) -> int:
        return hash(self.items)
    
    def __str__(self) -> str:
        """String representation of the item set."""
        if not self.items:
            return "{}"
        
        items_str = ",\n  ".join(str(item) for item in sorted(self.items, key=str))
        return f"{{\n  {items_str}\n}}"
    
    def __repr__(self) -> str:
        return f"ItemSet({len(self.items)} items)"


# Add FIRST computation to Grammar class
def _extend_grammar_with_first(grammar: Grammar):
    """Extend Grammar class with FIRST computation."""
    
    @lru_cache(maxsize=None)
    def first(self, symbols: tuple) -> Set[Symbol]:
        """Compute FIRST set for a sequence of symbols.
        
        FIRST(α) is the set of terminals that can begin strings derived from α.
        """
        if not symbols:
            return set()
        
        first_set = set()
        
        for i, symbol in enumerate(symbols):
            if symbol.symbol_type == SymbolType.TERMINAL:
                first_set.add(symbol)
                break  # Terminal can't derive empty string
            elif symbol.symbol_type == SymbolType.EPSILON:
                continue  # Skip epsilon
            else:  # Non-terminal
                # Add FIRST of this non-terminal
                symbol_first = self._first_of_non_terminal(symbol)
                first_set.update(symbol_first)
                
                # If epsilon is in FIRST(symbol), continue to next symbol
                if not self._has_epsilon_production(symbol):
                    break
        
        return first_set
    
    def _first_of_non_terminal(self, symbol: Symbol) -> Set[Symbol]:
        """Compute FIRST set for a single non-terminal."""
        first_set = set()
        
        for production in self.get_productions_for_symbol(symbol):
            if not production.rhs:  # ε production
                epsilon = Symbol("ε", SymbolType.EPSILON)
                first_set.add(epsilon)
            else:
                prod_first = self.first(tuple(production.rhs))
                first_set.update(prod_first)
        
        return first_set
    
    def _has_epsilon_production(self, symbol: Symbol) -> bool:
        """Check if a non-terminal has an epsilon production."""
        for production in self.get_productions_for_symbol(symbol):
            if not production.rhs:
                return True
        return False
    
    # Add methods to Grammar class
    grammar.first = first.__get__(grammar, Grammar)
    grammar._first_of_non_terminal = _first_of_non_terminal.__get__(grammar, Grammar)
    grammar._has_epsilon_production = _has_epsilon_production.__get__(grammar, Grammar)
