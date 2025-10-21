"""Data structure grammars for testing."""

# JSON-like structure
JSON_GRAMMAR = """
value: object | array | string | number | "true" | "false" | "null"
object: "{" pairs "}"
pairs: pair pairs_tail | ε
pairs_tail: "," pair pairs_tail | ε
pair: string ":" value
array: "[" elements "]"
elements: value elements_tail | ε
elements_tail: "," value elements_tail | ε
string: "\"" string_content "\""
string_content: string_char string_content | ε
string_char: /[^"\\]/
number: /[0-9]+/
"""

# XML-like structure
XML_GRAMMAR = """
document: element
element: "<" "id" ">" content "</" "id" ">" | "<" "id" "/>"
content: element content | text content | ε
text: /[^<]+/
"""

# CSV-like structure
CSV_GRAMMAR = """
csv: row csv_tail
csv_tail: "\n" row csv_tail | ε
row: field row_tail
row_tail: "," field row_tail | ε
field: quoted_field | unquoted_field
quoted_field: "\"" field_content "\""
field_content: field_char field_content | ε
field_char: /[^",]/
unquoted_field: /[^,\n]+/
"""

# SQL-like structure
SQL_GRAMMAR = """
query: select_stmt | insert_stmt | update_stmt | delete_stmt
select_stmt: "SELECT" columns "FROM" table where_clause
insert_stmt: "INSERT" "INTO" table "VALUES" "(" values ")"
update_stmt: "UPDATE" table "SET" assignments where_clause
delete_stmt: "DELETE" "FROM" table where_clause
columns: "*" | column_list
column_list: "id" column_tail
column_tail: "," "id" column_tail | ε
table: "id"
where_clause: "WHERE" condition | ε
condition: "id" "=" value
value: "id" | "num" | "string"
assignments: "id" "=" value assignment_tail
assignment_tail: "," "id" "=" value assignment_tail | ε
values: value value_tail
value_tail: "," value value_tail | ε
"""
