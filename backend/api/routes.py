"""FastAPI routes for LR(1) parser endpoints."""

import json
import time
import traceback
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Request
from parser import Automaton, ParserEngine, ParsingTable
from parser.lark_grammar_v2 import parse_grammar_with_lark_v2
from parser.sample_generator import generate_sample_strings
from pydantic import BaseModel
from debug.logger import get_logger, log_api_request, log_api_response
from debug.api_validator import api_validator


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


class InteractiveDerivationRequest(BaseModel):
    """Request model for interactive string derivation."""

    grammar_text: str
    input_string: str
    start_symbol: str = "S"


class InteractiveDerivationResponse(BaseModel):
    """Response model for interactive string derivation."""

    valid: bool
    error: str | None = None
    input_string: str
    tokens: list[str]
    total_steps: int
    success: bool
    steps: list[dict[str, Any]]
    summary: dict[str, Any]
    ast: dict[str, Any] | None = None   


# Create router
router = APIRouter(prefix="/api/v1", tags=["parser"])

# Get logger
logger = get_logger(__name__)


def validate_and_log_request(request: Request, endpoint: str, data: dict = None) -> str:
    """Validate request and log with unique ID."""
    request_id = api_validator.generate_request_id()

    # Log request
    api_validator.log_request(
        request_id=request_id, method=request.method, endpoint=endpoint, data=data, headers=dict(request.headers)
    )

    return request_id


