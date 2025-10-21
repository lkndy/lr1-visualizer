"""Web-based debugging tools for the LR(1) Parser Visualizer."""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from parser.automaton import Automaton
from parser.grammar_v2 import Grammar
from parser.table import ParsingTable
from debug.inspector import GrammarInspector, AutomatonInspector, TableInspector
from debug.validators import GrammarValidator, TableValidator
from debug.logger import get_logger

logger = get_logger(__name__)

# Create debug router
debug_router = APIRouter(prefix="/debug", tags=["debug"])


@debug_router.post("/grammar/analyze")
async def analyze_grammar(request: Request) -> Dict[str, Any]:
    """Analyze grammar properties and return detailed information."""
    try:
        data = await request.json()
        grammar_text = data.get("grammar_text", "")
        start_symbol = data.get("start_symbol", "S")

        if not grammar_text:
            raise HTTPException(status_code=400, detail="grammar_text is required")

        # Parse grammar
        grammar = Grammar.from_text(grammar_text, start_symbol)

        # Create inspector and validator
        inspector = GrammarInspector(grammar)
        validator = GrammarValidator(grammar)

        # Generate reports
        inspection_report = inspector.generate_report()
        validation_result = validator.validate_all()

        return {
            "success": True,
            "grammar_info": inspection_report["grammar_info"],
            "symbols": inspection_report["symbols"],
            "productions": inspection_report["productions"],
            "first_sets": inspection_report["first_sets"],
            "follow_sets": inspection_report["follow_sets"],
            "left_recursion": inspection_report["left_recursion"],
            "reachability": inspection_report["reachability"],
            "validation": validation_result,
        }

    except Exception as e:
        logger.error(f"Error analyzing grammar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.post("/automaton/analyze")
async def analyze_automaton(request: Request) -> Dict[str, Any]:
    """Analyze automaton properties and return detailed information."""
    try:
        data = await request.json()
        grammar_text = data.get("grammar_text", "")
        start_symbol = data.get("start_symbol", "S")

        if not grammar_text:
            raise HTTPException(status_code=400, detail="grammar_text is required")

        # Parse grammar and build automaton
        grammar = Grammar.from_text(grammar_text, start_symbol)
        automaton = Automaton(grammar)

        # Create inspector
        inspector = AutomatonInspector(automaton)

        # Generate report
        report = inspector.generate_report()

        return {
            "success": True,
            "automaton_info": report["automaton_info"],
            "states": report["states"],
            "conflicts": report["conflicts"],
            "grammar_type": report["grammar_type"],
        }

    except Exception as e:
        logger.error(f"Error analyzing automaton: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.post("/table/analyze")
async def analyze_table(request: Request) -> Dict[str, Any]:
    """Analyze parsing table properties and return detailed information."""
    try:
        data = await request.json()
        grammar_text = data.get("grammar_text", "")
        start_symbol = data.get("start_symbol", "S")

        if not grammar_text:
            raise HTTPException(status_code=400, detail="grammar_text is required")

        # Parse grammar and build automaton and table
        grammar = Grammar.from_text(grammar_text, start_symbol)
        automaton = Automaton(grammar)
        table = ParsingTable(automaton)

        # Create inspector and validator
        inspector = TableInspector(table)
        validator = TableValidator(table)

        # Generate reports
        inspection_report = inspector.generate_report()
        validation_result = validator.validate_all()

        return {
            "success": True,
            "table_info": inspection_report["table_info"],
            "action_table": inspection_report["action_table"],
            "goto_table": inspection_report["goto_table"],
            "conflicts": inspection_report["conflicts"],
            "density": inspection_report["density"],
            "validation": validation_result,
        }

    except Exception as e:
        logger.error(f"Error analyzing table: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.post("/parse/trace")
async def trace_parsing(request: Request) -> Dict[str, Any]:
    """Trace parsing steps for a given input string."""
    try:
        data = await request.json()
        grammar_text = data.get("grammar_text", "")
        input_string = data.get("input_string", "")
        start_symbol = data.get("start_symbol", "S")

        if not grammar_text:
            raise HTTPException(status_code=400, detail="grammar_text is required")
        if not input_string:
            raise HTTPException(status_code=400, detail="input_string is required")

        # Parse grammar and build automaton and table
        grammar = Grammar.from_text(grammar_text, start_symbol)
        automaton = Automaton(grammar)
        table = ParsingTable(automaton)

        if table.has_conflicts():
            return {
                "success": False,
                "error": "Grammar has conflicts and cannot be used for parsing",
                "conflicts": table.get_conflict_summary(),
            }

        # TODO: Implement step-by-step parsing trace
        # For now, return a placeholder
        return {
            "success": True,
            "message": "Parsing trace not yet implemented",
            "input": input_string,
            "grammar_type": automaton.get_grammar_type(),
            "num_states": len(automaton.states),
        }

    except Exception as e:
        logger.error(f"Error tracing parsing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.post("/conflicts/resolve")
async def resolve_conflicts(request: Request) -> Dict[str, Any]:
    """Analyze conflicts and suggest resolution strategies."""
    try:
        data = await request.json()
        grammar_text = data.get("grammar_text", "")
        start_symbol = data.get("start_symbol", "S")

        if not grammar_text:
            raise HTTPException(status_code=400, detail="grammar_text is required")

        # Parse grammar and build automaton and table
        grammar = Grammar.from_text(grammar_text, start_symbol)
        automaton = Automaton(grammar)
        table = ParsingTable(automaton)

        conflicts = table.find_conflicts()
        conflict_analysis = []

        for conflict in conflicts:
            analysis = {"type": conflict["type"], "state": conflict["state"], "symbol": conflict["symbol"], "suggestions": []}

            if conflict["type"] == "shift_reduce":
                analysis["suggestions"] = [
                    "Consider operator precedence rules",
                    "Use left or right associativity",
                    "Restructure grammar to avoid ambiguity",
                ]
            elif conflict["type"] == "reduce_reduce":
                analysis["suggestions"] = [
                    "Remove duplicate productions",
                    "Use different non-terminal names",
                    "Restructure grammar to eliminate ambiguity",
                ]

            conflict_analysis.append(analysis)

        return {
            "success": True,
            "conflicts": conflict_analysis,
            "total_conflicts": len(conflicts),
            "is_lr1": len(conflicts) == 0,
        }

    except Exception as e:
        logger.error(f"Error resolving conflicts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.post("/performance/profile")
async def profile_performance(request: Request) -> Dict[str, Any]:
    """Profile grammar performance."""
    try:
        data = await request.json()
        grammar_text = data.get("grammar_text", "")
        start_symbol = data.get("start_symbol", "S")
        iterations = data.get("iterations", 10)

        if not grammar_text:
            raise HTTPException(status_code=400, detail="grammar_text is required")

        from debug.profiler import profile_grammar

        # Profile the grammar
        results = profile_grammar(grammar_text, start_symbol, iterations)

        return {"success": True, "results": results}

    except Exception as e:
        logger.error(f"Error profiling performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@debug_router.get("/examples")
async def get_debug_examples() -> Dict[str, Any]:
    """Get example grammars for debugging."""
    examples = {
        "simple": {
            "name": "Simple Grammar",
            "description": "Basic grammar with no conflicts",
            "grammar": """
            S: A B
            A: "a" | ε
            B: "b" | ε
            """,
            "start_symbol": "S",
        },
        "arithmetic": {
            "name": "Arithmetic Expressions",
            "description": "Grammar for arithmetic expressions with operator precedence",
            "grammar": """
            E: E "+" T | E "-" T | T
            T: T "*" F | T "/" F | F
            F: "(" E ")" | "id" | "num"
            """,
            "start_symbol": "E",
        },
        "ambiguous": {
            "name": "Ambiguous Grammar",
            "description": "Grammar with shift-reduce conflicts",
            "grammar": """
            S: "a" S | "a"
            """,
            "start_symbol": "S",
        },
        "left_recursive": {
            "name": "Left Recursive Grammar",
            "description": "Grammar with left recursion (acceptable for LR)",
            "grammar": """
            E: E "+" T | T
            T: T "*" F | F
            F: "id"
            """,
            "start_symbol": "E",
        },
        "epsilon": {
            "name": "Epsilon Productions",
            "description": "Grammar with epsilon productions",
            "grammar": """
            S: A B C
            A: "a" | ε
            B: "b" | ε
            C: "c" | ε
            """,
            "start_symbol": "S",
        },
    }

    return {"success": True, "examples": examples}


@debug_router.get("/health")
async def debug_health() -> Dict[str, Any]:
    """Health check for debug endpoints."""
    return {
        "success": True,
        "status": "healthy",
        "endpoints": [
            "/debug/grammar/analyze",
            "/debug/automaton/analyze",
            "/debug/table/analyze",
            "/debug/parse/trace",
            "/debug/conflicts/resolve",
            "/debug/performance/profile",
            "/debug/examples",
        ],
    }
