"""Tests for interactive string derivation functionality."""

import pytest
from fastapi.testclient import TestClient

from main import app
from parser.grammar_v2 import Grammar
from parser.automaton import Automaton
from parser.table import ParsingTable
from parser.engine import ParserEngine


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestInteractiveDerivationAPI:
    """Test interactive derivation API endpoints."""

    def test_parse_interactive_success(self, client):
        """Test successful interactive parsing."""
        data = {
            "grammar_text": """
            E: E "+" T | T
            T: T "*" F | F
            F: "(" E ")" | "id"
            """,
            "input_string": "id + id",
            "start_symbol": "E",
        }

        response = client.post("/api/v1/parse/interactive", json=data)

        assert response.status_code == 200
        result = response.json()

        # Check response structure
        assert result["valid"] is True
        assert result["error"] is None
        assert result["input_string"] == "id + id"
        assert result["tokens"] == ["id", "+", "id", "$"]
        assert result["success"] is True
        assert result["total_steps"] > 0
        assert isinstance(result["steps"], list)
        assert len(result["steps"]) > 0

        # Check step structure
        first_step = result["steps"][0]
        assert "step_number" in first_step
        assert "stack" in first_step
        assert "input_remaining" in first_step
        assert "current_token" in first_step
        assert "action" in first_step
        assert "explanation" in first_step
        assert "ast_nodes" in first_step
        assert "derivation_so_far" in first_step

        # Check action structure
        assert "type" in first_step["action"]
        assert "target" in first_step["action"]
        assert "description" in first_step["action"]

        # Check summary
        assert "total_steps" in result["summary"]
        assert "success" in result["summary"]
        assert "grammar_type" in result["summary"]
        assert "num_states" in result["summary"]
        assert "num_productions" in result["summary"]

    def test_parse_interactive_invalid_grammar(self, client):
        """Test interactive parsing with invalid grammar."""
        data = {"grammar_text": "invalid grammar syntax", "input_string": "id + id", "start_symbol": "E"}

        response = client.post("/api/v1/parse/interactive", json=data)

        assert response.status_code == 200
        result = response.json()

        assert result["valid"] is False
        assert result["error"] is not None
        assert "Grammar parsing failed" in result["error"]
        assert result["success"] is False
        assert result["total_steps"] == 0
        assert result["steps"] == []

    def test_parse_interactive_ambiguous_grammar(self, client):
        """Test interactive parsing with ambiguous grammar."""
        data = {
            "grammar_text": """
            S: S S | "a"
            """,
            "input_string": "a a",
            "start_symbol": "S",
        }

        response = client.post("/api/v1/parse/interactive", json=data)

        assert response.status_code == 200
        result = response.json()

        assert result["valid"] is False
        assert result["error"] is not None
        assert "Grammar has conflicts" in result["error"]
        assert result["success"] is False
        assert result["total_steps"] == 0
        assert result["steps"] == []

    def test_parse_interactive_invalid_input(self, client):
        """Test interactive parsing with invalid input string."""
        data = {
            "grammar_text": """
            E: E "+" T | T
            T: T "*" F | F
            F: "(" E ")" | "id"
            """,
            "input_string": "invalid + input",
            "start_symbol": "E",
        }

        response = client.post("/api/v1/parse/interactive", json=data)

        assert response.status_code == 200
        result = response.json()

        # Should still be valid but parsing should fail
        assert result["valid"] is True
        assert result["error"] is None
        assert result["success"] is False
        assert result["total_steps"] > 0

        # Check that last step is an error
        last_step = result["steps"][-1]
        assert last_step["action"]["type"] == "error"

    def test_parse_interactive_empty_input(self, client):
        """Test interactive parsing with empty input."""
        data = {
            "grammar_text": """
            S: "a" | ε
            """,
            "input_string": "",
            "start_symbol": "S",
        }

        response = client.post("/api/v1/parse/interactive", json=data)

        assert response.status_code == 200
        result = response.json()

        assert result["valid"] is True
        assert result["error"] is None
        assert result["tokens"] == ["$"]
        assert result["total_steps"] > 0

    def test_parse_interactive_complex_expression(self, client):
        """Test interactive parsing with complex expression."""
        data = {
            "grammar_text": """
            E: E "+" T | E "-" T | T
            T: T "*" F | T "/" F | F
            F: "(" E ")" | "id" | "num"
            """,
            "input_string": "id + id * id",
            "start_symbol": "E",
        }

        response = client.post("/api/v1/parse/interactive", json=data)

        assert response.status_code == 200
        result = response.json()

        assert result["valid"] is True
        assert result["error"] is None
        assert result["success"] is True
        assert result["total_steps"] > 0

        # Check that we have various action types
        action_types = {step["action"]["type"] for step in result["steps"]}
        assert "shift" in action_types
        assert "reduce" in action_types
        assert "accept" in action_types

    def test_parse_interactive_step_progression(self, client):
        """Test that steps progress correctly through parsing."""
        data = {
            "grammar_text": """
            E: E "+" T | T
            T: T "*" F | F
            F: "(" E ")" | "id"
            """,
            "input_string": "id + id",
            "start_symbol": "E",
        }

        response = client.post("/api/v1/parse/interactive", json=data)

        assert response.status_code == 200
        result = response.json()

        assert result["valid"] is True
        assert result["success"] is True

        steps = result["steps"]

        # Check step numbering
        for i, step in enumerate(steps):
            assert step["step_number"] == i + 1

        # Check that input_remaining decreases over time
        for i in range(len(steps) - 1):
            current_remaining = len(steps[i]["input_remaining"])
            next_remaining = len(steps[i + 1]["input_remaining"])
            assert current_remaining >= next_remaining

        # Check that stack changes appropriately
        for step in steps:
            assert isinstance(step["stack"], list)
            for stack_item in step["stack"]:
                assert isinstance(stack_item, list)
                assert len(stack_item) == 2
                assert isinstance(stack_item[0], int)  # state
                assert isinstance(stack_item[1], str)  # symbol

    def test_parse_interactive_derivation_tracking(self, client):
        """Test that derivation tracking works correctly."""
        data = {
            "grammar_text": """
            E: E "+" T | T
            T: T "*" F | F
            F: "(" E ")" | "id"
            """,
            "input_string": "id + id",
            "start_symbol": "E",
        }

        response = client.post("/api/v1/parse/interactive", json=data)

        assert response.status_code == 200
        result = response.json()

        assert result["valid"] is True
        assert result["success"] is True

        steps = result["steps"]

        # Check that derivation_so_far is provided for each step
        for step in steps:
            assert "derivation_so_far" in step
            assert isinstance(step["derivation_so_far"], str)

    def test_parse_interactive_ast_nodes(self, client):
        """Test that AST nodes are properly tracked."""
        data = {
            "grammar_text": """
            E: E "+" T | T
            T: T "*" F | F
            F: "(" E ")" | "id"
            """,
            "input_string": "id + id",
            "start_symbol": "E",
        }

        response = client.post("/api/v1/parse/interactive", json=data)

        assert response.status_code == 200
        result = response.json()

        assert result["valid"] is True
        assert result["success"] is True

        steps = result["steps"]

        # Check that AST nodes are provided
        for step in steps:
            assert "ast_nodes" in step
            assert isinstance(step["ast_nodes"], list)

            # Check AST node structure if present
            for node in step["ast_nodes"]:
                assert "id" in node
                assert "type" in node
                assert "symbol" in node
                assert "value" in node
                assert "children" in node


