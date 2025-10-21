"""LR(1) item generation with closure and goto operations."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from parser.types import Production, Symbol, SymbolType

if TYPE_CHECKING:
    from parser.grammar_v2 import Grammar


@dataclass(frozen=True)
class LR1Item:
    """Represents an LR(1) item: [A -> a·b, a] where · marks position and a is lookahead."""

    production: Production
    dot_position: int  # Position of the dot (0 means before first symbol)
    lookahead: Symbol  # Lookahead symbol (terminal)

    def __post_init__(self) -> None:
        """Validate item after initialization."""
        if self.dot_position < 0 or self.dot_position > len(self.production.rhs):
            msg = f"Invalid dot position {self.dot_position} for production {self.production}"
            raise ValueError(msg)

        if self.lookahead.symbol_type != SymbolType.TERMINAL:
            msg = f"Lookahead must be a terminal, got {self.lookahead}"
            raise ValueError(msg)

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
    def alpha(self) -> list[Symbol]:
        """Get the symbols before the dot (α in A -> α·β)."""
        return self.production.rhs[: self.dot_position]

    @property
    def beta(self) -> list[Symbol]:
        """Get the symbols after the dot (β in A -> α·β)."""
        return self.production.rhs[self.dot_position :]

    def advance_dot(self) -> "LR1Item":
        """Create a new item with the dot advanced by one position."""
        if self.is_complete:
            msg = "Cannot advance dot in complete item"
            raise ValueError(msg)

        return LR1Item(
            production=self.production,
            dot_position=self.dot_position + 1,
            lookahead=self.lookahead,
        )

    def __str__(self) -> str:
        """Return string representation of the item."""
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
        """Return string representation of the item."""
        return self.__str__()


class ItemSet:
    """Represents a set of LR(1) items with closure and goto operations."""

    def __init__(self, items: set[LR1Item]) -> None:
        """Initialize item set with a set of LR(1) items."""
        self.items = frozenset(items)  # Use frozenset for hashability

    @classmethod
    def from_initial_item(cls, item: LR1Item, grammar: "Grammar") -> "ItemSet":
        """Create item set starting with a single item and computing its closure."""
        items = {item}
        return cls(items).closure(grammar)

    def closure(self, grammar: "Grammar") -> "ItemSet":
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
                # If item is [A -> a·Bb, a] and B is a non-terminal
                symbol_after_dot = item.symbol_after_dot
                if symbol_after_dot and grammar.is_non_terminal(symbol_after_dot):
                    b_symbol = symbol_after_dot
                    beta = item.beta[1:]  # b (symbols after B)

                    # Compute FIRST(ba). Use tuple for caching compatibility
                    first_beta_a = grammar.first((*beta, item.lookahead))

                    # For each production B -> y
                    for production in grammar.get_productions_for_symbol(b_symbol):
                        # For each terminal b in FIRST(βa)
                        for terminal in first_beta_a:
                            if terminal.symbol_type == SymbolType.TERMINAL:
                                new_item = LR1Item(
                                    production=production,
                                    dot_position=0,
                                    lookahead=terminal,
                                )
                                if new_item not in items:
                                    new_items.add(new_item)
                                    changed = True

            items.update(new_items)

        return ItemSet(items)

    def goto(self, grammar: "Grammar", symbol: Symbol) -> "ItemSet":
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

    def get_reduce_items(self) -> list[LR1Item]:
        """Get all reduce items (complete items) in this set."""
        return [item for item in self.items if item.is_reduce_item]

    def get_shift_symbols(self) -> set[Symbol]:
        """Get all symbols that can be shifted from this item set."""
        symbols = set()
        for item in self.items:
            if not item.is_complete:
                symbol = item.symbol_after_dot
                if symbol:
                    symbols.add(symbol)
        return symbols

    def __eq__(self, other: object) -> bool:
        """Check if this item set is equal to another item set."""
        if not isinstance(other, ItemSet):
            return False
        return self.items == other.items

    def __hash__(self) -> int:
        """Return hash value of this item set."""
        return hash(self.items)

    def __str__(self) -> str:
        """Return string representation of the item set."""
        if not self.items:
            return "{}"

        items_str = ",\n  ".join(str(item) for item in sorted(self.items, key=str))
        return f"{{\n  {items_str}\n}}"

    def __repr__(self) -> str:
        """Return string representation of the item set."""
        return f"ItemSet({len(self.items)} items)"


# Add FIRST computation to Grammar class
# This function will be imported and used in grammar.py to avoid circular imports
def extend_grammar_with_first(grammar: "Grammar") -> None:
    """Extend Grammar class with FIRST computation."""
    _add_first_method(grammar)
    _add_first_of_non_terminal_method(grammar)
    _add_has_epsilon_production_method(grammar)


def _add_first_method(grammar: "Grammar") -> None:
    """Add first method to grammar."""

    def first(self: "Grammar", symbols: tuple) -> set[Symbol]:
        """Compute FIRST set for a sequence of symbols using memoization and cycle guards."""
        # Initialize caches/guards lazily on the grammar instance
        if not hasattr(self, "_first_cache"):
            self._first_cache: dict[tuple, set[Symbol]] = {}
        if not hasattr(self, "_first_nt_cache"):
            self._first_nt_cache: dict[Symbol, set[Symbol]] = {}
        if not hasattr(self, "_first_in_progress"):
            self._first_in_progress: set[Symbol] = set()

        # Cache by the exact tuple of symbols
        if symbols in self._first_cache:
            return self._first_cache[symbols]

        if not symbols:
            result: set[Symbol] = set()
            self._first_cache[symbols] = result
            return result

        result: set[Symbol] = set()
        epsilon_symbol = Symbol("ε", SymbolType.EPSILON)
        all_can_derive_epsilon = True

        for symbol in symbols:
            if symbol.symbol_type == SymbolType.TERMINAL:
                result.add(symbol)
                all_can_derive_epsilon = False
                break
            if symbol.symbol_type == SymbolType.EPSILON:
                # ε contributes only if all symbols derive ε; continue scanning
                continue

            # Non-terminal
            nt_first = self._first_of_non_terminal(symbol)
            # everything except ε is added directly
            for s in nt_first:
                if s.symbol_type != SymbolType.EPSILON:
                    result.add(s)

            # If this non-terminal cannot derive ε, we're done
            if epsilon_symbol not in nt_first and not self._has_epsilon_production(symbol):
                all_can_derive_epsilon = False
                break

        if all_can_derive_epsilon:
            result.add(epsilon_symbol)

        self._first_cache[symbols] = result
        return result

    grammar.first = first.__get__(grammar, grammar.__class__)


def _add_first_of_non_terminal_method(grammar: "Grammar") -> None:
    """Add _first_of_non_terminal method to grammar."""

    def _first_of_non_terminal(self: "Grammar", symbol: Symbol) -> set[Symbol]:
        """Compute FIRST set for a single non-terminal using memoization and cycle guards."""
        # Initialize caches/guards lazily on the grammar instance
        if not hasattr(self, "_first_nt_cache"):
            self._first_nt_cache: dict[Symbol, set[Symbol]] = {}
        if not hasattr(self, "_first_in_progress"):
            self._first_in_progress: set[Symbol] = set()

        # Cached?
        cached = self._first_nt_cache.get(symbol)
        if cached is not None:
            return cached

        # Cycle guard: if already exploring this non-terminal, break the cycle
        if symbol in self._first_in_progress:
            return set()

        self._first_in_progress.add(symbol)

        first_set: set[Symbol] = set()
        epsilon_symbol = Symbol("ε", SymbolType.EPSILON)

        for production in self.get_productions_for_symbol(symbol):
            if not production.rhs:  # ε production
                first_set.add(epsilon_symbol)
                continue

            seq_first = self.first(tuple(production.rhs))
            first_set.update(seq_first)

        # Done exploring this non-terminal
        self._first_in_progress.remove(symbol)

        # Memoize
        self._first_nt_cache[symbol] = first_set
        return first_set

    grammar._first_of_non_terminal = _first_of_non_terminal.__get__(  # noqa: SLF001
        grammar,
        grammar.__class__,
    )


def _add_has_epsilon_production_method(grammar: "Grammar") -> None:
    """Add _has_epsilon_production method to grammar."""

    def _has_epsilon_production(self: "Grammar", symbol: Symbol) -> bool:
        """Check if a non-terminal has an epsilon production."""
        return any(not production.rhs for production in self.get_productions_for_symbol(symbol))

    grammar._has_epsilon_production = _has_epsilon_production.__get__(  # noqa: SLF001
        grammar,
        grammar.__class__,
    )


def extend_grammar_with_follow(grammar: "Grammar") -> None:
    """Extend Grammar class with FOLLOW computation."""
    _add_follow_method(grammar)


def _add_follow_method(grammar: "Grammar") -> None:
    """Add follow method to grammar."""

    def follow(self: "Grammar", symbol: Symbol) -> set[Symbol]:
        """Compute FOLLOW set using memoization and cycle guards."""
        if not hasattr(self, "_follow_cache"):
            self._follow_cache: dict[Symbol, set[Symbol]] = {}
        if not hasattr(self, "_follow_in_progress"):
            self._follow_in_progress: set[Symbol] = set()

        cached = self._follow_cache.get(symbol)
        if cached is not None:
            return cached

        # Cycle guard
        if symbol in self._follow_in_progress:
            return set()
        self._follow_in_progress.add(symbol)

        follow_set: set[Symbol] = set()

        # For start symbol, add end marker
        if symbol == self.start_symbol or symbol.name == self.start_symbol.name.replace("'", ""):
            end_marker = Symbol("$", SymbolType.TERMINAL)
            follow_set.add(end_marker)

        epsilon_symbol = Symbol("ε", SymbolType.EPSILON)

        # Find all productions where symbol appears on RHS
        for production in self.productions:
            for i, rhs_symbol in enumerate(production.rhs):
                if rhs_symbol == symbol:
                    remaining_symbols = tuple(production.rhs[i + 1 :])

                    if remaining_symbols:
                        first_remaining = self.first(remaining_symbols)
                        first_without_epsilon = {s for s in first_remaining if s.symbol_type != SymbolType.EPSILON}
                        follow_set.update(first_without_epsilon)

                        if epsilon_symbol in first_remaining:
                            lhs_follow = self.follow(production.lhs)
                            follow_set.update(lhs_follow)
                    else:
                        lhs_follow = self.follow(production.lhs)
                        follow_set.update(lhs_follow)

        # Done exploring
        self._follow_in_progress.remove(symbol)

        # Memoize
        self._follow_cache[symbol] = follow_set
        return follow_set

    grammar.follow = follow.__get__(grammar, grammar.__class__)
