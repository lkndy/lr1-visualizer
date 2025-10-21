"""Clean Lark-based grammar parsing and conversion to internal Grammar format."""

import logging
from typing import Any, Dict, List, Set, Tuple

from lark import Lark, Token, Transformer
from lark.exceptions import LarkError
from typing import TYPE_CHECKING

# Import moved to avoid circular import
from parser.types import GrammarError, Production, Symbol, SymbolType

if TYPE_CHECKING:
    from parser.grammar_v2 import Grammar

# Configure logger
logger = logging.getLogger(__name__)


class GrammarParseError(Exception):
    """Raised when grammar parsing fails."""

    pass


class LarkGrammarTransformer(Transformer):
    """Transform Lark parse tree to internal Grammar format."""

    def __init__(self, start_symbol_name: str = "S"):
        """Initialize transformer with start symbol name."""
        self.start_symbol_name = start_symbol_name
        self.all_symbols: Dict[str, Symbol] = {}
        self.productions: List[Production] = []
        self.lhs_names: Set[str] = set()  # Track LHS symbols to distinguish from terminals
        self.errors: List[GrammarError] = []
        self.current_lhs: Symbol = None

        # Create start symbol
        self.start_symbol = Symbol(start_symbol_name, SymbolType.NON_TERMINAL)
        self.all_symbols[start_symbol_name] = self.start_symbol

    def start(self, rules: List[List[Production]]) -> Tuple["Grammar", List[GrammarError]]:
        """Transform start rule."""
        # Flatten the list of lists of productions
        all_productions = []
        for rule_productions in rules:
            all_productions.extend(rule_productions)

        # Add augmented production
        augmented_start = Symbol(f"{self.start_symbol_name}'", SymbolType.NON_TERMINAL)
        self.all_symbols[f"{self.start_symbol_name}'"] = augmented_start
        augmented_production = Production(augmented_start, [self.start_symbol])
        all_productions.insert(0, augmented_production)

        # Reclassify symbols now that we have all LHS names
        self._reclassify_symbols(all_productions)

        # Import locally to avoid circular import
        from parser.grammar_v2 import Grammar

        # Create grammar
        grammar = Grammar(all_productions, augmented_start)
        return grammar, self.errors

    def rule(self, items: List[Any]) -> List[Production]:
        """Transform grammar rule."""
        if len(items) != 2:
            self.errors.append(GrammarError(error_type="syntax_error", message="Invalid rule format"))
            return []

        lhs_token, alternatives = items
        lhs_name = lhs_token.value

        # Track LHS symbol name
        self.lhs_names.add(lhs_name)

        # Create or get LHS symbol
        if lhs_name not in self.all_symbols:
            self.all_symbols[lhs_name] = Symbol(lhs_name, SymbolType.NON_TERMINAL)
        lhs_symbol = self.all_symbols[lhs_name]

        # Create productions with the correct LHS
        productions = []
        for alternative in alternatives:
            # Create production even if alternative is empty (epsilon production)
            productions.append(Production(lhs_symbol, alternative))

        return productions

    def alternatives(self, items: List[List[Symbol]]) -> List[List[Symbol]]:
        """Transform alternatives (separated by |)."""
        return items

    def alternative(self, symbols: List[Symbol]) -> List[Symbol]:
        """Transform single alternative."""
        # Filter out None values (which represent epsilon)
        filtered_symbols = [s for s in symbols if s is not None]
        return filtered_symbols

    def symbol(self, items: List[Token]) -> Symbol:
        """Transform symbol token."""
        if not items:
            return self._create_epsilon_symbol()

        token = items[0]
        symbol_name = token.value
        token_type = token.type

        # Determine symbol type based on token type
        if token_type == "EPSILON":
            # For epsilon, we need to handle this specially in the alternative method
            # Return a special marker that will be filtered out
            return None
        elif token_type == "TERMINAL":
            # Remove quotes if present
            if symbol_name.startswith('"') and symbol_name.endswith('"'):
                symbol_name = symbol_name[1:-1]
            elif symbol_name.startswith("'") and symbol_name.endswith("'"):
                symbol_name = symbol_name[1:-1]
            return self._get_or_create_symbol(symbol_name, SymbolType.TERMINAL)
        elif token_type == "NONTERMINAL":
            # Initially treat all NONTERMINAL tokens as non-terminals
            # Will be reclassified later based on LHS names
            return self._get_or_create_symbol(symbol_name, SymbolType.NON_TERMINAL)
        else:
            # Fallback: treat as terminal
            return self._get_or_create_symbol(symbol_name, SymbolType.TERMINAL)

    def _create_epsilon_symbol(self) -> Symbol:
        """Create epsilon symbol."""
        if "ε" not in self.all_symbols:
            self.all_symbols["ε"] = Symbol("ε", SymbolType.EPSILON)
        return self.all_symbols["ε"]

    def _get_or_create_symbol(self, name: str, symbol_type: SymbolType) -> Symbol:
        """Get existing symbol or create new one."""
        if name in self.all_symbols:
            return self.all_symbols[name]

        symbol = Symbol(name, symbol_type)
        self.all_symbols[name] = symbol
        return symbol

    def _reclassify_symbols(self, productions: List[Production]) -> None:
        """Reclassify symbols based on LHS names collected during parsing."""
        for name, symbol in self.all_symbols.items():
            # Skip special symbols
            if name in [self.start_symbol_name, f"{self.start_symbol_name}'", "ε"]:
                continue

            # If symbol appears as LHS, it's a non-terminal
            if name in self.lhs_names:
                if symbol.symbol_type != SymbolType.NON_TERMINAL:
                    # Recreate symbol as non-terminal
                    new_symbol = Symbol(name, SymbolType.NON_TERMINAL)
                    self.all_symbols[name] = new_symbol
            else:
                # If symbol doesn't appear as LHS, it's a terminal
                if symbol.symbol_type != SymbolType.TERMINAL:
                    # Recreate symbol as terminal
                    new_symbol = Symbol(name, SymbolType.TERMINAL)
                    self.all_symbols[name] = new_symbol

        # Update symbols in productions
        for production in productions:
            # Update LHS symbol
            if production.lhs.name in self.all_symbols:
                production.lhs = self.all_symbols[production.lhs.name]

            # Update RHS symbols
            for i, symbol in enumerate(production.rhs):
                if symbol.name in self.all_symbols:
                    production.rhs[i] = self.all_symbols[symbol.name]