class TestInteractiveDerivationEngine:
    """Test interactive derivation engine directly."""

    def test_parse_interactive_engine_success(self):
        """Test engine parse_interactive method directly."""
        grammar_text = """
        E: E "+" T | T
        T: T "*" F | F
        F: "(" E ")" | "id"
        """
        grammar = Grammar.from_text(grammar_text, "E")
        automaton = Automaton(grammar)
        table = ParsingTable(automaton)
        engine = ParserEngine(grammar, table)

        result = engine.parse_interactive("id + id")

        assert result["input_string"] == "id + id"
        assert result["tokens"] == ["id", "+", "id", "$"]
        assert result["success"] is True
        assert result["total_steps"] > 0
        assert len(result["steps"]) > 0

        # Check step structure
        for step in result["steps"]:
            assert "step_number" in step
            assert "stack" in step
            assert "input_remaining" in step
            assert "current_token" in step
            assert "action" in step
            assert "explanation" in step
            assert "ast_nodes" in step
            assert "derivation_so_far" in step

    def test_parse_interactive_engine_error(self):
        """Test engine parse_interactive method with error."""
        grammar_text = """
        E: E "+" T | T
        T: T "*" F | F
        F: "(" E ")" | "id"
        """
        grammar = Grammar.from_text(grammar_text, "E")
        automaton = Automaton(grammar)
        table = ParsingTable(automaton)
        engine = ParserEngine(grammar, table)

        result = engine.parse_interactive("invalid input")

        assert result["input_string"] == "invalid input"
        assert result["success"] is False
        assert result["total_steps"] > 0

        # Check that last step is an error
        last_step = result["steps"][-1]
        assert last_step["action"]["type"] == "error"

    def test_parse_interactive_engine_epsilon(self):
        """Test engine parse_interactive method with epsilon production."""
        grammar_text = """
        S: "a" | ε
        """
        grammar = Grammar.from_text(grammar_text, "S")
        automaton = Automaton(grammar)
        table = ParsingTable(automaton)
        engine = ParserEngine(grammar, table)

        result = engine.parse_interactive("")

        assert result["input_string"] == ""
        assert result["tokens"] == ["$"]
        assert result["success"] is True
        assert result["total_steps"] > 0

    def test_action_description_formatting(self):
        """Test that action descriptions are properly formatted."""
        grammar_text = """
        E: E "+" T | T
        T: T "*" F | F
        F: "(" E ")" | "id"
        """
        grammar = Grammar.from_text(grammar_text, "E")
        automaton = Automaton(grammar)
        table = ParsingTable(automaton)
        engine = ParserEngine(grammar, table)

        result = engine.parse_interactive("id + id")

        for step in result["steps"]:
            action = step["action"]
            assert "description" in action
            assert isinstance(action["description"], str)
            assert len(action["description"]) > 0

            # Check specific action descriptions
            if action["type"] == "shift":
                assert "Shift to state" in action["description"]
            elif action["type"] == "reduce":
                assert "Reduce by" in action["description"]
            elif action["type"] == "accept":
                assert "Accept" in action["description"]
            elif action["type"] == "error":
                assert "Error" in action["description"]