def validate_and_log_response(
    request_id: str, status_code: int, data: dict = None, duration_ms: float = 0, error: str = None
) -> None:
    """Validate response and log with validation results."""
    # Validate response structure based on endpoint
    validation_errors = []
    if data:
        if "valid" in data and "errors" in data:
            # Grammar validation response
            validation_errors = api_validator.validate_grammar_response(data)
        elif "steps" in data and "total_steps" in data:
            # Parsing response
            validation_errors = api_validator.validate_parsing_response(data)

    if validation_errors:
        logger.warning(f"⚠️ [RESP-{request_id}] Validation errors: {validation_errors}")

    # Log response
    api_validator.log_response(request_id=request_id, status_code=status_code, data=data, duration_ms=duration_ms, error=error)


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
async def validate_grammar(request: GrammarRequest, http_request: Request) -> GrammarResponse:
    """Validate a grammar and return any errors."""
    start_time = time.time()

    # Validate request structure
    request_data = request.model_dump()
    validation_errors = api_validator.validate_grammar_request(request_data)
    if validation_errors:
        logger.error(f"❌ Invalid grammar request: {validation_errors}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {'; '.join(validation_errors)}")

    # Generate request ID and log
    request_id = validate_and_log_request(http_request, "/grammar/validate", request_data)
    log_api_request("POST", "/grammar/validate", {"start_symbol": request.start_symbol})

    try:
        # Parse grammar using Lark
        grammar, lark_errors = parse_grammar_with_lark_v2(request.grammar_text, request.start_symbol)

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
                logger.info("Building automaton and parsing table")
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
                        "transitions": [],
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

                    # Add transitions from this state
                    for transition in automaton.get_transitions_from_state(i):
                        state_info["transitions"].append(
                            {
                                "to_state": transition.to_state,
                                "symbol": transition.symbol.name,
                            }
                        )

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

                logger.info("Automaton and table built successfully")

                response = GrammarResponse(valid=True, errors=[], grammar_info=grammar_info)
                duration_ms = (time.time() - start_time) * 1000
                validate_and_log_response(request_id, 200, response.model_dump(), duration_ms)
                return response

            except Exception as e:
                tb = traceback.format_exc()
                logger.error(f"Automaton/table build failed: {e}", extra={"trace": tb})
                response = GrammarResponse(
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
                duration_ms = (time.time() - start_time) * 1000
                validate_and_log_response(request_id, 200, response.model_dump(), duration_ms)
                return response
        else:
            response = GrammarResponse(valid=False, errors=error_dicts)
            duration_ms = (time.time() - start_time) * 1000
            validate_and_log_response(request_id, 200, response.model_dump(), duration_ms)
            return response

    except Exception as e:
        response = GrammarResponse(
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
        duration_ms = (time.time() - start_time) * 1000
        validate_and_log_response(request_id, 500, response.model_dump(), duration_ms, str(e))
        return response


@router.post("/parser/table")
async def get_parsing_table(request: GrammarRequest) -> TableResponse:
    """Generate parsing table for a grammar."""
    try:
        # Parse grammar using Lark
        grammar, lark_errors = parse_grammar_with_lark_v2(request.grammar_text, request.start_symbol)
        validation_errors = grammar.validate()
        errors = lark_errors + validation_errors

        if errors:
            _raise_grammar_validation_error(errors)

        # Build automaton and parsing table
        try:
            logger.info("Building automaton and parsing table (table endpoint)")
            automaton = Automaton(grammar)
            parsing_table = ParsingTable(automaton)
        except Exception as e:
            logger.error(f"Table build failed: {e}", extra={"trace": traceback.format_exc()})
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
        logger.error(f"/parser/table failed: {e}", extra={"trace": traceback.format_exc()})
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/parser/parse")
async def parse_input(request: ParsingRequest) -> ParsingResponse:
    """Parse input string using the given grammar."""
    try:
        # Parse grammar using Lark
        grammar, lark_errors = parse_grammar_with_lark_v2(request.grammar_text, request.start_symbol)
        validation_errors = grammar.validate()
        errors = lark_errors + validation_errors

        if errors:
            _raise_grammar_validation_error(errors)

        # Build automaton and parsing table
        try:
            logger.info("Building automaton and parsing table (parse endpoint)")
            automaton = Automaton(grammar)
            parsing_table = ParsingTable(automaton)
        except Exception as e:
            logger.error(f"Parse build failed: {e}", extra={"trace": traceback.format_exc()})
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
        logger.error(f"/parser/parse failed: {e}", extra={"trace": traceback.format_exc()})
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/examples")
async def get_example_grammars() -> dict[str, Any]:
    """Get example grammars for testing."""
    examples = {
        "arithmetic": {
            "name": "Arithmetic Expressions",
            "description": "Simple arithmetic expressions with +, -, *, /, parentheses and operator precedence",
            "grammar": """E -> E + T | E - T | T
T -> T * F | T / F | F
F -> ( E ) | id | num""",
            "start_symbol": "E",
            "sample_inputs": ["id + id * id", "id - num", "( id + num ) * id", "id / num + id", "( ( id + id ) * num ) - id"],
        },
        "simple_language": {
            "name": "Simple Programming Language",
            "description": "Basic language with statements, expressions, and control flow constructs",
            "grammar": """S -> stmt_list
stmt_list -> stmt stmt_list | stmt
stmt -> id = expr | if expr then stmt | while expr do stmt | { stmt_list }
expr -> expr + term | expr - term | term
term -> term * factor | term / factor | factor
factor -> id | num | ( expr )""",
            "start_symbol": "S",
            "sample_inputs": ["id = id + num", "if num then id = id", "while id do id = num", "{ id = num ; id = id + num }"],
        },
        "json": {
            "name": "JSON-like Structure",
            "description": "Simplified JSON structure with objects, arrays, and nested data",
            "grammar": """value -> object | array | string | number | true | false | null
object -> { pairs }
pairs -> pair pairs_tail | ε
pairs_tail -> , pair pairs_tail | ε
pair -> string : value
array -> [ elements ]
elements -> value elements_tail | ε
elements_tail -> , value elements_tail | ε""",
            "start_symbol": "value",
            "sample_inputs": [
                '{ "key" : "value" }',
                '[ "item1" , "item2" ]',
                "true",
                "{ }",
                '{ "name" : "John" , "age" : 25 }',
            ],
        },
        "boolean_expressions": {
            "name": "Boolean Expressions",
            "description": "Boolean logic with AND, OR, NOT operators and parentheses",
            "grammar": """expr -> expr OR term | term
term -> term AND factor | factor
factor -> NOT factor | ( expr ) | true | false | id""",
            "start_symbol": "expr",
            "sample_inputs": [
                "true OR false",
                "id AND NOT id",
                "( true OR false ) AND true",
                "NOT ( id OR false )",
                "true AND true OR false",
            ],
        },
        "simple_calculator": {
            "name": "Simple Calculator",
            "description": "Calculator with numbers, basic operations, and function calls",
            "grammar": """expr -> expr + term | expr - term | term
term -> term * factor | term / factor | factor
factor -> ( expr ) | num | function_call
function_call -> id ( expr )""",
            "start_symbol": "expr",
            "sample_inputs": [
                "num + num",
                "function_call ( num )",
                "( num + num ) * num",
                "num / function_call ( num )",
                "num - num + num",
            ],
        },
        "list_processing": {
            "name": "List Processing",
            "description": "Grammar for processing lists with elements and separators",
            "grammar": """list -> [ elements ]
elements -> element elements_tail | ε
elements_tail -> , element elements_tail | ε
element -> id | num | list""",
            "start_symbol": "list",
            "sample_inputs": ["[ id , num , id ]", "[ ]", "[ num ]", "[ id , [ id , num ] , id ]", "[ num , num , num ]"],
        },
        "conditional_statements": {
            "name": "Conditional Statements",
            "description": "If-then-else statements with boolean conditions",
            "grammar": """stmt -> if condition then stmt else stmt | id = expr | block
block -> { stmt_list }
stmt_list -> stmt stmt_list | stmt
condition -> expr relop expr
expr -> id | num
relop -> = | < | >""",
            "start_symbol": "stmt",
            "sample_inputs": [
                "if id = num then id = num else id = num",
                "{ id = num }",
                "if id < num then { id = num } else id = num",
                "id = num",
            ],
        },
        "recursive_descent": {
            "name": "Recursive Descent Example",
            "description": "Simple grammar demonstrating left recursion and recursive structure",
            "grammar": """S -> A
A -> A + B | B
B -> B * C | C
C -> ( A ) | id""",
            "start_symbol": "S",
            "sample_inputs": ["id", "id + id", "id * id", "id + id * id", "( id + id )"],
        },
        "nested_structures": {
            "name": "Nested Structures",
            "description": "Grammar with nested parentheses and bracket structures",
            "grammar": """structure -> ( content ) | [ content ] | { content }
content -> structure content | id | ε""",
            "start_symbol": "structure",
            "sample_inputs": ["( id )", "[ id ]", "{ id }", "( [ id ] )", "{ ( id ) }", "(( id ))"],
        },
        "assignment_language": {
            "name": "Assignment Language",
            "description": "Simple language with variable assignments and expressions",
            "grammar": """program -> stmt_list
stmt_list -> stmt ; stmt_list | stmt
stmt -> id = expr
expr -> expr + term | expr - term | term
term -> term * factor | term / factor | factor
factor -> id | num | ( expr )""",
            "start_symbol": "program",
            "sample_inputs": [
                "id = num",
                "id = id + num ; id = num",
                "id = ( id + num ) * num",
                "id = num ; id = id - num ; id = id * num",
            ],
        },
    }

    return {"examples": examples}


@router.get("/debug/logs")
async def get_debug_logs(format: str = "json", limit: int = 100) -> dict:
    """Get debug logs for troubleshooting."""
    try:
        if format == "json":
            logs = api_validator.get_recent_logs(limit)
            return {"logs": logs, "total": len(api_validator.request_logs)}
        elif format == "export":
            filepath = api_validator.export_logs("json")
            return {"message": f"Logs exported to {filepath}", "filepath": filepath}
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'json' or 'export'")
    except Exception as e:
        logger.error(f"Failed to get debug logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/debug/logs")
async def clear_debug_logs() -> dict:
    """Clear all debug logs."""
    try:
        api_validator.clear_logs()
        return {"message": "Debug logs cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear debug logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


@router.post("/parse/interactive", response_model=InteractiveDerivationResponse)
async def parse_interactive_derivation(
    request: InteractiveDerivationRequest, http_request: Request
) -> InteractiveDerivationResponse:
    """Parse input string with detailed interactive derivation steps."""
    start_time = time.time()

    # Validate request structure
    request_data = request.model_dump()
    validation_errors = api_validator.validate_parsing_request(request_data)
    if validation_errors:
        logger.error(f"❌ Invalid parsing request: {validation_errors}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {'; '.join(validation_errors)}")

    # Generate request ID and log
    request_id = validate_and_log_request(http_request, "/parse/interactive", request_data)
    log_api_request("parse_interactive_derivation", request.model_dump())

    try:
        # Parse grammar
        grammar, errors = parse_grammar_with_lark_v2(request.grammar_text, request.start_symbol)

        if errors:
            return InteractiveDerivationResponse(
                valid=False,
                error=f"Grammar parsing failed: {errors[0].message}",
                input_string=request.input_string,
                tokens=[],
                total_steps=0,
                success=False,
                steps=[],
                summary={"error": "Grammar parsing failed"},
            )

        # Create automaton and parsing table
        automaton = Automaton(grammar)
        table = ParsingTable(automaton)

        if table.has_conflicts():
            return InteractiveDerivationResponse(
                valid=False,
                error="Grammar has conflicts and cannot be parsed",
                input_string=request.input_string,
                tokens=[],
                total_steps=0,
                success=False,
                steps=[],
                summary={"error": "Grammar has conflicts"},
            )

        # Create parser engine
        engine = ParserEngine(grammar, table)

        # Parse with interactive derivation
        derivation_info = engine.parse_interactive(request.input_string)

        # Create summary
        summary = {
            "total_steps": derivation_info["total_steps"],
            "success": derivation_info["success"],
            "grammar_type": automaton.get_grammar_type(),
            "num_states": len(automaton.states),
            "num_productions": len(grammar.productions),
        }

        response = InteractiveDerivationResponse(
            valid=True,
            error=None,
            input_string=derivation_info["input_string"],
            tokens=derivation_info["tokens"],
            total_steps=derivation_info["total_steps"],
            success=derivation_info["success"],
            steps=derivation_info["steps"],
            summary=summary,
            ast=derivation_info.get("ast"),
        )

        duration_ms = (time.time() - start_time) * 1000
        validate_and_log_response(request_id, 200, response.model_dump(), duration_ms)
        log_api_response("parse_interactive_derivation", 200, response.model_dump())
        return response

    except Exception as e:
        error_msg = f"Interactive parsing failed: {str(e)}"
        logger.error(f"Interactive parsing error: {error_msg}\n{traceback.format_exc()}")

        response = InteractiveDerivationResponse(
            valid=False,
            error=error_msg,
            input_string=request.input_string,
            tokens=[],
            total_steps=0,
            success=False,
            steps=[],
            summary={"error": error_msg},
        )

        duration_ms = (time.time() - start_time) * 1000
        validate_and_log_response(request_id, 500, response.model_dump(), duration_ms, error_msg)
        log_api_response("parse_interactive_derivation", 200, response.model_dump())
        return response


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
