"""Lark-based grammar parsing and conversion to internal Grammar format."""

import os
import re
from typing import Any

from lark import Lark, Token, Tree
from lark.exceptions import LarkError

from parser.grammar import Grammar
from parser.types import GrammarError, Production, Symbol, SymbolType
from utils.debug import debug_log, error_log

# Debug flag
DEBUG_GRAMMAR = os.getenv("DEBUG", "false").lower() == "true"


class LarkGrammarParser:
    """Parse grammars using Lark and convert to internal format."""

    def __init__(self) -> None:
        """Initialize the Lark grammar parser."""
        if DEBUG_GRAMMAR:
            debug_log("🔧 Initializing LarkGrammarParser")

        # Grammar definition: accept identifiers (lower/upper), quoted strings, and operator tokens
        self.lark_grammar = r"""
        start: grammar_rule+
        
        grammar_rule: IDENT ARROW rhs_alternatives
        
        rhs_alternatives: rhs_alternative (VBAR rhs_alternative)*
        rhs_alternative: symbol*
        
        symbol: IDENT | STRING | OP | EPSILON
        
        IDENT: /[A-Za-z_][A-Za-z0-9_]*/
        STRING: ESCAPED_STRING
        ARROW.10: "->"
        VBAR.10: "|"
        OP.-1: /[+\-*/(){}\[\].,;:<>!=&|]+/
        EPSILON: "ε" | "epsilon" | "eps"
        
        %import common.ESCAPED_STRING
        %import common.WS
        %ignore WS
        %ignore /#[^\n]*/
        """

        if DEBUG_GRAMMAR:
            debug_log("🔧 Lark grammar definition", {"grammar": self.lark_grammar})

        try:
            self.parser = Lark(self.lark_grammar, start="start", lexer="dynamic_complete")
            if DEBUG_GRAMMAR:
                debug_log("✅ Lark parser initialized successfully")
        except Exception as e:
            error_log("💥 Failed to initialize Lark parser", {"error": str(e), "grammar": self.lark_grammar})
            raise

    def parse_text_grammar(self, grammar_text: str, start_symbol_name: str = "S") -> tuple[Grammar, list[GrammarError]]:
        """Parse text-based grammar and convert to internal format."""
        if DEBUG_GRAMMAR:
            debug_log(
                "🔧 Starting grammar parsing",
                {
                    "start_symbol": start_symbol_name,
                    "grammar_length": len(grammar_text),
                    "grammar_preview": grammar_text[:200],
                    "grammar_full": grammar_text,
                    "grammar_lines": grammar_text.split("\n"),
                    "has_newlines": "\n" in grammar_text,
                    "grammar_bytes": grammar_text.encode("utf-8"),
                },
            )

        errors = []

        try:
            if DEBUG_GRAMMAR:
                debug_log("🔧 Attempting direct Lark parsing", {"grammar_text": grammar_text})
            # First, try to parse as Lark grammar directly
            tree = self.parser.parse(grammar_text)
            if DEBUG_GRAMMAR:
                debug_log("✅ Direct Lark parsing succeeded", {"tree": str(tree)})
            return self._convert_lark_tree_to_grammar(tree, start_symbol_name, errors)

        except LarkError as e:
            if DEBUG_GRAMMAR:
                debug_log(
                    "⚠️ Direct Lark parsing failed, trying custom format",
                    {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "grammar_text": grammar_text,
                        "grammar_lines": grammar_text.split("\n"),
                    },
                )

            # If that fails, try custom format conversion
            try:
                if DEBUG_GRAMMAR:
                    debug_log("🔄 Starting custom format conversion", {"input": grammar_text})
                converted_text = self._convert_custom_to_lark_format(grammar_text)
                if DEBUG_GRAMMAR:
                    debug_log(
                        "🔄 Custom conversion completed",
                        {
                            "original": grammar_text,
                            "converted": converted_text,
                            "conversion_successful": converted_text != grammar_text,
                        },
                    )

                if DEBUG_GRAMMAR:
                    debug_log("🔧 Attempting to parse converted grammar", {"converted_text": converted_text})
                tree = self.parser.parse(converted_text)
                if DEBUG_GRAMMAR:
                    debug_log("✅ Converted grammar parsing succeeded", {"tree": str(tree)})
                return self._convert_lark_tree_to_grammar(tree, start_symbol_name, errors)

            except Exception as conv_error:
                if DEBUG_GRAMMAR:
                    debug_log(
                        "💥 Custom conversion and parsing failed",
                        {
                            "conversion_error": str(conv_error),
                            "conversion_error_type": type(conv_error).__name__,
                            "original_text": grammar_text,
                            "converted_text": converted_text if "converted_text" in locals() else "N/A",
                            "lark_grammar_def": self.lark_grammar,
                        },
                    )
                error_log(
                    "💥 Failed to convert custom grammar format",
                    {
                        "error": str(conv_error),
                        "original_text": grammar_text,
                        "converted_text": converted_text if "converted_text" in locals() else "N/A",
                    },
                )
                errors.append(GrammarError(error_type="parse_error", message=f"Could not parse grammar: {str(conv_error)}"))
                # Fallback to original parsing
                if DEBUG_GRAMMAR:
                    debug_log("🔄 Attempting fallback to Grammar.from_string", {"grammar_text": grammar_text})
                return Grammar.from_string(grammar_text, start_symbol_name)

    def parse_lark_file(self, lark_content: str, start_symbol_name: str = "S") -> tuple[Grammar, list[GrammarError]]:
        """Parse .lark file format and convert to internal format."""
        debug_log("🔧 Parsing .lark file with Lark", {"start_symbol": start_symbol_name})

        errors = []

        try:
            # Parse the .lark file
            tree = self.parser.parse(lark_content)
            return self._convert_lark_tree_to_grammar(tree, start_symbol_name, errors)

        except LarkError as e:
            error_log("💥 Failed to parse .lark file", {"error": str(e)})
            errors.append(GrammarError(error_type="parse_error", message=f"Could not parse .lark file: {str(e)}"))
            # Return empty grammar on error
            start_symbol = Symbol(start_symbol_name, SymbolType.NON_TERMINAL)
            return Grammar([], start_symbol)

    def _convert_custom_to_lark_format(self, grammar_text: str) -> str:
        """Convert custom grammar format to Lark format."""
        # First, try to split by newlines
        lines = grammar_text.strip().split("\n")

        # If we only have one line, try to split by patterns that indicate rule boundaries
        if len(lines) == 1:
            single_line = lines[0].strip()
            if DEBUG_GRAMMAR:
                debug_log("🔍 Single line grammar detected", {"line": single_line})

            # Split by patterns like " T ->" or " F ->" (space + uppercase + arrow)
            # This handles cases where rules are concatenated without newlines
            rule_pattern = r"\s+([A-Z][A-Z0-9_]*)\s*->"
            parts = re.split(rule_pattern, single_line)
            if DEBUG_GRAMMAR:
                debug_log("🔍 Rule splitting result", {"parts": parts, "num_parts": len(parts), "pattern": rule_pattern})

            if len(parts) > 1:
                # Reconstruct the rules
                lines = []
                for i in range(1, len(parts), 2):
                    if i + 1 < len(parts):
                        lhs = parts[i]
                        rhs = parts[i + 1].strip()
                        lines.append(f"{lhs} -> {rhs}")
                        if DEBUG_GRAMMAR:
                            debug_log("🔍 Reconstructed rule", {"lhs": lhs, "rhs": rhs})
            elif DEBUG_GRAMMAR:
                debug_log("🔍 No rule splitting occurred", {"single_line": single_line, "parts": parts})

        converted_lines = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Handle different arrow types
            if "->" in line:
                lhs, rhs = line.split("->", 1)
            elif "→" in line:
                lhs, rhs = line.split("→", 1)
            else:
                continue

            lhs = lhs.strip()
            rhs = rhs.strip()

            # Convert RHS symbols to proper format
            rhs_symbols = []
            for part in rhs.split("|"):
                part = part.strip()
                symbols = []

                # Simple tokenization
                tokens = re.findall(r"\S+", part)
                for token in tokens:
                    if token in ["ε", "epsilon", "eps"]:
                        symbols.append("ε")
                    elif token.isupper() or (token.startswith('"') and token.endswith('"')):
                        symbols.append(token)
                    elif token.islower() or not token.replace("_", "").replace("-", "").isalnum():
                        # Treat as terminal
                        symbols.append(f'"{token}"')
                    else:
                        # Default to non-terminal
                        symbols.append(token)

                rhs_symbols.append(" ".join(symbols))

            converted_line = f"{lhs} -> {' | '.join(rhs_symbols)}"
            converted_lines.append(converted_line)

        return "\n".join(converted_lines)

    def _convert_lark_tree_to_grammar(
        self, tree: Tree, start_symbol_name: str, errors: list[GrammarError]
    ) -> tuple[Grammar, list[GrammarError]]:
        """Convert Lark parse tree to internal Grammar format."""
        debug_log("🔄 Converting Lark tree to Grammar")

        productions = []
        all_symbols: dict[str, Symbol] = {}

        # Create start symbol
        start_symbol = Symbol(start_symbol_name, SymbolType.NON_TERMINAL)
        all_symbols[start_symbol_name] = start_symbol

        # Process grammar rules
        for rule in tree.children:
            if rule.data == "grammar_rule":
                lhs_token = rule.children[0]
                rhs_alternatives = rule.children[1]

                lhs_name = lhs_token.value
                if lhs_name not in all_symbols:
                    all_symbols[lhs_name] = Symbol(lhs_name, SymbolType.NON_TERMINAL)
                lhs = all_symbols[lhs_name]

                # Process each alternative
                for alternative in rhs_alternatives.children:
                    if alternative.data == "rhs_alternative":
                        rhs_symbols = []

                        for symbol_node in alternative.children:
                            if symbol_node.data == "symbol":
                                symbol_token = symbol_node.children[0]
                                symbol_name = symbol_token.value

                                # Determine symbol type based on token type and known LHS symbols
                                token_type = getattr(symbol_token, "type", "")
                                if token_type in {"EPSILON"}:
                                    symbol_type = SymbolType.EPSILON
                                elif token_type in {"STRING", "OP", "TERMINAL"}:
                                    # Terminal tokens; strip quotes for STRING
                                    symbol_type = SymbolType.TERMINAL
                                    if symbol_name.startswith('"') and symbol_name.endswith('"'):
                                        symbol_name = symbol_name[1:-1]
                                    elif symbol_name.startswith("'") and symbol_name.endswith("'"):
                                        symbol_name = symbol_name[1:-1]
                                elif token_type in {"IDENT", "NONTERMINAL"}:
                                    # IDENT may be a non-terminal if it was introduced as an LHS earlier
                                    if (
                                        symbol_name in all_symbols
                                        and all_symbols[symbol_name].symbol_type == SymbolType.NON_TERMINAL
                                    ):
                                        symbol_type = SymbolType.NON_TERMINAL
                                    else:
                                        symbol_type = SymbolType.TERMINAL
                                else:
                                    # Fallback to terminal
                                    symbol_type = SymbolType.TERMINAL

                                if symbol_name not in all_symbols:
                                    all_symbols[symbol_name] = Symbol(symbol_name, symbol_type)
                                rhs_symbols.append(all_symbols[symbol_name])

                        # Create production
                        production = Production(lhs, rhs_symbols)
                        productions.append(production)

        # Create augmented grammar
        augmented_start = Symbol(f"{start_symbol_name}'", SymbolType.NON_TERMINAL)
        productions.insert(0, Production(augmented_start, [start_symbol]))

        # Create grammar
        grammar = Grammar(productions, augmented_start)

        debug_log("✅ Grammar converted successfully", {"num_productions": len(productions), "num_symbols": len(all_symbols)})

        return grammar, errors


