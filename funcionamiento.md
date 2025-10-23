# 📚 Parser LR(1) - Guía Completa

> **Explicación detallada del análisis sintáctico LR(1) y su implementación**

---

## 📋 Tabla de Contenidos

1. [¿Qué es LR(1)?](#qué-es-lr1)
2. [Visión General del Sistema](#visión-general-del-sistema)
3. [Componentes Principales](#componentes-principales)
4. [Construcción del Autómata](#construcción-del-autómata)
5. [Operaciones CLOSURE y GOTO](#operaciones-closure-y-goto)
6. [Tabla de Parsing](#tabla-de-parsing)
7. [Motor de Parsing](#motor-de-parsing)
8. [Ejemplo Completo: "id + num"](#ejemplo-completo-id--num)
9. [Detección de Conflictos](#detección-de-conflictos)
10. [Referencia de API](#referencia-de-api)

---

## 🎯 ¿Qué es LR(1)?

**LR(1)** es un algoritmo de parsing (análisis sintáctico) que significa:
- **L**: Lee la entrada de izquierda a derecha (**L**eft to right)
- **R**: Construye una derivación por la derecha en reversa (**R**ightmost derivation in reverse)
- **(1)**: Usa **1** símbolo de lookahead (mira 1 token adelante)

### Características Principales

✅ **Parser ascendente (bottom-up)**: Construye el árbol desde las hojas hacia la raíz  
✅ **Eficiente**: Complejidad O(n) en tiempo de parsing  
✅ **Potente**: Reconoce más gramáticas que LL(k)  
✅ **Determinista**: No hay backtracking  
✅ **Detección temprana de errores**: Identifica errores sintácticos inmediatamente  

### ¿Por qué LR(1)?

```
┌─────────────────┬──────────────┬────────────────────────┐
│   Tipo Parser   │  Potencia    │    Gramáticas que      │
│                 │              │      reconoce          │
├─────────────────┼──────────────┼────────────────────────┤
│ LL(1)           │ Limitada     │ Gramáticas simples     │
│ LR(0)           │ Básica       │ Muy restrictivas       │
│ SLR(1)          │ Moderada     │ Gramáticas básicas     │
│ LALR(1)         │ Alta         │ Mayoría de gramáticas  │
│ LR(1) ⭐        │ Máxima       │ Casi todas las         │
│                 │              │ gramáticas prácticas   │
└─────────────────┴──────────────┴────────────────────────┘
```

---

## 🏗️ Visión General del Sistema

### Flujo Completo

```
┌────────────────────────────────────────────────────────────┐
│                     USUARIO                                 │
│                        ↓                                    │
│               Texto de Gramática                            │
│         "S -> E                                             │
│          E -> E + T | T                                     │
│          T -> id"                                           │
└──────────────────────┬─────────────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────────┐
│  FASE 1: PARSING DE GRAMÁTICA                             │
│  📄 lark_grammar_v2.py                                    │
│                                                            │
│  • Usa Lark para parsear la sintaxis BNF/EBNF            │
│  • Identifica símbolos (terminales/no-terminales)         │
│  • Crea producciones                                       │
│  • Agrega producción aumentada: S' → S                    │
└──────────────────────┬───────────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────────┐
│  FASE 2: OBJETO GRAMMAR                                   │
│  📚 grammar_v2.py                                         │
│                                                            │
│  Grammar {                                                 │
│    productions: [S' → S, S → E, E → E + T, ...]          │
│    terminals: {id, num, +, -, *, /, (, )}                │
│    non_terminals: {S', S, E, T, F}                        │
│    first_sets: {...}   ← Calculados                       │
│    follow_sets: {...}  ← Calculados                       │
│  }                                                         │
└──────────────────────┬───────────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────────┐
│  FASE 3: CONSTRUCCIÓN DEL AUTÓMATA                        │
│  🏗️ automaton.py                                          │
│                                                            │
│  1. Crear ítem inicial: [S' → ·S, $]                     │
│  2. Calcular CLOSURE(I₀)                                  │
│  3. Para cada símbolo X:                                  │
│     • Calcular GOTO(I, X)                                 │
│     • Si es nuevo estado, agregarlo                       │
│  4. Repetir hasta procesar todos los estados              │
│                                                            │
│  Resultado:                                                │
│    • N estados (ItemSets)                                 │
│    • M transiciones                                       │
└──────────────────────┬───────────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────────┐
│  FASE 4: TABLA DE PARSING                                 │
│  📋 table.py                                              │
│                                                            │
│  Para cada estado:                                         │
│    • Ítems completos → ACTION[estado, lookahead] = Reduce │
│    • Transiciones terminales → ACTION[estado, t] = Shift  │
│    • Transiciones no-terminales → GOTO[estado, NT] = n    │
│                                                            │
│  Resultado:                                                │
│    • ACTION table: (estado, terminal) → acción            │
│    • GOTO table: (estado, no-terminal) → estado           │
│    • Conflictos detectados                                │
└──────────────────────┬───────────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────────┐
│  FASE 5: MOTOR DE PARSING                                 │
│  ⚙️ engine.py                                             │
│                                                            │
│  ParserEngine.parse("id + num"):                          │
│    Stack: [(estado, símbolo), ...]                        │
│    Input: [tokens...]                                     │
│                                                            │
│    Loop:                                                   │
│      1. Consultar ACTION[estado_actual, token_actual]     │
│      2. Si SHIFT: push token, avanzar pointer             │
│      3. Si REDUCE: pop RHS, consultar GOTO, push LHS      │
│      4. Si ACCEPT: ¡Éxito!                                │
│      5. Construir AST mientras parsea                     │
└──────────────────────┬───────────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────────┐
│  SALIDA: AST (Abstract Syntax Tree)                       │
│                                                            │
│           S                                                │
│           |                                                │
│           E                                                │
│          /|\                                               │
│         E + T                                              │
│         |   |                                              │
│         T   F                                              │
│         |   |                                              │
│         F  num                                             │
│         |                                                  │
│        id                                                  │
└───────────────────────────────────────────────────────────┘
```

---

## 🧩 Componentes Principales

### 1. Ítems LR(1) (`items.py`)

Un **ítem LR(1)** es una producción con:
- Un **punto (·)** que indica la posición de parsing
- Un **símbolo de lookahead** (terminal)

**Formato:** `[A → α·β, a]`
- `A`: No-terminal de la izquierda
- `α`: Símbolos antes del punto (ya procesados)
- `β`: Símbolos después del punto (por procesar)
- `a`: Lookahead (siguiente token esperado)

```python
@dataclass(frozen=True)
class LR1Item:
    production: Production  # A → αβ
    dot_position: int       # Posición del punto
    lookahead: Symbol       # Símbolo de lookahead

# Ejemplo:
item = LR1Item(
    production=Production(E, [E, plus, T]),
    dot_position=1,  # E → E · + T
    lookahead=Symbol("$", TERMINAL)
)
# Representa: [E → E · + T, $]
```

**Propiedades importantes:**

```python
# ¿Qué símbolo viene después del punto?
item.symbol_after_dot  # Retorna: plus

# ¿El ítem está completo? (punto al final)
item.is_complete  # False

# ¿Es un ítem de reducción?
item.is_reduce_item  # False

# Avanzar el punto una posición
item.advance_dot()  # [E → E + · T, $]
```

### 2. Conjuntos de Ítems (`ItemSet`)

Un **ItemSet** es un conjunto de ítems LR(1) que representan un **estado** del autómata.

```python
class ItemSet:
    items: frozenset[LR1Item]  # Conjunto inmutable de ítems
    
    def closure(self, grammar) -> ItemSet:
        """Calcula el cierre del conjunto de ítems"""
        
    def goto(self, grammar, symbol) -> ItemSet:
        """Calcula GOTO(I, X) - siguiente estado"""
        
    def get_reduce_items(self) -> list[LR1Item]:
        """Obtiene ítems completos (para reducción)"""
        
    def get_shift_symbols(self) -> set[Symbol]:
        """Obtiene símbolos que pueden ser shifteados"""
```

**Ejemplo:**

```python
I₀ = ItemSet({
    [S' → ·S, $],
    [S → ·E, $],
    [E → ·E + T, $],
    [E → ·T, $],
    [T → ·id, $]
})

# Símbolos que se pueden shiftear:
I₀.get_shift_symbols()  # {S, E, T, id}

# Calcular siguiente estado:
I₁ = I₀.goto(grammar, Symbol("id"))
# Resultado: {[T → id·, $]}
```

### 3. Autómata LR(1) (`automaton.py`)

El **autómata** es la colección canónica de conjuntos de ítems LR(1).

```python
class Automaton:
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.states: list[ItemSet] = []
        self.transitions: list[StateTransition] = []
        self.state_map: dict[ItemSet, int] = {}
        
        self._build_automaton()  # Construye todo
```

**Algoritmo de construcción:**

```python
def _build_automaton(self):
    # 1. Agregar FIRST/FOLLOW al grammar
    self._add_first_computation()
    self._add_follow_computation()
    
    # 2. Crear ítem inicial: [S' → ·S, $]
    initial_item = LR1Item(
        production=grammar.productions[0],
        dot_position=0,
        lookahead=Symbol("$", TERMINAL)
    )
    
    # 3. Calcular CLOSURE del ítem inicial
    I₀ = ItemSet.from_initial_item(initial_item, grammar)
    
    # 4. Inicializar estructuras
    self.states = [I₀]
    self.state_map[I₀] = 0
    worklist = [0]
    
    # 5. Algoritmo BFS (worklist)
    while worklist:
        state_index = worklist.pop(0)
        current_state = self.states[state_index]
        
        # Para cada símbolo que se puede shiftear
        for symbol in current_state.get_shift_symbols():
            # Calcular GOTO
            goto_state = current_state.goto(grammar, symbol)
            
            if goto_state:
                # ¿Es un estado nuevo?
                if goto_state not in self.state_map:
                    # Agregar nuevo estado
                    new_index = len(self.states)
                    self.states.append(goto_state)
                    self.state_map[goto_state] = new_index
                    worklist.append(new_index)
                    target_index = new_index
                else:
                    target_index = self.state_map[goto_state]
                
                # Agregar transición
                self.transitions.append(
                    StateTransition(state_index, target_index, symbol)
                )
```

### 4. Tabla de Parsing (`table.py`)

La **tabla de parsing** convierte el autómata en tablas ACTION y GOTO.

```python
class ParsingTable:
    def __init__(self, automaton: Automaton):
        self.automaton = automaton
        self.action_table: dict[tuple[int, str], ParsingAction] = {}
        self.goto_table: dict[tuple[int, str], int] = {}
        self.conflicts: list[ConflictInfo] = []
        
        self._build_tables()
```

**Construcción:**

```python
def _build_tables(self):
    for state_index, state in enumerate(self.automaton.states):
        # 1. Procesar ítems de reducción
        for item in state.get_reduce_items():
            if item.production == grammar.productions[0]:
                # S' → S· → ACCEPT
                self.action_table[(state_index, '$')] = ACCEPT
            else:
                # Reduce por producción N
                prod_idx = grammar.productions.index(item.production)
                self.action_table[(state_index, item.lookahead.name)] = \
                    ParsingAction(REDUCE, prod_idx)
        
        # 2. Procesar acciones shift (transiciones con terminales)
        for transition in automaton.get_transitions_from_state(state_index):
            if transition.symbol.is_terminal:
                self.action_table[(state_index, transition.symbol.name)] = \
                    ParsingAction(SHIFT, transition.to_state)
        
        # 3. Procesar GOTO (transiciones con no-terminales)
        for transition in automaton.get_transitions_from_state(state_index):
            if transition.symbol.is_non_terminal:
                self.goto_table[(state_index, transition.symbol.name)] = \
                    transition.to_state
```

### 5. Motor de Parsing (`engine.py`)

El **motor** ejecuta el algoritmo de parsing usando las tablas.

```python
class ParserEngine:
    def __init__(self, grammar: Grammar, parsing_table: ParsingTable):
        self.grammar = grammar
        self.parsing_table = parsing_table
    
    def parse(self, input_string: str) -> list[ParsingStep]:
        # Tokenizar
        tokens = self._tokenize(input_string)
        
        # Estado inicial
        stack = [(0, '')]
        pointer = 0
        steps = []
        
        while True:
            state = stack[-1][0]
            token = tokens[pointer]
            
            # Consultar ACTION
            action = self.parsing_table.get_action(state, token)
            
            if action.type == SHIFT:
                # Empujar token y cambiar estado
                stack.append((action.target, token))
                pointer += 1
                
            elif action.type == REDUCE:
                # Obtener producción
                production = grammar.productions[action.target]
                
                # Pop |RHS| elementos
                for _ in range(len(production.rhs)):
                    stack.pop()
                
                # Consultar GOTO
                prev_state = stack[-1][0]
                new_state = self.parsing_table.get_goto(
                    prev_state, 
                    production.lhs.name
                )
                
                # Push LHS
                stack.append((new_state, production.lhs.name))
                
            elif action.type == ACCEPT:
                # ¡Éxito!
                break
                
            else:
                # Error sintáctico
                raise ParseError(f"Unexpected token: {token}")
            
            steps.append(ParsingStep(...))
        
        return steps
```

---

## 🏗️ Construcción del Autómata

### Paso 1: Ítem Inicial

```python
# Gramática:
# S' → S    (producción aumentada)
# S → E
# E → E + T
# E → T
# T → id

# Crear ítem inicial
initial_item = [S' → ·S, $]
```

### Paso 2: CLOSURE del Ítem Inicial

**Algoritmo CLOSURE:**

```
CLOSURE(I):
  repeat:
    for cada ítem [A → α·Bβ, a] en I:
      if B es no-terminal:
        for cada producción B → γ:
          for cada b en FIRST(βa):
            agregar [B → ·γ, b] a I
  until no cambios
```

**Ejecución:**

```python
I₀ = {[S' → ·S, $]}

# Iteración 1: S es no-terminal después del punto
# Producción: S → E
# FIRST(ε $) = {$}
I₀ = {
    [S' → ·S, $],
    [S → ·E, $]  # ← Agregado
}

# Iteración 2: E es no-terminal
# Producciones: E → E + T, E → T
# FIRST(ε $) = {$}
I₀ = {
    [S' → ·S, $],
    [S → ·E, $],
    [E → ·E + T, $],  # ← Agregado
    [E → ·T, $]       # ← Agregado
}

# Iteración 3: E es no-terminal en [E → ·E + T, $]
# β = [+, T], a = $
# FIRST(+ T $) = {+}
I₀ = {
    [S' → ·S, $],
    [S → ·E, $],
    [E → ·E + T, $],
    [E → ·E + T, +],  # ← Agregado con lookahead +
    [E → ·T, $],
    [E → ·T, +]       # ← Agregado con lookahead +
}

# Continúa hasta que no hay cambios...

# CLOSURE final de I₀
I₀ = {
    [S' → ·S, $],
    [S → ·E, $],
    [E → ·E + T, $],
    [E → ·E + T, +],
    [E → ·E + T, -],
    [E → ·E + T, *],
    [E → ·T, $],
    [E → ·T, +],
    [E → ·T, -],
    [E → ·T, *],
    [T → ·id, $],
    [T → ·id, +],
    [T → ·id, -],
    [T → ·id, *]
}
```

### Paso 3: Calcular GOTO

**Algoritmo GOTO:**

```
GOTO(I, X):
  J = {}
  for cada ítem [A → α·Xβ, a] en I:
    agregar [A → αX·β, a] a J
  return CLOSURE(J)
```

**Ejemplo: GOTO(I₀, id)**

```python
# Buscar ítems con 'id' después del punto
# [T → ·id, $]  → [T → id·, $]
# [T → ·id, +]  → [T → id·, +]
# [T → ·id, -]  → [T → id·, -]
# [T → ·id, *]  → [T → id·, *]

J = {
    [T → id·, $],
    [T → id·, +],
    [T → id·, -],
    [T → id·, *]
}

# CLOSURE(J)
# Todos los ítems están completos (punto al final)
# No se agregan más ítems

I₅ = {
    [T → id·, $],
    [T → id·, +],
    [T → id·, -],
    [T → id·, *]
}

# Crear transición: Estado 0 --id--> Estado 5
```

**Ejemplo: GOTO(I₀, E)**

```python
# Buscar ítems con 'E' después del punto
# [S → ·E, $]       → [S → E·, $]
# [E → ·E + T, $]   → [E → E· + T, $]
# [E → ·E + T, +]   → [E → E· + T, +]
# ...

J = {
    [S → E·, $],
    [E → E· + T, $],
    [E → E· + T, +],
    [E → E· + T, -],
    [E → E· + T, *]
}

# CLOSURE(J)
# Los símbolos después del punto son '+', '-', etc. (terminales)
# No se agregan más ítems

I₁ = {
    [S → E·, $],
    [E → E· + T, $],
    [E → E· + T, +],
    [E → E· + T, -],
    [E → E· + T, *]
}

# Crear transición: Estado 0 --E--> Estado 1
```

### Paso 4: Algoritmo Worklist (BFS)

```python
states = [I₀]
state_map = {I₀: 0}
worklist = [0]

while worklist:
    current_index = worklist.pop(0)
    current_state = states[current_index]
    
    # Obtener símbolos que se pueden shiftear
    shift_symbols = current_state.get_shift_symbols()
    # Para I₀: {S, E, T, id}
    
    for symbol in shift_symbols:
        # Calcular GOTO
        goto_state = current_state.goto(grammar, symbol)
        
        if goto_state:
            # ¿Es un estado nuevo?
            if goto_state not in state_map:
                new_index = len(states)
                states.append(goto_state)
                state_map[goto_state] = new_index
                worklist.append(new_index)  # Procesar después
                target_index = new_index
            else:
                target_index = state_map[goto_state]
            
            # Agregar transición
            transitions.append(
                StateTransition(current_index, target_index, symbol)
            )
```

**Resultado:**

```
Estado 0: I₀ (ítem inicial + CLOSURE)
  Transiciones: S→1, E→2, T→3, id→5
  
Estado 1: GOTO(I₀, S)
  Contiene: [S' → S·, $]
  Acción: ACCEPT
  
Estado 2: GOTO(I₀, E)
  Transiciones: +→8, -→9
  Reduce con $: S → E
  
Estado 3: GOTO(I₀, T)
  Transiciones: *→10, /→11
  Reduce: E → T
  
Estado 5: GOTO(I₀, id)
  Reduce: T → id
  
... (más estados)
```

---

## ⚙️ Operaciones CLOSURE y GOTO

### CLOSURE

**Definición:** El CLOSURE de un conjunto de ítems I es el conjunto de todos los ítems que se pueden derivar de I aplicando la regla de closure.

**Regla de Closure:**
```
Si [A → α·Bβ, a] ∈ CLOSURE(I) y B → γ es una producción,
entonces [B → ·γ, b] ∈ CLOSURE(I) para todo b ∈ FIRST(βa)
```

**Implementación:**

```python
def closure(self, grammar: Grammar) -> ItemSet:
    items = set(self.items)
    changed = True
    
    while changed:
        changed = False
        new_items = set()
        
        for item in items:
            # ¿Hay no-terminal después del punto?
            symbol_after_dot = item.symbol_after_dot
            
            if symbol_after_dot and grammar.is_non_terminal(symbol_after_dot):
                B = symbol_after_dot
                beta = item.beta[1:]  # Símbolos después de B
                
                # Calcular FIRST(βa)
                first_beta_a = grammar.first((*beta, item.lookahead))
                
                # Para cada producción B → γ
                for production in grammar.get_productions_for_symbol(B):
                    # Para cada terminal b en FIRST(βa)
                    for terminal in first_beta_a:
                        if terminal.is_terminal:
                            new_item = LR1Item(
                                production=production,
                                dot_position=0,
                                lookahead=terminal
                            )
                            
                            if new_item not in items:
                                new_items.add(new_item)
                                changed = True
        
        items.update(new_items)
    
    return ItemSet(items)
```

**Ejemplo Visual:**

```
Input: {[E → ·E + T, $]}

┌─────────────────────────────────────┐
│ [E → ·E + T, $]                     │ ← Ítem inicial
└─────────────┬───────────────────────┘
              │ E es no-terminal
              │ β = [+, T], a = $
              │ FIRST(+ T $) = {+}
              ↓
┌─────────────────────────────────────┐
│ [E → ·E + T, $]                     │
│ [E → ·E + T, +]  ← Agregado         │
│ [E → ·T, +]      ← Agregado         │
└─────────────┬───────────────────────┘
              │ T es no-terminal
              │ FIRST($) = {$}
              ↓
┌─────────────────────────────────────┐
│ [E → ·E + T, $]                     │
│ [E → ·E + T, +]                     │
│ [E → ·T, +]                         │
│ [T → ·id, +]     ← Agregado         │
└─────────────────────────────────────┘
```

### GOTO

**Definición:** GOTO(I, X) es el conjunto de ítems que resulta de "avanzar" el punto sobre el símbolo X.

**Fórmula:**
```
GOTO(I, X) = CLOSURE({[A → αX·β, a] | [A → α·Xβ, a] ∈ I})
```

**Implementación:**

```python
def goto(self, grammar: Grammar, symbol: Symbol) -> ItemSet:
    goto_items = set()
    
    # Buscar ítems con 'symbol' después del punto
    for item in self.items:
        if item.symbol_after_dot == symbol:
            # Avanzar el punto
            advanced_item = item.advance_dot()
            goto_items.add(advanced_item)
    
    if not goto_items:
        return None
    
    # Calcular CLOSURE
    return ItemSet(goto_items).closure(grammar)
```

**Ejemplo Visual:**

```
Estado I₀:
┌─────────────────────────────────────┐
│ [S' → ·S, $]                        │
│ [S → ·E, $]                         │
│ [E → ·E + T, $]                     │
│ [E → ·T, $]                         │
│ [T → ·id, $]                        │
└─────────────────────────────────────┘
                 │
                 │ GOTO(I₀, id)
                 ↓
┌─────────────────────────────────────┐
│ Ítems con 'id' después del punto:   │
│ [T → ·id, $] → [T → id·, $]        │
└─────────────┬───────────────────────┘
              │ CLOSURE
              ↓
┌─────────────────────────────────────┐
│ Estado I₁:                          │
│ [T → id·, $]                        │
│ (No se agregan más ítems)           │
└─────────────────────────────────────┘
```

---

## 📋 Tabla de Parsing

### Construcción de ACTION

La tabla ACTION define qué hacer cuando vemos un terminal en un estado dado.

**Algoritmo:**

```python
for cada estado I:
    # 1. REDUCE / ACCEPT
    for cada ítem [A → α·, a] en I:  # Ítem completo
        if A = S' (producción aumentada):
            ACTION[I, a] = ACCEPT
        else:
            prod_idx = índice de (A → α)
            ACTION[I, a] = REDUCE prod_idx
    
    # 2. SHIFT
    for cada transición I --t--> J donde t es terminal:
        ACTION[I, t] = SHIFT J
```

**Ejemplo:**

```python
# Estado 0:
# Transiciones: id→5, num→6, (→7
ACTION[0, 'id']  = Shift 5
ACTION[0, 'num'] = Shift 6
ACTION[0, '(']   = Shift 7

# Estado 1:
# Ítem: [S' → S·, $]
ACTION[1, '$'] = Accept

# Estado 5:
# Ítems: [F → id·, $], [F → id·, +], [F → id·, -], ...
# Producción 9: F → id
ACTION[5, '$'] = Reduce 9
ACTION[5, '+'] = Reduce 9
ACTION[5, '-'] = Reduce 9
ACTION[5, '*'] = Reduce 9
ACTION[5, '/'] = Reduce 9
```

### Construcción de GOTO

La tabla GOTO define a dónde ir después de una reducción.

**Algoritmo:**

```python
for cada estado I:
    for cada transición I --N--> J donde N es no-terminal:
        GOTO[I, N] = J
```

**Ejemplo:**

```python
# Estado 0:
# Transiciones: S→1, E→2, T→3, F→4
GOTO[0, 'S'] = 1
GOTO[0, 'E'] = 2
GOTO[0, 'T'] = 3
GOTO[0, 'F'] = 4

# Estado 8: (después de ver E y +)
# Transiciones: T→13, F→4
GOTO[8, 'T'] = 13
GOTO[8, 'F'] = 4
```

### Tabla Completa (Ejemplo)

**ACTION:**
```
┌───────┬────────┬────────┬────────┬────────┬────────┬────────┬────────┐
│ State │   id   │  num   │   +    │   -    │   *    │   /    │   $    │
├───────┼────────┼────────┼────────┼────────┼────────┼────────┼────────┤
│   0   │  s5    │  s6    │        │        │        │        │        │
│   1   │        │        │        │        │        │        │  acc   │
│   2   │        │        │  s8    │  s9    │        │        │  r1    │
│   3   │        │        │  r4    │  r4    │  s10   │  s11   │  r4    │
│   4   │        │        │  r7    │  r7    │  r7    │  r7    │  r7    │
│   5   │        │        │  r9    │  r9    │  r9    │  r9    │  r9    │
│   6   │        │        │  r10   │  r10   │  r10   │  r10   │  r10   │
│   7   │  s5    │  s6    │        │        │        │        │        │
│   8   │  s5    │  s6    │        │        │        │        │        │
│  13   │        │        │  r2    │  r2    │  s10   │  s11   │  r2    │
└───────┴────────┴────────┴────────┴────────┴────────┴────────┴────────┘
```

**GOTO:**
```
┌───────┬────────┬────────┬────────┬────────┐
│ State │   S    │   E    │   T    │   F    │
├───────┼────────┼────────┼────────┼────────┤
│   0   │   1    │   2    │   3    │   4    │
│   7   │        │  12    │   3    │   4    │
│   8   │        │        │  13    │   4    │
│  10   │        │        │        │  15    │
└───────┴────────┴────────┴────────┴────────┘
```

---

## ⚙️ Motor de Parsing

### Algoritmo de Parsing

```python
def parse(input_string):
    tokens = tokenize(input_string) + ['$']
    stack = [(0, '')]
    pointer = 0
    
    while True:
        state = stack[-1][0]
        token = tokens[pointer]
        
        action = ACTION[state, token]
        
        if action == None:
            error("Syntax error")
        
        elif action.type == SHIFT:
            # Empujar token y cambiar estado
            stack.append((action.target, token))
            pointer += 1
        
        elif action.type == REDUCE:
            # Obtener producción
            production = grammar.productions[action.target]
            
            # Pop |RHS| elementos
            for _ in range(len(production.rhs)):
                stack.pop()
            
            # Consultar GOTO
            prev_state = stack[-1][0]
            new_state = GOTO[prev_state, production.lhs]
            
            # Push LHS
            stack.append((new_state, production.lhs))
        
        elif action.type == ACCEPT:
            return SUCCESS
```

### Construcción del AST

Durante el parsing, se construye el AST:

```python
# En cada SHIFT:
ast_node = ASTNode(
    id=f"node_{counter}",
    symbol=token,
    symbol_type=TERMINAL,
    children=[]
)
ast_stack.append(ast_node.id)

# En cada REDUCE:
production = grammar.productions[action.target]
children_ids = ast_stack[-len(production.rhs):]
ast_stack = ast_stack[:-len(production.rhs)]

parent_node = ASTNode(
    id=f"node_{counter}",
    symbol=production.lhs.name,
    symbol_type=NON_TERMINAL,
    children=children_ids
)
ast_stack.append(parent_node.id)
```

---

## 🎬 Ejemplo Completo: "id + num"

### Gramática

```
0: S' → S
1: S → E
2: E → E + T
3: E → T
4: T → id
5: T → num
```

### Tokens

```
['id', '+', 'num', '$']
```

### Pasos de Parsing

#### **Paso 0: Inicialización**

```
Stack:    [(0, '')]
Input:    [id, +, num, $]
Pointer:  0 (apuntando a 'id')
State:    0
Token:    'id'
Action:   ACTION[0, 'id'] = Shift 5
```

#### **Paso 1: Shift id**

```
Action:   Shift 5
Stack:    [(0, ''), (5, 'id')]
Pointer:  1 (apuntando a '+')
State:    5
Token:    '+'
Action:   ACTION[5, '+'] = Reduce 4 (T → id)

AST: Crear nodo terminal 'id'
```

#### **Paso 2: Reduce T → id**

```
Action:   Reduce 4 (T → id)
Pop:      1 elemento [(5, 'id')]
Stack:    [(0, '')]
Prev State: 0
GOTO:     GOTO[0, 'T'] = 3
Push:     (3, 'T')
Stack:    [(0, ''), (3, 'T')]
State:    3
Token:    '+' (sin avanzar pointer)
Action:   ACTION[3, '+'] = Reduce 3 (E → T)

AST: Crear nodo no-terminal 'T' con hijo 'id'
```

#### **Paso 3: Reduce E → T**

```
Action:   Reduce 3 (E → T)
Pop:      1 elemento [(3, 'T')]
Stack:    [(0, '')]
GOTO:     GOTO[0, 'E'] = 2
Push:     (2, 'E')
Stack:    [(0, ''), (2, 'E')]
State:    2
Token:    '+'
Action:   ACTION[2, '+'] = Shift 8

AST: Crear nodo no-terminal 'E' con hijo 'T'
```

#### **Paso 4: Shift +**

```
Action:   Shift 8
Stack:    [(0, ''), (2, 'E'), (8, '+')]
Pointer:  2 (apuntando a 'num')
State:    8
Token:    'num'
Action:   ACTION[8, 'num'] = Shift 6

AST: Crear nodo terminal '+'
```

#### **Paso 5: Shift num**

```
Action:   Shift 6
Stack:    [(0, ''), (2, 'E'), (8, '+'), (6, 'num')]
Pointer:  3 (apuntando a '$')
State:    6
Token:    '$'
Action:   ACTION[6, '$'] = Reduce 5 (T → num)

AST: Crear nodo terminal 'num'
```

#### **Paso 6: Reduce T → num**

```
Action:   Reduce 5 (T → num)
Pop:      1 elemento [(6, 'num')]
Stack:    [(0, ''), (2, 'E'), (8, '+')]
GOTO:     GOTO[8, 'T'] = 13
Push:     (13, 'T')
Stack:    [(0, ''), (2, 'E'), (8, '+'), (13, 'T')]
State:    13
Token:    '$'
Action:   ACTION[13, '$'] = Reduce 2 (E → E + T)

AST: Crear nodo no-terminal 'T' con hijo 'num'
```

#### **Paso 7: Reduce E → E + T**

```
Action:   Reduce 2 (E → E + T)
Pop:      3 elementos [(2, 'E'), (8, '+'), (13, 'T')]
Stack:    [(0, '')]
GOTO:     GOTO[0, 'E'] = 2
Push:     (2, 'E')
Stack:    [(0, ''), (2, 'E')]
State:    2
Token:    '$'
Action:   ACTION[2, '$'] = Reduce 1 (S → E)

AST: Crear nodo no-terminal 'E' con hijos ['E', '+', 'T']
```

#### **Paso 8: Reduce S → E**

```
Action:   Reduce 1 (S → E)
Pop:      1 elemento [(2, 'E')]
Stack:    [(0, '')]
GOTO:     GOTO[0, 'S'] = 1
Push:     (1, 'S')
Stack:    [(0, ''), (1, 'S')]
State:    1
Token:    '$'
Action:   ACTION[1, '$'] = Accept

AST: Crear nodo raíz 'S' con hijo 'E'
```

#### **Paso 9: Accept**

```
Action:   Accept
Status:   SUCCESS ✅
```

### AST Final

```
           S
           |
           E
          /|\
         / | \
        E  +  T
        |     |
        T    num
        |
       id
```

---

## ⚠️ Detección de Conflictos

### Tipos de Conflictos

#### 1. Shift-Reduce Conflict

Ocurre cuando el parser no sabe si hacer **shift** o **reduce**.

**Ejemplo:**

```
Estado X contiene:
  • [E → E + T·, +]        → Quiere REDUCE
  • Transición X --+--> Y  → Quiere SHIFT

En ACTION[X, +]:
  Opción 1: Shift Y
  Opción 2: Reduce por E → E + T
¡CONFLICTO!
```

**Causas comunes:**
- Gramáticas ambiguas
- Precedencia de operadores no definida
- El problema del "dangling else"

**Ejemplo clásico (dangling else):**

```
stmt → if expr then stmt
stmt → if expr then stmt else stmt

Estado contiene:
  [stmt → if expr then stmt·, else]
  [stmt → if expr then stmt· else stmt, ...]

¿Hacer reduce o shift del 'else'?
```

**Solución:**
- Especificar precedencia de operadores
- Reestructurar la gramática
- Usar resolución por defecto (shift > reduce)

#### 2. Reduce-Reduce Conflict

Ocurre cuando el parser no sabe cuál de dos producciones usar para reducir.

**Ejemplo:**

```
Estado X contiene:
  • [A → α·, a]  → Quiere reduce por A → α
  • [B → β·, a]  → Quiere reduce por B → β

En ACTION[X, a]:
  Opción 1: Reduce por A → α
  Opción 2: Reduce por B → β
¡CONFLICTO!
```

**Causas comunes:**
- Gramática ambigua
- Necesita más lookahead (LR(1) no es suficiente)

**Ejemplo:**

```
S → A a
S → B a
A → x
B → x

Estado contiene:
  [A → x·, a]
  [B → x·, a]

¿Reducir por A → x o por B → x?
```

**Solución:**
- Reestructurar la gramática
- Factorizar producciones comunes
- Usar un parser más potente (GLR)

### Detección en el Código

```python
def _add_reduce_action(self, state_index, item, lookahead):
    prod_idx = grammar.productions.index(item.production)
    action = ParsingAction(REDUCE, prod_idx)
    key = (state_index, lookahead)
    
    if key in self.action_table:
        existing = self.action_table[key]
        
        if existing.type == SHIFT:
            conflict_type = "shift_reduce"
        else:
            conflict_type = "reduce_reduce"
        
        self.conflicts.append(
            ConflictInfo(
                state=state_index,
                symbol=lookahead,
                actions=[existing, action],
                conflict_type=conflict_type
            )
        )
    else:
        self.action_table[key] = action
```

### Verificación de Gramática

```python
# Verificar si la gramática es LR(1)
automaton = Automaton(grammar)
table = ParsingTable(automaton)

if table.has_conflicts():
    print("⚠️ La gramática NO es LR(1)")
    conflicts = table.get_conflict_summary()
    
    for conflict in conflicts:
        print(f"Estado {conflict['state']}: "
              f"{conflict['type']} en símbolo '{conflict['symbol']}'")
else:
    print("✅ La gramática es LR(1)")
```

---

## 📖 Referencia de API

### Grammar

```python
grammar = Grammar.from_text(grammar_text, start_symbol="S")

# Propiedades
grammar.productions          # Lista de producciones
grammar.terminals            # Conjunto de terminales
grammar.non_terminals        # Conjunto de no-terminales
grammar.start_symbol         # Símbolo inicial

# Métodos
grammar.first(symbols)       # Calcular FIRST(α)
grammar.follow(symbol)       # Calcular FOLLOW(A)
grammar.validate()           # Validar gramática
```

### Automaton

```python
automaton = Automaton(grammar)

# Propiedades
automaton.states             # Lista de ItemSets
automaton.transitions        # Lista de transiciones
automaton.grammar            # Gramática

# Métodos
automaton.get_state_info(n)          # Info del estado n
automaton.find_conflicts()            # Detectar conflictos
automaton.is_lr1_grammar()           # ¿Es LR(1)?
automaton.get_grammar_type()         # Tipo de gramática
```

### ParsingTable

```python
table = ParsingTable(automaton)

# Propiedades
table.action_table           # Tabla ACTION
table.goto_table             # Tabla GOTO
table.conflicts              # Lista de conflictos

# Métodos
table.get_action(state, symbol)      # Consultar ACTION
table.get_goto(state, non_terminal)  # Consultar GOTO
table.has_conflicts()                # ¿Tiene conflictos?
table.export_action_table()          # Exportar ACTION
table.export_goto_table()            # Exportar GOTO
```

### ParserEngine

```python
engine = ParserEngine(grammar, table)

# Métodos
engine.parse(input_string)           # Parsear input
engine.parse_interactive(input)      # Parsear con detalles
engine.validate_input(input)         # Validar input
```

---

## 🎓 Ventajas de LR(1)

### ✅ Comparado con otros parsers

| Característica | LL(1) | SLR(1) | LALR(1) | LR(1) |
|---------------|-------|--------|---------|-------|
| **Potencia** | Baja | Media | Alta | **Máxima** |
| **Gramáticas reconocidas** | Limitadas | Moderadas | Muchas | **Casi todas** |
| **Tamaño de tabla** | Pequeño | Medio | Medio | **Grande** |
| **Complejidad construcción** | O(n) | O(n³) | O(n³) | **O(n³)** |
| **Detección de errores** | Tardía | Temprana | Temprana | **Inmediata** |
| **Recursión izquierda** | ❌ No | ✅ Sí | ✅ Sí | **✅ Sí** |

### ✅ Ventajas principales

1. **Máxima potencia**: Reconoce casi todas las gramáticas prácticas
2. **Detección temprana de errores**: Identifica errores sintácticos inmediatamente
3. **Eficiente**: O(n) en tiempo de parsing
4. **Determinista**: No hay backtracking
5. **Recursión izquierda**: Maneja naturalmente
6. **AST automático**: Construye el árbol durante el parsing

### ✅ Casos de uso

- ✅ Compiladores profesionales
- ✅ Intérpretes de lenguajes de programación
- ✅ Analizadores de SQL
- ✅ Parsers de formatos complejos
- ✅ Herramientas de análisis de código

---

## 🎯 Resumen

### Flujo de Construcción

```
1. Grammar Text
   ↓ [Lark Parser]
2. Grammar Object (productions, symbols, FIRST, FOLLOW)
   ↓ [Automaton]
3. LR(1) States (ItemSets + transitions)
   ↓ [ParsingTable]
4. ACTION & GOTO tables
   ↓ [ParserEngine]
5. Parse input → AST
```

### Componentes Clave

1. **LR1Item**: `[A → α·β, a]`
2. **ItemSet**: Conjunto de ítems (estado)
3. **CLOSURE**: Expande ítems
4. **GOTO**: Calcula siguiente estado
5. **Automaton**: Colección de estados
6. **ACTION**: Qué hacer con terminales
7. **GOTO**: A dónde ir con no-terminales
8. **ParserEngine**: Ejecuta el parsing

### Algoritmos Fundamentales

1. **CLOSURE(I)**: Expande ítems con no-terminales después del punto
2. **GOTO(I, X)**: Avanza el punto sobre X y calcula CLOSURE
3. **Worklist (BFS)**: Construye todos los estados
4. **Construcción de tablas**: Convierte autómata en ACTION/GOTO
5. **Parsing**: Stack + INPUT + tablas → AST

---

## 📚 Referencias

- **Dragon Book**: Compilers: Principles, Techniques, and Tools (Aho, Sethi, Ullman)
- **Modern Compiler Implementation**: Andrew W. Appel
- **Engineering a Compiler**: Keith Cooper, Linda Torczon
- **Documentación oficial**: [docs.claude.com](https://docs.claude.com)

---

## 🚀 Siguiente Paso

¡Experimenta con diferentes gramáticas!

```python
# Prueba tu propia gramática
grammar_text = """
S -> E
E -> E + T | T
T -> T * F | F  
F -> ( E ) | id
"""

grammar = Grammar.from_text(grammar_text)
automaton = Automaton(grammar)
table = ParsingTable(automaton)

if table.has_conflicts():
    print("⚠️ La gramática tiene conflictos")
else:
    print("✅ ¡Gramática LR(1) válida!")
    engine = ParserEngine(grammar, table)
    result = engine.parse("id + id * id")
    print("✅ Parsing exitoso!")
```

---

**¿Preguntas?** Consulta la documentación o revisa los ejemplos en el código.

---
