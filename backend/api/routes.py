"""FastAPI routes for LR(1) parser endpoints."""

import json
import traceback
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from parser import Automaton, ParserEngine, ParsingTable
from parser.lark_grammar import parse_grammar_with_lark
from parser.sample_generator import generate_sample_strings
from pydantic import BaseModel
from utils.debug import error_log, info_log, log_api_request


# Request/Response models
class GrammarRequest(BaseModel):
    """Request model for grammar validation."""

    grammar_text: str
    start_symbol: str = "S"


class GrammarResponse(BaseModel):
    """Response model for grammar validation."""

    valid: bool
    errors: list[dict[str, Any]]
    grammar_info: dict[str, Any] | None = None


class ParsingRequest(BaseModel):
    """Request model for parsing."""

    grammar_text: str
    input_string: str
    start_symbol: str = "S"


class ParsingResponse(BaseModel):
    """Response model for parsing."""

    valid: bool
    error: str | None = None
    steps: list[dict[str, Any]]
    ast: dict[str, Any] | None = None
    summary: dict[str, Any]


class TableResponse(BaseModel):
    """Response model for parsing table."""

    action_table: dict[str, Any]
    goto_table: dict[str, Any]
    summary: dict[str, Any]
    conflicts: list[dict[str, Any]]


# Create router
router = APIRouter(prefix="/api/v1", tags=["parser"])


def _raise_grammar_validation_error(errors: list) -> None:
    """Raise HTTP exception for grammar validation failure."""
    raise HTTPException(
        status_code=400,
        detail=f"Grammar validation failed: {errors[0].message}",
    )


def _raise_conflict_error() -> None:
    """Raise HTTP exception for grammar conflicts."""
    raise HTTPException(
        status_code=400,
        detail="Grammar has conflicts and cannot be used for parsing",
    )


