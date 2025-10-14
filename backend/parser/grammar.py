"""Grammar definition, parsing, and validation."""

from dataclasses import dataclass

from parser.types import GrammarError, Production, Symbol, SymbolType
from utils.debug import debug_log, debug_timer, info_log


@dataclass
class Grammar:
    """Represents a context-free grammar with LR(1) parsing capabilities."""

    productions: list[Production]
    start_symbol: Symbol
    terminals: set[Symbol]
    non_terminals: set[Symbol]
    end_of_input: str
    first_sets: dict[str, set[str]]
    follow_sets: dict[str, set[str]]

    def __init__(self, productions: list[Production], start_symbol: Symbol) -> None:
        """Initialize grammar with productions and start symbol."""
        debug_log(
            "🔧 Initializing Grammar",
            {"num_productions": len(productions), "start_symbol": str(start_symbol)},
        )

        self.productions = productions
        self.start_symbol = start_symbol
        self.end_of_input = "$"  # End-of-input marker
        self.first_sets = {}
        self.follow_sets = {}

        # Extract terminals and non-terminals
        self.non_terminals = set()
        self.terminals = set()

        # Add start symbol as non-terminal
        self.non_terminals.add(start_symbol)

        self._epsilon_symbol = Symbol("ε", SymbolType.EPSILON)

        # Extract symbols from productions
        for production in productions:
            self.non_terminals.add(production.lhs)
            for symbol in production.rhs:
                if symbol.symbol_type == SymbolType.TERMINAL:
                    self.terminals.add(symbol)
                elif symbol.symbol_type == SymbolType.NON_TERMINAL:
                    self.non_terminals.add(symbol)

        debug_log(
            "✅ Grammar initialized",
            {
                "terminals": [str(t) for t in self.terminals],
                "non_terminals": [str(nt) for nt in self.non_terminals],
            },
        )

    @classmethod
    def from_string(cls, grammar_text: str, start_symbol_name: str = "S") -> "Grammar":
        """Parse grammar from text format.

        Expected format:
        S -> A B | C
        A -> a | ε
        B -> b
        """
        productions = []
        errors = []

        # Create augmented start symbol
        start_symbol = Symbol(start_symbol_name, SymbolType.NON_TERMINAL)
        augmented_start = Symbol(f"{start_symbol_name}'", SymbolType.NON_TERMINAL)

        lines = grammar_text.strip().split("\n")
        all_symbols: dict[str, Symbol] = {start_symbol_name: start_symbol}

        # First pass: collect all LHS symbols as non-terminals
        lhs_names = cls._collect_lhs_symbols(lines, all_symbols)

        for line_num, raw_line in enumerate(lines, 1):
            line = raw_line.strip()
            if not line or line.startswith("#"):  # Skip empty lines and comments
                continue

            try:
                production_errors, new_productions = cls._parse_production_line(
                    line,
                    line_num,
                    lhs_names,
                    all_symbols,
                )
                errors.extend(production_errors)
                productions.extend(new_productions)

            except (ValueError, IndexError, KeyError) as e:
                errors.append(
                    GrammarError(
                        error_type="parse_error",
                        message=f"Error parsing line: {e!s}",
                        line_number=line_num,
                    ),
                )

        # Add augmented production
        productions.insert(0, Production(augmented_start, [start_symbol]))

        grammar = cls(productions, augmented_start)
        grammar._parse_errors = errors

        return grammar

    @staticmethod
    def _tokenize_rhs(rhs: str) -> list[str]:
        """Tokenize the right-hand side of a production."""
        # Simple tokenization - split on whitespace, handle parentheses
        tokens = []
        current_token = ""

        for char in rhs:
            if char.isspace():
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            elif char in "()[]{}":
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
                tokens.append(char)
            else:
                current_token += char

        if current_token:
            tokens.append(current_token)

        return tokens

    @debug_timer
    def validate(self) -> list[GrammarError]:
        """Validate the grammar and return any errors."""
        debug_log("🔍 Validating grammar")
        errors = []

        # Check for undefined symbols
        defined_symbols = set()
        for production in self.productions:
            defined_symbols.add(production.lhs)
            defined_symbols.update(production.rhs)

        # Check that all non-terminals have productions
        non_terminals_with_productions = {p.lhs for p in self.productions}
        epsilon_symbol = self._epsilon_symbol
        for non_terminal in self.non_terminals:
            if non_terminal in self.terminals or non_terminal == epsilon_symbol:
                continue  # Skip terminals mistakenly added
            if non_terminal not in non_terminals_with_productions:
                errors.append(
                    GrammarError(
                        error_type="undefined_non_terminal",
                        message=(f"Non-terminal '{non_terminal.name}' has no productions"),
                    ),
                )

        # Check for unreachable symbols
        reachable = self._find_reachable_symbols()
        errors.extend(
            GrammarError(
                error_type="unreachable_non_terminal",
                message=(f"Non-terminal '{non_terminal.name}' is unreachable from start symbol"),
            )
            for non_terminal in self.non_terminals
            if non_terminal not in reachable
        )

        # Left recursion is acceptable for LR parsers; log informationally only
        left_recursive = self._find_left_recursive_symbols()
        if left_recursive:
            info_log(
                "i Left recursion detected (allowed for LR parsers)",
                {"symbols": [s.name for s in left_recursive]},
            )

        return errors

    def _find_reachable_symbols(self) -> set[Symbol]:
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

    def _find_left_recursive_symbols(self) -> set[Symbol]:
        """Find symbols with left recursion."""
        left_recursive = set()

        for production in self.productions:
            if production.rhs and production.rhs[0] == production.lhs:
                left_recursive.add(production.lhs)

        return left_recursive

    def get_productions_for_symbol(self, symbol: Symbol) -> list[Production]:
        """Get all productions with the given symbol as LHS."""
        return [p for p in self.productions if p.lhs == symbol]

    def is_terminal(self, symbol: Symbol) -> bool:
        """Check if symbol is a terminal."""
        return symbol.symbol_type == SymbolType.TERMINAL

    def is_non_terminal(self, symbol: Symbol) -> bool:
        """Check if symbol is a non-terminal."""
        return symbol.symbol_type == SymbolType.NON_TERMINAL

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

    @classmethod
    def _collect_lhs_symbols(cls, lines: list[str], all_symbols: dict[str, Symbol]) -> set[str]:
        """Collect all LHS symbols as non-terminals in first pass."""
        lhs_names: set[str] = set()
        for raw_line in lines:
            raw = raw_line.strip()
            if not raw or raw.startswith("#"):
                continue
            if "->" not in raw and "→" not in raw:
                continue
            sep = "->" if "->" in raw else "→"
            lhs_candidate = raw.split(sep, 1)[0].strip()
            if lhs_candidate:
                lhs_names.add(lhs_candidate)
                if lhs_candidate not in all_symbols:
                    all_symbols[lhs_candidate] = Symbol(
                        lhs_candidate,
                        SymbolType.NON_TERMINAL,
                    )
        return lhs_names

    @classmethod
    def _parse_production_line(
        cls,
        line: str,
        line_num: int,
        lhs_names: set[str],
        all_symbols: dict[str, Symbol],
    ) -> tuple[list[GrammarError], list[Production]]:
        """Parse a single production line."""
        errors = []
        productions = []

        # Validate line format
        if "->" not in line and "→" not in line:
            errors.append(
                GrammarError(
                    error_type="syntax_error",
                    message="Missing '->' or '→' in production",
                    line_number=line_num,
                ),
            )
            return errors, productions

        # Split lhs and rhs
        separator = "->" if "->" in line else "→"
        lhs_str, rhs_str = line.split(separator, 1)
        lhs_str = lhs_str.strip()
        rhs_str = rhs_str.strip()

        if not lhs_str:
            errors.append(
                GrammarError(
                    error_type="syntax_error",
                    message="Empty left-hand side",
                    line_number=line_num,
                ),
            )
            return errors, productions

        # Create or get LHS symbol
        if lhs_str not in all_symbols:
            all_symbols[lhs_str] = Symbol(lhs_str, SymbolType.NON_TERMINAL)
        lhs = all_symbols[lhs_str]

        # Parse RHS alternatives
        alternatives = [alt.strip() for alt in rhs_str.split("|")]
        for alt in alternatives:
            new_productions = cls._parse_alternative(alt, lhs, lhs_names, all_symbols)
            productions.extend(new_productions)

        return errors, productions

    @classmethod
    def _parse_alternative(
        cls,
        alt: str,
        lhs: Symbol,
        lhs_names: set[str],
        all_symbols: dict[str, Symbol],
    ) -> list[Production]:
        """Parse a single alternative from RHS."""
        productions = []

        # Empty alternative (epsilon)
        if not alt:
            productions.append(Production(lhs, []))
            return productions

        # Explicit epsilon token
        if alt == "ε" or alt.lower() in ("epsilon", "eps"):
            productions.append(Production(lhs, []))
            return productions

        # Parse tokens in alternative
        rhs_symbols = []
        tokens = cls._tokenize_rhs(alt)

        for token_name in tokens:
            # Skip explicit epsilon within tokenized RHS
            if token_name == "ε" or token_name.lower() in ("epsilon", "eps"):
                continue

            symbol = cls._get_or_create_symbol(token_name, lhs_names, all_symbols)
            rhs_symbols.append(symbol)

        productions.append(Production(lhs, rhs_symbols))
        return productions

    @classmethod
    def _get_or_create_symbol(
        cls,
        token_name: str,
        lhs_names: set[str],
        all_symbols: dict[str, Symbol],
    ) -> Symbol:
        """Get existing symbol or create new one with appropriate type."""
        if token_name in all_symbols:
            return all_symbols[token_name]

        # Determine if terminal or non-terminal
        symbol_type = SymbolType.NON_TERMINAL if token_name in lhs_names else cls._classify_symbol_type(token_name)

        symbol = Symbol(token_name, symbol_type)
        all_symbols[token_name] = symbol
        return symbol

    @classmethod
    def _classify_symbol_type(cls, token_name: str) -> SymbolType:
        """Classify a token as terminal or non-terminal based on heuristics."""
        # Common terminal keywords
        terminal_keywords = {
            "id",
            "num",
            "string",
            "true",
            "false",
            "null",
            "number",
        }

        # Common operators and punctuation
        operators = {
            "(",
            ")",
            "[",
            "]",
            "{",
            "}",
            "+",
            "-",
            "*",
            "/",
            "=",
            "<",
            ">",
            "<=",
            ">=",
            "==",
            "!=",
            "&&",
            "||",
            "!",
            "&",
            "|",
            "^",
            "~",
            "<<",
            ">>",
            "++",
            "--",
            "+=",
            "-=",
            "*=",
            "/=",
            "%=",
            "^=",
            "&=",
            "|=",
            "<<=",
            ">>=",
            "=>",
            "->",
            "::",
            ".",
            ",",
            ";",
            ":",
            "?",
            "??",
            "??=",
            "...",
            "..",
            "..=",
        }

        # Heuristic rules:
        # - Lowercase words default to terminal
        # - Known terminal keywords
        # - Operators and punctuation
        # - Non-alphanumeric strings
        if (
            token_name.islower()
            or token_name in terminal_keywords
            or token_name in operators
            or not token_name.replace("_", "").replace("-", "").isalnum()
        ):
            return SymbolType.TERMINAL
        return SymbolType.NON_TERMINAL
