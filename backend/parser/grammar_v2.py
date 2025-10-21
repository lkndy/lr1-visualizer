"""Refactored Grammar class with proper FIRST/FOLLOW computation and Lark integration."""

import logging
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

from parser.types import GrammarError, Production, Symbol, SymbolType

# Configure logger
logger = logging.getLogger(__name__)


@dataclass
class Grammar:
    """Represents a context-free grammar with LR(1) parsing capabilities."""

    productions: List[Production]
    start_symbol: Symbol
    terminals: Set[Symbol]
    non_terminals: Set[Symbol]
    end_of_input: str
    first_sets: Dict[Symbol, Set[Symbol]]
    follow_sets: Dict[Symbol, Set[Symbol]]

    def __init__(self, productions: List[Production], start_symbol: Symbol):
        """Initialize grammar with productions and start symbol."""
        logger.debug(f"Initializing Grammar with {len(productions)} productions")

        self.productions = productions
        self.start_symbol = start_symbol
        self.end_of_input = "$"
        self.first_sets = {}
        self.follow_sets = {}

        # Extract terminals and non-terminals
        self.non_terminals = set()
        self.terminals = set()

        # Add start symbol as non-terminal
        self.non_terminals.add(start_symbol)

        self._epsilon_symbol = Symbol("ε", SymbolType.EPSILON)
        self.end_of_input = "$"

        # Add end-of-input symbol as terminal
        eoi_symbol = Symbol("$", SymbolType.TERMINAL)
        self.terminals.add(eoi_symbol)

        # Extract symbols from productions
        has_epsilon_productions = False
        for production in productions:
            self.non_terminals.add(production.lhs)
            if len(production.rhs) == 0:  # Empty production (epsilon)
                has_epsilon_productions = True
            for symbol in production.rhs:
                if symbol.symbol_type == SymbolType.TERMINAL:
                    self.terminals.add(symbol)
                elif symbol.symbol_type == SymbolType.NON_TERMINAL:
                    self.non_terminals.add(symbol)
                elif symbol.symbol_type == SymbolType.EPSILON:
                    self.terminals.add(symbol)

        # Add epsilon symbol if there are epsilon productions
        if has_epsilon_productions:
            epsilon_symbol = Symbol("ε", SymbolType.EPSILON)
            self.terminals.add(epsilon_symbol)

        logger.debug(f"Grammar initialized: {len(self.terminals)} terminals, {len(self.non_terminals)} non-terminals")

    @classmethod
    def from_text(cls, grammar_text: str, start_symbol_name: str = "S") -> "Grammar":
        """Parse grammar from text using Lark parser."""
        logger.debug(f"Parsing grammar text with start symbol: {start_symbol_name}")

        # Import locally to avoid circular import
        from parser.lark_grammar_v2 import parse_grammar_with_lark_v2

        grammar, errors = parse_grammar_with_lark_v2(grammar_text, start_symbol_name)

        if errors:
            logger.warning(f"Grammar parsing had {len(errors)} errors")
            # Store errors for later retrieval
            grammar._parse_errors = errors
            # Raise exception for invalid grammars
            raise GrammarError(error_type="parse_error", message=f"Grammar parsing failed: {errors[0].message}")

        return grammar

    @classmethod
    def from_string(cls, grammar_text: str, start_symbol_name: str = "S") -> "Grammar":
        """Backward compatibility wrapper for from_text."""
        return cls.from_text(grammar_text, start_symbol_name)

    def first(self, symbols: Tuple[Symbol, ...]) -> Set[Symbol]:
        """Compute FIRST set for a sequence of symbols using memoization and cycle guards."""
        # Initialize caches/guards lazily
        if not hasattr(self, "_first_cache"):
            self._first_cache: Dict[Tuple, Set[Symbol]] = {}
        if not hasattr(self, "_first_nt_cache"):
            self._first_nt_cache: Dict[Symbol, Set[Symbol]] = {}
        if not hasattr(self, "_first_in_progress"):
            self._first_in_progress: Set[Symbol] = set()

        # Cache by the exact tuple of symbols
        if symbols in self._first_cache:
            return self._first_cache[symbols]

        if not symbols:
            result: Set[Symbol] = set()
            self._first_cache[symbols] = result
            return result

        result: Set[Symbol] = set()
        epsilon_symbol = self._epsilon_symbol
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

    def _first_of_non_terminal(self, symbol: Symbol) -> Set[Symbol]:
        """Compute FIRST set for a single non-terminal using memoization and cycle guards."""
        # Initialize caches/guards lazily
        if not hasattr(self, "_first_nt_cache"):
            self._first_nt_cache: Dict[Symbol, Set[Symbol]] = {}
        if not hasattr(self, "_first_in_progress"):
            self._first_in_progress: Set[Symbol] = set()

        # Cached?
        cached = self._first_nt_cache.get(symbol)
        if cached is not None:
            return cached

        # Cycle guard: if already exploring this non-terminal, break the cycle
        if symbol in self._first_in_progress:
            return set()

        self._first_in_progress.add(symbol)

        first_set: Set[Symbol] = set()
        epsilon_symbol = self._epsilon_symbol

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

    def _has_epsilon_production(self, symbol: Symbol) -> bool:
        """Check if a non-terminal has an epsilon production."""
        return any(not production.rhs for production in self.get_productions_for_symbol(symbol))

    def follow(self, symbol: Symbol) -> Set[Symbol]:
        """Compute FOLLOW set using memoization and cycle guards."""
        if not hasattr(self, "_follow_cache"):
            self._follow_cache: Dict[Symbol, Set[Symbol]] = {}
        if not hasattr(self, "_follow_in_progress"):
            self._follow_in_progress: Set[Symbol] = set()

        cached = self._follow_cache.get(symbol)
        if cached is not None:
            return cached

        # Cycle guard
        if symbol in self._follow_in_progress:
            return set()
        self._follow_in_progress.add(symbol)

        follow_set: Set[Symbol] = set()

        # For start symbol, add end marker
        if symbol == self.start_symbol or symbol.name == self.start_symbol.name.replace("'", ""):
            end_marker = Symbol("$", SymbolType.TERMINAL)
            follow_set.add(end_marker)

        epsilon_symbol = self._epsilon_symbol

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

    def validate(self) -> List[GrammarError]:
        """Validate the grammar and return any errors."""
        logger.debug("Validating grammar")
        errors = []

        # Check for undefined non-terminals (used in RHS but not defined as LHS)
        non_terminals_with_productions = {p.lhs.name for p in self.productions}
        used_symbols = set()
        for production in self.productions:
            for symbol in production.rhs:
                if symbol.symbol_type == SymbolType.NON_TERMINAL:
                    used_symbols.add(symbol.name)

        # Check if any used non-terminal doesn't have a production
        for symbol_name in used_symbols:
            if symbol_name not in non_terminals_with_productions:
                errors.append(
                    GrammarError(
                        error_type="undefined_non_terminal",
                        message=f"Non-terminal '{symbol_name}' is used but has no productions",
                        symbol=symbol_name,
                    ),
                )

        # Check for symbols that look like non-terminals (uppercase) but are classified as terminals
        # and have no productions - these are likely undefined non-terminals
        for symbol in self.terminals:
            if (
                symbol.name[0].isupper()  # Looks like a non-terminal
                and symbol.name not in non_terminals_with_productions  # No production defined
                and symbol.name not in ["$", "ε"]
            ):  # Not special symbols
                errors.append(
                    GrammarError(
                        error_type="undefined_non_terminal",
                        message=f"Symbol '{symbol.name}' appears to be a non-terminal but has no productions",
                        symbol=symbol.name,
                    ),
                )

        # Check that all non-terminals have productions
        epsilon_symbol = self._epsilon_symbol
        for non_terminal in self.non_terminals:
            if non_terminal in self.terminals or non_terminal == epsilon_symbol:
                continue  # Skip terminals mistakenly added
            if non_terminal.name not in non_terminals_with_productions:
                errors.append(
                    GrammarError(
                        error_type="undefined_non_terminal",
                        message=f"Non-terminal '{non_terminal.name}' has no productions",
                        symbol=non_terminal.name,
                    ),
                )

        # Check for unreachable symbols
        reachable = self._find_reachable_symbols()
        errors.extend(
            GrammarError(
                error_type="unreachable_non_terminal",
                message=f"Non-terminal '{non_terminal.name}' is unreachable from start symbol",
            )
            for non_terminal in self.non_terminals
            if non_terminal not in reachable
        )

        # Left recursion is acceptable for LR parsers; log informationally only
        left_recursive = self._find_left_recursive_symbols()
        if left_recursive:
            logger.info(f"Left recursion detected (allowed for LR parsers): {[s.name for s in left_recursive]}")

        return errors

    def _find_reachable_symbols(self) -> Set[Symbol]:
        """Find all symbols reachable from the start symbol."""
        reachable = {self.start_symbol}
        changed = True

        while changed:
            changed = False
            for production in self.productions:
                if production.lhs in reachable:
                    for symbol in production.rhs:
                        if symbol not in reachable:
                            reachable.add(symbol)
                            changed = True

        return reachable

    def _find_left_recursive_symbols(self) -> Set[Symbol]:
        """Find symbols with left recursion."""
        left_recursive = set()

        for production in self.productions:
            if production.rhs and production.rhs[0] == production.lhs:
                left_recursive.add(production.lhs)

        return left_recursive

    def get_productions_for_symbol(self, symbol: Symbol) -> List[Production]:
        """Get all productions with the given symbol as LHS."""
        return [p for p in self.productions if p.lhs == symbol]

    def is_terminal(self, symbol: Symbol) -> bool:
        """Check if symbol is a terminal."""
        return symbol.symbol_type == SymbolType.TERMINAL

    def is_non_terminal(self, symbol: Symbol) -> bool:
        """Check if symbol is a non-terminal."""
        return symbol.symbol_type == SymbolType.NON_TERMINAL

    def __eq__(self, other: object) -> bool:
        """Check equality with another grammar."""
        if not isinstance(other, Grammar):
            return False
        return self.productions == other.productions and self.start_symbol == other.start_symbol

    def __hash__(self) -> int:
        """Return hash of the grammar."""
        return hash((tuple(self.productions), self.start_symbol))

    def __str__(self) -> str:
        """Return string representation of the grammar."""
        lines = []
        current_lhs = None

        for production in self.productions:
            if production.lhs != current_lhs:
                if current_lhs is not None:
                    lines.append("")
                lines.append(f"{production.lhs.name} →")
                current_lhs = production.lhs
            else:
                lines.append("    |")

            rhs_str = " ".join(str(symbol) for symbol in production.rhs) if production.rhs else "ε"
            lines.append(f"    {rhs_str}")

        return "\n".join(lines)

    def __repr__(self) -> str:
        """Return string representation of the grammar."""
        return f"Grammar({len(self.productions)} productions, start={self.start_symbol.name})"
