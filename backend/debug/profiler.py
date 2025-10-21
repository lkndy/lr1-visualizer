"""Performance profiling tools for the LR(1) Parser Visualizer."""

import cProfile
import io
import pstats
import time
import tracemalloc
from contextlib import contextmanager
from typing import Any, Dict, List

from parser.automaton import Automaton
from parser.grammar_v2 import Grammar
from parser.table import ParsingTable
from debug.logger import get_logger

logger = get_logger(__name__)


class ParserProfiler:
    """Performance profiler for parser components."""

    def __init__(self):
        """Initialize the profiler."""
        self.results: Dict[str, Any] = {}

    @contextmanager
    def profile_function(self, function_name: str):
        """Context manager for profiling a function."""
        logger.debug(f"Starting profile for {function_name}")

        # Start memory tracing
        tracemalloc.start()

        # Start CPU profiling
        profiler = cProfile.Profile()
        profiler.enable()

        start_time = time.time()

        try:
            yield
        finally:
            end_time = time.time()
            profiler.disable()

            # Stop memory tracing
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            # Get profiling stats
            stats_stream = io.StringIO()
            stats = pstats.Stats(profiler, stream=stats_stream)
            stats.sort_stats("cumulative")
            stats.print_stats(20)  # Top 20 functions

            # Store results
            self.results[function_name] = {
                "execution_time": end_time - start_time,
                "memory_current": current,
                "memory_peak": peak,
                "cpu_profile": stats_stream.getvalue(),
                "function_calls": stats.total_calls,
                "primitive_calls": stats.prim_calls,
            }

            logger.debug(f"Completed profile for {function_name}")

    def profile_grammar_parsing(self, grammar_text: str, start_symbol: str = "S", iterations: int = 1) -> Dict[str, Any]:
        """Profile grammar parsing performance."""
        logger.info(f"Profiling grammar parsing ({iterations} iterations)")

        for i in range(iterations):
            with self.profile_function(f"grammar_parsing_{i}"):
                Grammar.from_text(grammar_text, start_symbol)

        # Calculate statistics
        execution_times = [self.results[f"grammar_parsing_{i}"]["execution_time"] for i in range(iterations)]

        return {
            "operation": "grammar_parsing",
            "iterations": iterations,
            "execution_times": execution_times,
            "average_time": sum(execution_times) / len(execution_times),
            "min_time": min(execution_times),
            "max_time": max(execution_times),
            "total_time": sum(execution_times),
        }

    def profile_automaton_construction(self, grammar: Grammar, iterations: int = 1) -> Dict[str, Any]:
        """Profile automaton construction performance."""
        logger.info(f"Profiling automaton construction ({iterations} iterations)")

        automaton = None
        for i in range(iterations):
            with self.profile_function(f"automaton_construction_{i}"):
                automaton = Automaton(grammar)

        # Calculate statistics
        execution_times = [self.results[f"automaton_construction_{i}"]["execution_time"] for i in range(iterations)]

        return {
            "operation": "automaton_construction",
            "iterations": iterations,
            "execution_times": execution_times,
            "average_time": sum(execution_times) / len(execution_times),
            "min_time": min(execution_times),
            "max_time": max(execution_times),
            "total_time": sum(execution_times),
            "num_states": len(automaton.states) if automaton else 0,
            "num_transitions": len(automaton.transitions) if automaton else 0,
        }

    def profile_table_construction(self, automaton: Automaton, iterations: int = 1) -> Dict[str, Any]:
        """Profile parsing table construction performance."""
        logger.info(f"Profiling table construction ({iterations} iterations)")

        table = None
        for i in range(iterations):
            with self.profile_function(f"table_construction_{i}"):
                table = ParsingTable(automaton)

        # Calculate statistics
        execution_times = [self.results[f"table_construction_{i}"]["execution_time"] for i in range(iterations)]

        return {
            "operation": "table_construction",
            "iterations": iterations,
            "execution_times": execution_times,
            "average_time": sum(execution_times) / len(execution_times),
            "min_time": min(execution_times),
            "max_time": max(execution_times),
            "total_time": sum(execution_times),
            "action_entries": len(table.action_table) if table else 0,
            "goto_entries": len(table.goto_table) if table else 0,
            "has_conflicts": table.has_conflicts() if table else False,
        }

    def profile_full_pipeline(self, grammar_text: str, start_symbol: str = "S", iterations: int = 1) -> Dict[str, Any]:
        """Profile the full parsing pipeline."""
        logger.info(f"Profiling full pipeline ({iterations} iterations)")

        pipeline_times = []
        grammar_times = []
        automaton_times = []
        table_times = []

        for i in range(iterations):
            start_time = time.time()

            # Grammar parsing
            grammar_start = time.time()
            grammar = Grammar.from_text(grammar_text, start_symbol)
            grammar_times.append(time.time() - grammar_start)

            # Automaton construction
            automaton_start = time.time()
            automaton = Automaton(grammar)
            automaton_times.append(time.time() - automaton_start)

            # Table construction
            table_start = time.time()
            ParsingTable(automaton)
            table_times.append(time.time() - table_start)

            pipeline_times.append(time.time() - start_time)

        return {
            "operation": "full_pipeline",
            "iterations": iterations,
            "pipeline_times": pipeline_times,
            "grammar_times": grammar_times,
            "automaton_times": automaton_times,
            "table_times": table_times,
            "average_pipeline_time": sum(pipeline_times) / len(pipeline_times),
            "average_grammar_time": sum(grammar_times) / len(grammar_times),
            "average_automaton_time": sum(automaton_times) / len(automaton_times),
            "average_table_time": sum(table_times) / len(table_times),
            "grammar_percentage": (sum(grammar_times) / sum(pipeline_times)) * 100,
            "automaton_percentage": (sum(automaton_times) / sum(pipeline_times)) * 100,
            "table_percentage": (sum(table_times) / sum(pipeline_times)) * 100,
        }

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage information."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        return {
            "rss": memory_info.rss,  # Resident Set Size
            "vms": memory_info.vms,  # Virtual Memory Size
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": process.memory_percent(),
        }

    def analyze_bottlenecks(self, results: Dict[str, Any]) -> List[str]:
        """Analyze performance bottlenecks from profiling results."""
        bottlenecks = []

        if "full_pipeline" in results:
            pipeline = results["full_pipeline"]

            # Find the slowest component
            components = {
                "Grammar Parsing": pipeline["average_grammar_time"],
                "Automaton Construction": pipeline["average_automaton_time"],
                "Table Construction": pipeline["average_table_time"],
            }

            slowest = max(components, key=components.get)
            bottlenecks.append(f"Slowest component: {slowest} ({components[slowest]:.4f}s)")

            # Check for high variance
            if pipeline["iterations"] > 1:
                grammar_variance = self._calculate_variance(pipeline["grammar_times"])
                automaton_variance = self._calculate_variance(pipeline["automaton_times"])
                table_variance = self._calculate_variance(pipeline["table_times"])

                if grammar_variance > 0.1:
                    bottlenecks.append(f"High variance in grammar parsing: {grammar_variance:.4f}")
                if automaton_variance > 0.1:
                    bottlenecks.append(f"High variance in automaton construction: {automaton_variance:.4f}")
                if table_variance > 0.1:
                    bottlenecks.append(f"High variance in table construction: {table_variance:.4f}")

        return bottlenecks

    def _calculate_variance(self, times: List[float]) -> float:
        """Calculate variance of execution times."""
        if len(times) < 2:
            return 0.0

        mean = sum(times) / len(times)
        variance = sum((t - mean) ** 2 for t in times) / len(times)
        return variance

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a human-readable performance report."""
        report_lines = []
        report_lines.append("Performance Profiling Report")
        report_lines.append("=" * 40)
        report_lines.append("")

        for operation, data in results.items():
            if operation == "full_pipeline":
                report_lines.append("Full Pipeline Performance:")
                report_lines.append(f"  Average total time: {data['average_pipeline_time']:.4f}s")
                report_lines.append(
                    f"  Grammar parsing: {data['average_grammar_time']:.4f}s ({data['grammar_percentage']:.1f}%)"
                )
                report_lines.append(
                    f"  Automaton construction: {data['average_automaton_time']:.4f}s ({data['automaton_percentage']:.1f}%)"
                )
                report_lines.append(
                    f"  Table construction: {data['average_table_time']:.4f}s ({data['table_percentage']:.1f}%)"
                )
                report_lines.append("")
            else:
                report_lines.append(f"{operation.replace('_', ' ').title()} Performance:")
                report_lines.append(f"  Average time: {data['average_time']:.4f}s")
                report_lines.append(f"  Min time: {data['min_time']:.4f}s")
                report_lines.append(f"  Max time: {data['max_time']:.4f}s")
                report_lines.append("")

        # Add bottleneck analysis
        bottlenecks = self.analyze_bottlenecks(results)
        if bottlenecks:
            report_lines.append("Bottleneck Analysis:")
            for bottleneck in bottlenecks:
                report_lines.append(f"  • {bottleneck}")
            report_lines.append("")

        # Add memory usage
        memory = self.get_memory_usage()
        report_lines.append("Memory Usage:")
        report_lines.append(f"  RSS: {memory['rss_mb']:.2f} MB")
        report_lines.append(f"  VMS: {memory['vms_mb']:.2f} MB")
        report_lines.append(f"  Percentage: {memory['percent']:.1f}%")

        return "\n".join(report_lines)

    def export_results(self, results: Dict[str, Any], file_path: str) -> None:
        """Export profiling results to JSON file."""
        import json

        with open(file_path, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Profiling results exported to {file_path}")


def profile_grammar(grammar_text: str, start_symbol: str = "S", iterations: int = 10) -> Dict[str, Any]:
    """Convenience function to profile a grammar."""
    profiler = ParserProfiler()

    # Profile individual components
    grammar_results = profiler.profile_grammar_parsing(grammar_text, start_symbol, iterations)

    # Profile full pipeline
    pipeline_results = profiler.profile_full_pipeline(grammar_text, start_symbol, iterations)

    # Combine results
    all_results = {"grammar_parsing": grammar_results, "full_pipeline": pipeline_results}

    return all_results


if __name__ == "__main__":
    # Example usage
    grammar_text = """
    E: E "+" T | E "-" T | T
    T: T "*" F | T "/" F | F
    F: "(" E ")" | "id" | "num"
    """

    results = profile_grammar(grammar_text, "E", 5)

    profiler = ParserProfiler()
    report = profiler.generate_report(results)
    print(report)
