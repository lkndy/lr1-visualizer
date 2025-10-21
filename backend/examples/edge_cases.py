"""Edge case grammars for testing."""

# Ambiguous grammar
AMBIGUOUS_GRAMMAR = """
S: S S | "a"
"""

# Left recursive grammar
LEFT_RECURSIVE_GRAMMAR = """
E: E "+" T | T
T: T "*" F | F
F: "id"
"""

# Right recursive grammar
RIGHT_RECURSIVE_GRAMMAR = """
E: T "+" E | T
T: F "*" T | F
F: "id"
"""

# Epsilon productions
EPSILON_GRAMMAR = """
S: A B C
A: "a" | ε
B: "b" | ε
C: "c" | ε
"""

# Single production
SINGLE_PRODUCTION_GRAMMAR = """
S: "a"
"""

# Empty grammar (epsilon only)
EMPTY_GRAMMAR = """
S: ε
"""

# Very deep nesting
DEEP_NESTING_GRAMMAR = """
S: "(" S ")" | "a"
"""

# Many alternatives
MANY_ALTERNATIVES_GRAMMAR = """
S: "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h" | "i" | "j"
"""

# Long right-hand side
LONG_RHS_GRAMMAR = """
S: A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
A: "a"
B: "b"
C: "c"
D: "d"
E: "e"
F: "f"
G: "g"
H: "h"
I: "i"
J: "j"
K: "k"
L: "l"
M: "m"
N: "n"
O: "o"
P: "p"
Q: "q"
R: "r"
S: "s"
T: "t"
U: "u"
V: "v"
W: "w"
X: "x"
Y: "y"
Z: "z"
"""

# Circular grammar
CIRCULAR_GRAMMAR = """
A: B
B: C
C: A
"""

# Self-referencing grammar
SELF_REF_GRAMMAR = """
A: A
"""