@router.post("/grammar/validate")
async def validate_grammar(request: GrammarRequest) -> GrammarResponse:
    """Validate a grammar and return any errors."""
    log_api_request("POST", "/grammar/validate", {"start_symbol": request.start_symbol})

    try:
        # Parse grammar using Lark
        grammar, lark_errors = parse_grammar_with_lark(request.grammar_text, request.start_symbol)

        # Validate grammar
        validation_errors = grammar.validate()
        errors = lark_errors + validation_errors

        # Convert errors to dict format
        error_dicts = [
            {
                "type": error.error_type,
                "message": error.message,
                "line_number": error.line_number,
                "symbol": error.symbol,
            }
            for error in errors
        ]

        if not errors:
            # Grammar is valid, build automaton and table
            try:
                info_log("🧩 Building automaton and parsing table")
                automaton = Automaton(grammar)
                parsing_table = ParsingTable(automaton)

                # Generate sample strings
                sample_strings = generate_sample_strings(grammar, 5)

                # Compute FIRST and FOLLOW sets
                first_sets = {}
                follow_sets = {}

                for nt in grammar.non_terminals:
                    if hasattr(grammar, "first"):
                        first_sets[nt.name] = [s.name for s in grammar.first((nt,))]
                    if hasattr(grammar, "follow"):
                        follow_sets[nt.name] = [s.name for s in grammar.follow(nt)]

                # Get detailed LR(1) states
                lr1_states = []
                for i, state in enumerate(automaton.states):
                    state_info = {
                        "state_number": i,
                        "items": [],
                        "shift_symbols": [s.name for s in state.get_shift_symbols()],
                        "reduce_items": [],
                    }

                    for item in state.items:
                        item_str = f"{item.production.lhs.name} -> "
                        rhs_str = " ".join(s.name for s in item.production.rhs)
                        if item.dot_position == 0:
                            item_str += "• " + rhs_str
                        elif item.dot_position >= len(item.production.rhs):
                            item_str += rhs_str + " •"
                        else:
                            rhs_parts = [s.name for s in item.production.rhs]
                            rhs_parts.insert(item.dot_position, "•")
                            item_str += " ".join(rhs_parts)
                        item_str += f" , {item.lookahead.name}"

                        state_info["items"].append(item_str)

                        if item.is_reduce_item:
                            state_info["reduce_items"].append(item_str)

                    lr1_states.append(state_info)

                grammar_info = {
                    "num_productions": len(grammar.productions),
                    "num_terminals": len(grammar.terminals),
                    "num_non_terminals": len(grammar.non_terminals),
                    "num_states": len(automaton.states),
                    "grammar_type": automaton.get_grammar_type(),
                    "has_conflicts": parsing_table.has_conflicts(),
                    "conflict_summary": parsing_table.get_conflict_summary(),
                    "terminals_list": [{"name": t.name, "type": "terminal"} for t in grammar.terminals],
                    "non_terminals_list": [{"name": nt.name, "type": "non_terminal"} for nt in grammar.non_terminals],
                    "productions_detailed": [
                        {"lhs": p.lhs.name, "rhs": [s.name for s in p.rhs] if p.rhs else ["ε"], "index": i}
                        for i, p in enumerate(grammar.productions)
                    ],
                    "first_sets": first_sets,
                    "follow_sets": follow_sets,
                    "lr1_states": lr1_states,
                    "sample_strings": sample_strings,
                    "parsing_table_preview": {
                        "action_table": parsing_table.export_action_table(),
                        "goto_table": parsing_table.export_goto_table(),
                    },
                }

                info_log("✅ Automaton and table built", grammar_info)

                return GrammarResponse(valid=True, errors=[], grammar_info=grammar_info)

            except Exception as e:
                tb = traceback.format_exc()
                error_log("💥 Automaton/table build failed", {"error": str(e), "trace": tb})
                return GrammarResponse(
                    valid=False,
                    errors=[
                        {
                            "type": "automaton_error",
                            "message": f"Error building automaton: {str(e)!s}",
                            "line_number": None,
                            "symbol": None,
                        },
                    ],
                )
        else:
            return GrammarResponse(valid=False, errors=error_dicts)

    except Exception as e:
        return GrammarResponse(
            valid=False,
            errors=[
                {
                    "type": "parse_error",
                    "message": f"Error parsing grammar: {str(e)!s}",
                    "line_number": None,
                    "symbol": None,
                },
            ],
        )


