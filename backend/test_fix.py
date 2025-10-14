#!/usr/bin/env python3
"""Test script to verify the table generation fix."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parser.grammar import Grammar
from parser.automaton import Automaton
from parser.table import ParsingTable

def test_table_generation():
    """Test that the ACTION table is properly populated."""
    grammar_text = """E -> E + T | E - T | T
T -> T * F | T / F | F
F -> ( E ) | id | num"""
    
    print("Creating grammar...")
    grammar = Grammar.from_string(grammar_text, "E")
    
    print("Building automaton...")
    automaton = Automaton(grammar)
    print(f"Automaton has {len(automaton.states)} states")
    
    print("Building parsing table...")
    parsing_table = ParsingTable(automaton)
    print(f"Action table has {len(parsing_table.action_table)} entries")
    print(f"Goto table has {len(parsing_table.goto_table)} entries")
    
    # Check that we have action entries
    assert len(parsing_table.action_table) > 0, "ACTION table should not be empty"
    assert len(parsing_table.goto_table) > 0, "GOTO table should not be empty"
    
    # Check that we have shift and reduce actions
    shift_actions = [action for action in parsing_table.action_table.values() if action.action_type.value == "shift"]
    reduce_actions = [action for action in parsing_table.action_table.values() if action.action_type.value == "reduce"]
    accept_actions = [action for action in parsing_table.action_table.values() if action.action_type.value == "accept"]
    
    print(f"Found {len(shift_actions)} shift actions")
    print(f"Found {len(reduce_actions)} reduce actions")
    print(f"Found {len(accept_actions)} accept actions")
    
    assert len(shift_actions) > 0, "Should have shift actions"
    assert len(reduce_actions) > 0, "Should have reduce actions"
    assert len(accept_actions) > 0, "Should have accept actions"
    
    # Test export
    action_table_export = parsing_table.export_action_table()
    print(f"Export has {len(action_table_export['rows'])} rows")
    print(f"Export has {len(action_table_export['headers'])} headers")
    
    # Check that exported table has non-empty cells
    non_empty_cells = 0
    for row in action_table_export['rows']:
        for cell in row[1:]:  # Skip state column
            if cell and cell != "":
                non_empty_cells += 1
    
    print(f"Export has {non_empty_cells} non-empty cells")
    assert non_empty_cells > 0, "Exported table should have non-empty cells"
    
    print("✅ All tests passed! Table generation is working correctly.")

if __name__ == "__main__":
    test_table_generation()
