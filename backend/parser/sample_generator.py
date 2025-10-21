"""Generate sample strings from grammars for testing and demonstration."""

import random
from typing import List

from parser.grammar_v2 import Grammar
from parser.types import Production, Symbol, SymbolType
from debug.logger import get_logger

logger = get_logger(__name__)


class SampleGenerator:
    """Generate valid sample strings from a grammar using leftmost derivation."""

    def __init__(self, grammar: Grammar) -> None:
        """Initialize the sample generator with a grammar."""
        self.grammar = grammar
        self.max_depth = 10  # Prevent infinite recursion
        self.max_samples = 5

    def generate_samples(self, count: int | None = None) -> list[str]:
        """Generate sample strings from the grammar."""
        if count is None:
            count = self.max_samples

        logger.debug("Generating sample strings", extra={"count": count})

        samples = []
        attempts = 0
        max_attempts = count * 3  # Try 3x to get enough unique samples

        while len(samples) < count and attempts < max_attempts:
            attempts += 1
            try:
                sample = self._generate_single_sample()
                if sample and sample not in samples:
                    samples.append(sample)
                    logger.debug("Generated sample", extra={"sample": sample})
            except Exception as e:
                logger.warning("Failed to generate sample", extra={"error": str(e)})
                continue

        # If we couldn't generate enough unique samples, add some shorter ones
        if len(samples) < count:
            samples.extend(self._generate_simple_samples(count - len(samples)))

        return samples[:count]

    def _generate_single_sample(self) -> str:
        """Generate a single sample string using leftmost derivation."""
        # Start with the start symbol (skip augmented production)
        start_symbol = self.grammar.start_symbol
        if start_symbol.name.endswith("'"):
            # Find the original start symbol from productions
            for prod in self.grammar.productions:
                if prod.lhs == start_symbol and len(prod.rhs) == 1:
                    current_symbols = [prod.rhs[0]]
                    break
            else:
                current_symbols = [self.grammar.start_symbol]
        else:
            current_symbols = [start_symbol]

        depth = 0
        while depth < self.max_depth and any(self._is_non_terminal(s) for s in current_symbols):
            depth += 1

            # Find leftmost non-terminal
            leftmost_nt_index = None
            for i, symbol in enumerate(current_symbols):
                if self._is_non_terminal(symbol):
                    leftmost_nt_index = i
                    break

            if leftmost_nt_index is None:
                break

            # Get productions for this non-terminal
            productions = self.grammar.get_productions_for_symbol(current_symbols[leftmost_nt_index])
            if not productions:
                break

            # Choose a random production
            chosen_production = random.choice(productions)

            # Replace the non-terminal with the RHS of the production
            new_symbols = (
                current_symbols[:leftmost_nt_index] + list(chosen_production.rhs) + current_symbols[leftmost_nt_index + 1 :]
            )
            current_symbols = new_symbols

        # Convert to string, filtering out epsilon
        result = []
        for symbol in current_symbols:
            if symbol.symbol_type != SymbolType.EPSILON:
                if symbol.symbol_type == SymbolType.TERMINAL:
                    # Add quotes for string terminals, but not for operators
                    if symbol.name in ["id", "num", "string", "number"]:
                        result.append(symbol.name)
                    elif symbol.name in ["+", "-", "*", "/", "(", ")", "{", "}", "[", "]", "=", ",", ";"]:
                        result.append(symbol.name)
                    else:
                        result.append(f'"{symbol.name}"')
                else:
                    result.append(symbol.name)

        return " ".join(result)

    def _generate_simple_samples(self, count: int) -> List[str]:
        """Generate simple samples by using only terminal productions."""
        samples = []

        # Find productions that produce only terminals
        terminal_productions = []
        for prod in self.grammar.productions:
            if len(prod.rhs) <= 3 and all(symbol.symbol_type == SymbolType.TERMINAL for symbol in prod.rhs):
                terminal_productions.append(prod)

        if not terminal_productions:
            return samples

        for i in range(min(count, len(terminal_productions))):
            prod = terminal_productions[i]
            sample_parts = []
            for symbol in prod.rhs:
                if symbol.symbol_type != SymbolType.EPSILON:
                    if symbol.name in ["+", "-", "*", "/", "(", ")", "{", "}", "[", "]", "=", ",", ";"]:
                        sample_parts.append(symbol.name)
                    else:
                        sample_parts.append(f'"{symbol.name}"')
            if sample_parts:
                samples.append(" ".join(sample_parts))

        return samples

    def _is_non_terminal(self, symbol: Symbol) -> bool:
        """Check if a symbol is a non-terminal."""
        return symbol.symbol_type == SymbolType.NON_TERMINAL

    def get_derivation_steps(self, target_string: str) -> list[tuple[str, Production]]:
        """Get the derivation steps for a given string (for debugging)."""
        # This is a simplified implementation - in practice, you'd need
        # a more sophisticated parsing approach to reconstruct derivations
        steps = []
        current_symbols = [self.grammar.start_symbol]
        steps.append((" ".join(str(s) for s in current_symbols), None))

        # This is a placeholder - actual implementation would be more complex
        return steps


def generate_sample_strings(grammar: Grammar, count: int = 5) -> list[str]:
    """Convenience function to generate sample strings from a grammar."""
    generator = SampleGenerator(grammar)
    return generator.generate_samples(count)