@router.post("/parser/table")
async def get_parsing_table(request: GrammarRequest) -> TableResponse:
    """Generate parsing table for a grammar."""
    try:
        # Parse grammar using Lark
        grammar, lark_errors = parse_grammar_with_lark(request.grammar_text, request.start_symbol)
        validation_errors = grammar.validate()
        errors = lark_errors + validation_errors

        if errors:
            _raise_grammar_validation_error(errors)

        # Build automaton and parsing table
        try:
            info_log("🧩 Building automaton and parsing table (table endpoint)")
            automaton = Automaton(grammar)
            parsing_table = ParsingTable(automaton)
        except Exception as e:
            error_log(
                "💥 Table build failed",
                {"error": str(e), "trace": traceback.format_exc()},
            )
            raise

        # Convert conflicts to dict format
        conflicts = [
            {
                "state": conflict.state,
                "symbol": conflict.symbol,
                "actions": [{"type": action.action_type.value, "target": action.target} for action in conflict.actions],
                "conflict_type": conflict.conflict_type,
            }
            for conflict in parsing_table.conflicts
        ]

        return TableResponse(
            action_table=parsing_table.export_action_table(),
            goto_table=parsing_table.export_goto_table(),
            summary=parsing_table.get_table_summary(),
            conflicts=conflicts,
        )

    except HTTPException:
        raise
    except Exception as e:
        error_log(
            "💥 /parser/table failed",
            {"error": str(e), "trace": traceback.format_exc()},
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/parser/parse")
async def parse_input(request: ParsingRequest) -> ParsingResponse:
    """Parse input string using the given grammar."""
    try:
        # Parse grammar using Lark
        grammar, lark_errors = parse_grammar_with_lark(request.grammar_text, request.start_symbol)
        validation_errors = grammar.validate()
        errors = lark_errors + validation_errors

        if errors:
            _raise_grammar_validation_error(errors)

        # Build automaton and parsing table
        try:
            info_log("🧩 Building automaton and parsing table (parse endpoint)")
            automaton = Automaton(grammar)
            parsing_table = ParsingTable(automaton)
        except Exception as e:
            error_log(
                "💥 Parse build failed",
                {"error": str(e), "trace": traceback.format_exc()},
            )
            raise

        if parsing_table.has_conflicts():
            _raise_conflict_error()

        # Create parser engine and parse input
        parser_engine = ParserEngine(grammar, parsing_table)
        validation_result = parser_engine.validate_input(request.input_string)

        summary = parser_engine.get_parsing_summary(request.input_string)

        return ParsingResponse(
            valid=validation_result["valid"],
            error=validation_result["error"],
            steps=validation_result["steps"],
            ast=validation_result["ast"],
            summary=summary,
        )

    except HTTPException:
        raise
    except Exception as e:
        error_log(
            "💥 /parser/parse failed",
            {"error": str(e), "trace": traceback.format_exc()},
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/examples")
async def get_example_grammars() -> dict[str, Any]:
    """Get example grammars for testing."""
    examples = {
        "arithmetic": {
            "name": "Arithmetic Expressions",
            "description": "Simple arithmetic expressions with +, -, *, /, parentheses",
            "grammar": """E -> E + T | E - T | T
T -> T * F | T / F | F
F -> ( E ) | id | num""",
            "start_symbol": "E",
            "sample_inputs": ["id + id * id", "id - num", "( id + num ) * id", "id / num + id"],
        },
        "simple_language": {
            "name": "Simple Language",
            "description": "Basic language with statements, expressions, and control flow",
            "grammar": """S -> stmt_list
stmt_list -> stmt stmt_list | stmt
stmt -> id = expr | if expr then stmt | while expr do stmt
expr -> expr + term | expr - term | term
term -> term * factor | term / factor | factor
factor -> id | num | ( expr )""",
            "start_symbol": "S",
            "sample_inputs": ["id = id + num", "if num then id = id", "while id do id = num"],
        },
        "json": {
            "name": "JSON-like Structure",
            "description": "Simplified JSON structure with objects and arrays",
            "grammar": """value -> object | array | string | number | true | false | null
object -> { pairs }
pairs -> pair pairs_tail | ε
pairs_tail -> , pair pairs_tail | ε
pair -> string : value
array -> [ elements ]
elements -> value elements_tail | ε
elements_tail -> , value elements_tail | ε""",
            "start_symbol": "value",
            "sample_inputs": ['{ "key" : "value" }', '[ "item1" , "item2" ]', "true", "{ }"],
        },
    }

    return {"examples": examples}


# WebSocket endpoint for real-time parsing
class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self) -> None:
        """Initialize connection manager."""
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and add WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        """Send message to specific WebSocket."""
        await websocket.send_text(message)

    async def broadcast(self, message: str) -> None:
        """Broadcast message to all connections."""
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@router.websocket("/ws/parse")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time parsing updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            # Parse the data (assuming it's JSON with grammar and input)
            try:
                request_data = json.loads(data)
                grammar_text = request_data.get("grammar_text", "")
                input_string = request_data.get("input_string", "")
                start_symbol = request_data.get("start_symbol", "S")

                # Create parsing request
                parse_request = ParsingRequest(
                    grammar_text=grammar_text,
                    input_string=input_string,
                    start_symbol=start_symbol,
                )

                # Get parsing result
                result = await parse_input(parse_request)

                # Send result back to client
                await manager.send_personal_message(json.dumps(result.dict()), websocket)

            except json.JSONDecodeError:
                await manager.send_personal_message(json.dumps({"error": "Invalid JSON format"}), websocket)
            except Exception as e:
                await manager.send_personal_message(json.dumps({"error": str(e)}), websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