def parse_grammar_with_lark(
    grammar_text: str, start_symbol_name: str = "S", is_lark_file: bool = False
) -> tuple[Grammar, list[GrammarError]]:
    """Parse grammar text.

    By default, use the internal text parser (robust to lowercase non-terminals and operators).
    Set USE_LARK=true to enable the Lark-based parser for strict formats.
    """
    if DEBUG_GRAMMAR:
        debug_log(
            "🚀 parse_grammar_with_lark called",
            {
                "start_symbol": start_symbol_name,
                "is_lark_file": is_lark_file,
                "grammar_length": len(grammar_text),
                "grammar_preview": grammar_text[:100],
                "use_lark": os.getenv("USE_LARK", "false").lower() == "true",
            },
        )

    if os.getenv("USE_LARK", "false").lower() == "true":
        parser = LarkGrammarParser()
        if is_lark_file:
            return parser.parse_lark_file(grammar_text, start_symbol_name)
        return parser.parse_text_grammar(grammar_text, start_symbol_name)

    # Fallback/default: internal robust parser
    grammar = Grammar.from_string(grammar_text, start_symbol_name)
    errors = getattr(grammar, "_parse_errors", [])
    if DEBUG_GRAMMAR:
        debug_log(
            "🧩 Internal parser result",
            {
                "num_productions": len(grammar.productions),
                "num_terminals": len(grammar.terminals),
                "num_non_terminals": len(grammar.non_terminals),
                "errors": [e.dict() for e in errors] if errors else [],
            },
        )
    return grammar, errors