class LarkGrammarParserV2:
    """Clean Lark-based grammar parser with proper EBNF support."""

    def __init__(self):
        """Initialize the Lark grammar parser."""
        logger.debug("Initializing LarkGrammarParserV2")

        # EBNF grammar definition for parsing CFGs
        self.grammar_def = r"""
        start: rule+

        rule: NONTERMINAL (":" | "->") alternatives

        alternatives: alternative ("|" alternative)*

        alternative: symbol*

        symbol: NONTERMINAL | TERMINAL | EPSILON

        NONTERMINAL: /[A-Za-z][A-Za-z0-9_']*/
        TERMINAL: /"[^"]*"/ | /'[^']*'/ | /[+\-*\/(){}[\],;]/
        EPSILON: "ε" | "epsilon" | "eps"

        %import common.WS
        %ignore WS
        %import common.NEWLINE
        %ignore NEWLINE
        %ignore /#.*/
        """

        try:
            self.parser = Lark(self.grammar_def, start="start", parser="earley", lexer="dynamic")
            logger.debug("Lark parser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Lark parser: {e}")
            raise GrammarParseError(f"Failed to initialize parser: {e}")

    def parse_grammar(self, grammar_text: str, start_symbol_name: str = "S") -> Tuple["Grammar", List[GrammarError]]:
        """Parse grammar text and return Grammar object with errors."""
        logger.debug(f"Parsing grammar with start symbol: {start_symbol_name}")

        try:
            # Create new transformer for this parse
            transformer = LarkGrammarTransformer(start_symbol_name)

            # Parse the grammar
            tree = self.parser.parse(grammar_text)

            # Transform to Grammar using the transformer
            grammar, errors = transformer.transform(tree)

            logger.debug(f"Grammar parsed successfully: {len(grammar.productions)} productions")
            return grammar, errors

        except LarkError as e:
            logger.error(f"Lark parsing error: {e}")
            raise GrammarError(error_type="parse_error", message=f"Grammar parsing failed: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error during parsing: {e}")
            raise GrammarError(error_type="parse_error", message=f"Unexpected error: {str(e)}")

    def parse_bnf_grammar(self, grammar_text: str, start_symbol_name: str = "S") -> Tuple["Grammar", List[GrammarError]]:
        """Parse BNF-style grammar (S -> A | B format)."""
        logger.debug("Converting BNF to EBNF format")

        # Convert BNF to EBNF format
        ebnf_text = self._convert_bnf_to_ebnf(grammar_text)
        logger.debug(f"Converted BNF to EBNF: {ebnf_text[:200]}...")

        return self.parse_grammar(ebnf_text, start_symbol_name)

    def _convert_bnf_to_ebnf(self, bnf_text: str) -> str:
        """Convert BNF format to EBNF format."""
        lines = bnf_text.strip().split("\n")
        ebnf_lines = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Convert -> to :
            if "->" in line:
                line = line.replace("->", ":")
            elif "→" in line:
                line = line.replace("→", ":")

            ebnf_lines.append(line)

        return "\n".join(ebnf_lines)

    def validate_grammar_text(self, grammar_text: str) -> List[GrammarError]:
        """Validate grammar text without creating Grammar object."""
        try:
            # Try to parse without creating transformer
            self.parser.parse(grammar_text)
            return []
        except LarkError as e:
            return [GrammarError(error_type="syntax_error", message=f"Invalid grammar syntax: {str(e)}")]
        except Exception as e:
            return [GrammarError(error_type="parse_error", message=f"Validation error: {str(e)}")]


def parse_grammar_with_lark_v2(
    grammar_text: str, start_symbol_name: str = "S", format_type: str = "auto"
) -> Tuple["Grammar", List[GrammarError]]:
    """
    Parse grammar text using the new Lark-based parser.

    Args:
        grammar_text: Grammar text to parse
        start_symbol_name: Name of the start symbol
        format_type: Format type ("auto", "ebnf", "bnf")

    Returns:
        Tuple of (Grammar, List[GrammarError])
    """
    parser = LarkGrammarParserV2()

    if format_type == "auto":
        # Try EBNF first, then BNF
        try:
            return parser.parse_grammar(grammar_text, start_symbol_name)
        except GrammarError:
            # If EBNF fails, try BNF
            try:
                return parser.parse_bnf_grammar(grammar_text, start_symbol_name)
            except GrammarError:
                # If both fail, raise the original EBNF error
                raise
    elif format_type == "ebnf":
        return parser.parse_grammar(grammar_text, start_symbol_name)
    elif format_type == "bnf":
        return parser.parse_bnf_grammar(grammar_text, start_symbol_name)
    else:
        raise ValueError(f"Unknown format type: {format_type}")


# Convenience function for backward compatibility
def parse_grammar_with_lark(
    grammar_text: str, start_symbol_name: str = "S", is_lark_file: bool = False
) -> Tuple["Grammar", List[GrammarError]]:
    """Backward compatibility wrapper."""
    return parse_grammar_with_lark_v2(grammar_text, start_symbol_name, "auto")
