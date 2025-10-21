"""Command-line debugging tools for the LR(1) Parser Visualizer."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from parser.automaton import Automaton
from parser.grammar_v2 import Grammar
from parser.table import ParsingTable
from debug.inspector import GrammarInspector, TableInspector
from debug.validators import GrammarValidator
from debug.logger import get_logger, setup_logging

logger = get_logger(__name__)


class ParserDebuggerCLI:
    """Command-line interface for parser debugging."""

    def __init__(self):
        """Initialize the CLI."""
        self.parser = self._create_parser()
        setup_logging()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            description="LR(1) Parser Visualizer Debugging Tools",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s validate grammar.txt
  %(prog)s inspect grammar.txt --format json
  %(prog)s table grammar.txt --show-conflicts
  %(prog)s parse grammar.txt "id + id * id"
  %(prog)s profile grammar.txt --iterations 100
            """,
        )

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Validate command
        validate_parser = subparsers.add_parser("validate", help="Validate grammar")
        validate_parser.add_argument("grammar_file", help="Grammar file to validate")
        validate_parser.add_argument("--start-symbol", default="S", help="Start symbol name")
        validate_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

        # Inspect command
        inspect_parser = subparsers.add_parser("inspect", help="Inspect grammar properties")
        inspect_parser.add_argument("grammar_file", help="Grammar file to inspect")
        inspect_parser.add_argument("--start-symbol", default="S", help="Start symbol name")
        inspect_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
        inspect_parser.add_argument(
            "--sections",
            nargs="+",
            choices=["grammar", "symbols", "productions", "first", "follow", "all"],
            default=["all"],
            help="Sections to inspect",
        )

        # Table command
        table_parser = subparsers.add_parser("table", help="Generate and inspect parsing table")
        table_parser.add_argument("grammar_file", help="Grammar file")
        table_parser.add_argument("--start-symbol", default="S", help="Start symbol name")
        table_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
        table_parser.add_argument("--show-conflicts", action="store_true", help="Show conflicts")
        table_parser.add_argument("--export-action", help="Export ACTION table to file")
        table_parser.add_argument("--export-goto", help="Export GOTO table to file")

        # Parse command
        parse_parser = subparsers.add_parser("parse", help="Parse input string")
        parse_parser.add_argument("grammar_file", help="Grammar file")
        parse_parser.add_argument("input_string", help="Input string to parse")
        parse_parser.add_argument("--start-symbol", default="S", help="Start symbol name")
        parse_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
        parse_parser.add_argument("--show-steps", action="store_true", help="Show parsing steps")

        # Profile command
        profile_parser = subparsers.add_parser("profile", help="Profile grammar performance")
        profile_parser.add_argument("grammar_file", help="Grammar file to profile")
        profile_parser.add_argument("--start-symbol", default="S", help="Start symbol name")
        profile_parser.add_argument("--iterations", type=int, default=10, help="Number of iterations")
        profile_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

        return parser

    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the CLI with given arguments."""
        parsed_args = self.parser.parse_args(args)

        if not parsed_args.command:
            self.parser.print_help()
            return 1

        try:
            if parsed_args.command == "validate":
                return self._validate_grammar(parsed_args)
            elif parsed_args.command == "inspect":
                return self._inspect_grammar(parsed_args)
            elif parsed_args.command == "table":
                return self._inspect_table(parsed_args)
            elif parsed_args.command == "parse":
                return self._parse_input(parsed_args)
            elif parsed_args.command == "profile":
                return self._profile_grammar(parsed_args)
            else:
                logger.error(f"Unknown command: {parsed_args.command}")
                return 1
        except Exception as e:
            logger.error(f"Error: {e}")
            if parsed_args.format == "json":
                print(json.dumps({"error": str(e), "success": False}))
            return 1

    def _validate_grammar(self, args) -> int:
        """Validate grammar command."""
        grammar_text = self._read_grammar_file(args.grammar_file)
        grammar = Grammar.from_text(grammar_text, args.start_symbol)

        validator = GrammarValidator(grammar)
        validation_result = validator.validate_all()

        if args.format == "json":
            print(json.dumps(validation_result, indent=2))
        else:
            self._print_validation_text(validation_result)

        return 0 if validation_result["is_valid"] else 1

    def _inspect_grammar(self, args) -> int:
        """Inspect grammar command."""
        grammar_text = self._read_grammar_file(args.grammar_file)
        grammar = Grammar.from_text(grammar_text, args.start_symbol)

        inspector = GrammarInspector(grammar)
        report = inspector.generate_report()

        if args.format == "json":
            print(json.dumps(report, indent=2))
        else:
            self._print_inspection_text(report, args.sections)

        return 0

    def _inspect_table(self, args) -> int:
        """Inspect table command."""
        grammar_text = self._read_grammar_file(args.grammar_file)
        grammar = Grammar.from_text(grammar_text, args.start_symbol)

        automaton = Automaton(grammar)
        table = ParsingTable(automaton)

        inspector = TableInspector(table)
        report = inspector.generate_report()

        if args.format == "json":
            print(json.dumps(report, indent=2))
        else:
            self._print_table_text(report, args)

        # Export tables if requested
        if args.export_action:
            self._export_action_table(table, args.export_action)
        if args.export_goto:
            self._export_goto_table(table, args.export_goto)

        return 0

    def _parse_input(self, args) -> int:
        """Parse input command."""
        grammar_text = self._read_grammar_file(args.grammar_file)
        grammar = Grammar.from_text(grammar_text, args.start_symbol)

        automaton = Automaton(grammar)
        table = ParsingTable(automaton)

        if table.has_conflicts():
            logger.error("Grammar has conflicts and cannot be used for parsing")
            return 1

        # TODO: Implement parsing with step-by-step output
        logger.info(f"Parsing input: {args.input_string}")

        if args.format == "json":
            print(json.dumps({"message": "Parsing not yet implemented", "success": False}))
        else:
            print("Parsing functionality not yet implemented")

        return 0

    def _profile_grammar(self, args) -> int:
        """Profile grammar command."""
        grammar_text = self._read_grammar_file(args.grammar_file)

        import time

        times = []
        for i in range(args.iterations):
            start_time = time.time()

            grammar = Grammar.from_text(grammar_text, args.start_symbol)
            automaton = Automaton(grammar)
            ParsingTable(automaton)

            end_time = time.time()
            times.append(end_time - start_time)

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        profile_data = {
            "iterations": args.iterations,
            "average_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "times": times,
        }

        if args.format == "json":
            print(json.dumps(profile_data, indent=2))
        else:
            print("Profile Results:")
            print(f"  Iterations: {args.iterations}")
            print(f"  Average time: {avg_time:.4f}s")
            print(f"  Min time: {min_time:.4f}s")
            print(f"  Max time: {max_time:.4f}s")

        return 0

    def _read_grammar_file(self, file_path: str) -> str:
        """Read grammar file content."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Grammar file not found: {file_path}")

        return path.read_text(encoding="utf-8")

    def _print_validation_text(self, result: Dict[str, Any]) -> None:
        """Print validation results in text format."""
        print("Grammar Validation Results")
        print("=" * 30)

        if result["is_valid"]:
            print("✅ Grammar is valid")
        else:
            print("❌ Grammar has errors")
            print(f"Error count: {result['error_count']}")
            print()

            for error in result["errors"]:
                print(f"• {error['type']}: {error['message']}")
                if "symbol" in error:
                    print(f"  Symbol: {error['symbol']}")
                if "production" in error:
                    print(f"  Production: {error['production']}")
                print()

    def _print_inspection_text(self, report: Dict[str, Any], sections: List[str]) -> None:
        """Print inspection results in text format."""
        print("Grammar Inspection Report")
        print("=" * 30)

        if "all" in sections or "grammar" in sections:
            print(f"Start symbol: {report['grammar_info']['start_symbol']}")
            print(f"Total productions: {report['grammar_info']['total_productions']}")
            print()

        if "all" in sections or "symbols" in sections:
            print("Symbols:")
            print(f"  Terminals: {report['symbols']['total_terminals']} - {report['symbols']['terminals']}")
            print(f"  Non-terminals: {report['symbols']['total_non_terminals']} - {report['symbols']['non_terminals']}")
            print()

        if "all" in sections or "productions" in sections:
            print("Productions:")
            for lhs, prods in report["productions"]["productions_by_lhs"].items():
                print(f"  {lhs}:")
                for prod in prods:
                    print(f"    {prod['rhs']}")
            print()

        if "all" in sections or "first" in sections:
            print("FIRST Sets:")
            for nt, first_set in report["first_sets"].items():
                print(f"  FIRST({nt}) = {{{', '.join(first_set)}}}")
            print()

        if "all" in sections or "follow" in sections:
            print("FOLLOW Sets:")
            for nt, follow_set in report["follow_sets"].items():
                print(f"  FOLLOW({nt}) = {{{', '.join(follow_set)}}}")
            print()

    def _print_table_text(self, report: Dict[str, Any], args) -> None:
        """Print table results in text format."""
        print("Parsing Table Report")
        print("=" * 30)

        print(f"Valid: {report['table_info']['is_valid']}")
        print(f"Has conflicts: {report['table_info']['has_conflicts']}")
        print()

        print(f"ACTION Table: {report['action_table']['total_entries']} entries")
        print(f"GOTO Table: {report['goto_table']['total_entries']} entries")
        print()

        if args.show_conflicts and report["conflicts"]["total_conflicts"] > 0:
            print("Conflicts:")
            for conflict_type, conflicts in report["conflicts"]["conflicts_by_type"].items():
                print(f"  {conflict_type}: {len(conflicts)} conflicts")
                for conflict in conflicts:
                    print(f"    State {conflict['state']}, Symbol '{conflict['symbol']}'")
            print()

    def _export_action_table(self, table: ParsingTable, file_path: str) -> None:
        """Export ACTION table to file."""
        exported = table.export_action_table()
        with open(file_path, "w") as f:
            json.dump(exported, f, indent=2)
        logger.info(f"ACTION table exported to {file_path}")

    def _export_goto_table(self, table: ParsingTable, file_path: str) -> None:
        """Export GOTO table to file."""
        exported = table.export_goto_table()
        with open(file_path, "w") as f:
            json.dump(exported, f, indent=2)
        logger.info(f"GOTO table exported to {file_path}")


def main():
    """Main entry point for the CLI."""
    cli = ParserDebuggerCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
