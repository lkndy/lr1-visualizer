"""FastAPI routes for LR(1) parser endpoints."""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ..parser import Grammar, Automaton, ParsingTable, ParserEngine
from ..parser.types import GrammarError, ConflictInfo


# Request/Response models
class GrammarRequest(BaseModel):
    """Request model for grammar validation."""
    grammar_text: str
    start_symbol: str = "S"


class GrammarResponse(BaseModel):
    """Response model for grammar validation."""
    valid: bool
    errors: List[Dict[str, Any]]
    grammar_info: Optional[Dict[str, Any]] = None


class ParsingRequest(BaseModel):
    """Request model for parsing."""
    grammar_text: str
    input_string: str
    start_symbol: str = "S"


class ParsingResponse(BaseModel):
    """Response model for parsing."""
    valid: bool
    error: Optional[str] = None
    steps: List[Dict[str, Any]]
    ast: Optional[Dict[str, Any]] = None
    summary: Dict[str, Any]


class TableResponse(BaseModel):
    """Response model for parsing table."""
    action_table: Dict[str, Any]
    goto_table: Dict[str, Any]
    summary: Dict[str, Any]
    conflicts: List[Dict[str, Any]]


# Create router
router = APIRouter(prefix="/api/v1", tags=["parser"])


@router.post("/grammar/validate", response_model=GrammarResponse)
async def validate_grammar(request: GrammarRequest) -> GrammarResponse:
    """Validate a grammar and return any errors."""
    try:
        # Parse grammar from text
        grammar = Grammar.from_string(request.grammar_text, request.start_symbol)
        
        # Validate grammar
        errors = grammar.validate()
        
        # Convert errors to dict format
        error_dicts = []
        for error in errors:
            error_dicts.append({
                "type": error.error_type,
                "message": error.message,
                "line_number": error.line_number,
                "symbol": error.symbol
            })
        
        if not errors:
            # Grammar is valid, build automaton and table
            try:
                automaton = Automaton(grammar)
                parsing_table = ParsingTable(automaton)
                
                grammar_info = {
                    "num_productions": len(grammar.productions),
                    "num_terminals": len(grammar.terminals),
                    "num_non_terminals": len(grammar.non_terminals),
                    "num_states": len(automaton.states),
                    "grammar_type": automaton.get_grammar_type(),
                    "has_conflicts": parsing_table.has_conflicts(),
                    "conflict_summary": parsing_table.get_conflict_summary()
                }
                
                return GrammarResponse(
                    valid=True,
                    errors=[],
                    grammar_info=grammar_info
                )
                
            except Exception as e:
                return GrammarResponse(
                    valid=False,
                    errors=[{
                        "type": "automaton_error",
                        "message": f"Error building automaton: {str(e)}",
                        "line_number": None,
                        "symbol": None
                    }]
                )
        else:
            return GrammarResponse(
                valid=False,
                errors=error_dicts
            )
            
    except Exception as e:
        return GrammarResponse(
            valid=False,
            errors=[{
                "type": "parse_error",
                "message": f"Error parsing grammar: {str(e)}",
                "line_number": None,
                "symbol": None
            }]
        )


@router.post("/parser/table", response_model=TableResponse)
async def get_parsing_table(request: GrammarRequest) -> TableResponse:
    """Generate parsing table for a grammar."""
    try:
        # Parse and validate grammar
        grammar = Grammar.from_string(request.grammar_text, request.start_symbol)
        errors = grammar.validate()
        
        if errors:
            raise HTTPException(
                status_code=400,
                detail=f"Grammar validation failed: {errors[0].message}"
            )
        
        # Build automaton and parsing table
        automaton = Automaton(grammar)
        parsing_table = ParsingTable(automaton)
        
        # Convert conflicts to dict format
        conflicts = []
        for conflict in parsing_table.conflicts:
            conflicts.append({
                "state": conflict.state,
                "symbol": conflict.symbol,
                "actions": [
                    {
                        "type": action.action_type.value,
                        "target": action.target
                    } for action in conflict.actions
                ],
                "conflict_type": conflict.conflict_type
            })
        
        return TableResponse(
            action_table=parsing_table.export_action_table(),
            goto_table=parsing_table.export_goto_table(),
            summary=parsing_table.get_table_summary(),
            conflicts=conflicts
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parser/parse", response_model=ParsingResponse)
async def parse_input(request: ParsingRequest) -> ParsingResponse:
    """Parse input string using the given grammar."""
    try:
        # Parse and validate grammar
        grammar = Grammar.from_string(request.grammar_text, request.start_symbol)
        errors = grammar.validate()
        
        if errors:
            raise HTTPException(
                status_code=400,
                detail=f"Grammar validation failed: {errors[0].message}"
            )
        
        # Build automaton and parsing table
        automaton = Automaton(grammar)
        parsing_table = ParsingTable(automaton)
        
        if parsing_table.has_conflicts():
            raise HTTPException(
                status_code=400,
                detail="Grammar has conflicts and cannot be used for parsing"
            )
        
        # Create parser engine and parse input
        parser_engine = ParserEngine(grammar, parsing_table)
        validation_result = parser_engine.validate_input(request.input_string)
        
        summary = parser_engine.get_parsing_summary(request.input_string)
        
        return ParsingResponse(
            valid=validation_result["valid"],
            error=validation_result["error"],
            steps=validation_result["steps"],
            ast=validation_result["ast"],
            summary=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/examples")
async def get_example_grammars() -> Dict[str, Any]:
    """Get example grammars for testing."""
    examples = {
        "arithmetic": {
            "name": "Arithmetic Expressions",
            "description": "Simple arithmetic expressions with +, -, *, /, parentheses",
            "grammar": """E -> E + T | E - T | T
T -> T * F | T / F | F
F -> ( E ) | id | num""",
            "start_symbol": "E",
            "example_input": "id + id * id"
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
            "example_input": "id = id + num"
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
            "example_input": "{ \"key\" : \"value\" }"
        }
    }
    
    return {"examples": examples}


# WebSocket endpoint for real-time parsing
class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@router.websocket("/ws/parse")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time parsing updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            # Parse the data (assuming it's JSON with grammar and input)
            import json
            try:
                request_data = json.loads(data)
                grammar_text = request_data.get("grammar_text", "")
                input_string = request_data.get("input_string", "")
                start_symbol = request_data.get("start_symbol", "S")
                
                # Create parsing request
                parse_request = ParsingRequest(
                    grammar_text=grammar_text,
                    input_string=input_string,
                    start_symbol=start_symbol
                )
                
                # Get parsing result
                result = await parse_input(parse_request)
                
                # Send result back to client
                await manager.send_personal_message(
                    json.dumps(result.dict()), 
                    websocket
                )
                
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({"error": "Invalid JSON format"}),
                    websocket
                )
            except Exception as e:
                await manager.send_personal_message(
                    json.dumps({"error": str(e)}),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
