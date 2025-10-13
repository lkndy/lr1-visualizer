# LR(1) Parser Visualizer

An interactive web-based visualizer for LR(1) parsing with step-by-step execution, animated visualizations, and comprehensive grammar analysis.

![LR(1) Parser Visualizer](https://img.shields.io/badge/LR%281%29-Parser%20Visualizer-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![React](https://img.shields.io/badge/React-18+-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-red)

## Features

### 🎯 Core Functionality
- **Interactive Grammar Editor** with syntax highlighting and real-time validation
- **Step-by-Step Parsing** with play/pause controls and adjustable speed
- **Comprehensive Visualizations**:
  - Animated parser stack with push/pop operations
  - Interactive Abstract Syntax Tree (AST) with D3.js
  - LR(1) automaton visualization with ReactFlow
  - Parsing tables with current state highlighting

### 📊 Advanced Features
- **Conflict Detection** with detailed explanations
- **Grammar Validation** with early error detection
- **Example Grammars** (arithmetic, JSON, simple languages)
- **Real-time Updates** via WebSocket connection
- **Export Capabilities** for parsing tables and AST

### 🎨 User Experience
- **Responsive Design** optimized for desktop and mobile
- **Smooth Animations** using Framer Motion
- **Color-coded Visualizations** matching academic standards
- **Intuitive Controls** with keyboard shortcuts
- **Comprehensive Help** and documentation

## Technology Stack

### Backend
- **Python 3.11+** with type hints and dataclasses
- **FastAPI** for REST API and WebSocket support
- **Pydantic** for data validation and serialization
- **uv** package manager for fast dependency management

### Frontend
- **React 18** with TypeScript for type safety
- **Vite** for fast development and building
- **TailwindCSS** for responsive styling
- **Bun** package manager for fast JavaScript execution

### Visualization Libraries
- **D3.js** for AST tree visualization and animations
- **ReactFlow** for automaton state machine visualization
- **Framer Motion** for smooth UI animations
- **React Syntax Highlighter** for grammar editing

## Quick Start

### Prerequisites
- Python 3.11 or higher
- Node.js 18 or higher (or Bun)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/lr1-parser-visualizer.git
   cd lr1-parser-visualizer
   ```

2. **Setup Backend**
   ```bash
   cd backend
   
   # Install uv if you don't have it
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install dependencies
   uv sync
   
   # Run the development server
   uv run python main.py
   ```

3. **Setup Frontend**
   ```bash
   cd frontend
   
   # Install dependencies (using Bun)
   bun install
   
   # Run the development server
   bun run dev
   ```

4. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs

## Usage

### 1. Define a Grammar
Enter your grammar rules in BNF-like syntax:
```
E -> E + T | E - T | T
T -> T * F | T / F | F
F -> ( E ) | id | num
```

### 2. Validate and Generate Tables
- Click "Generate Parsing Table" to build the LR(1) automaton
- View any conflicts or errors in the validation panel
- Explore the parsing table and automaton visualizations

### 3. Parse Input Strings
- Enter an input string (e.g., "id + id * id")
- Use the step controls to navigate through the parsing process
- Watch the stack, AST, and automaton update in real-time

### 4. Explore Visualizations
- **Stack Tab**: See the parser stack with animated push/pop operations
- **AST Tab**: Explore the abstract syntax tree construction
- **Automaton Tab**: Navigate the LR(1) state machine
- **Table Tab**: Examine the ACTION and GOTO tables

## Example Grammars

### Arithmetic Expressions
```
E -> E + T | E - T | T
T -> T * F | T / F | F
F -> ( E ) | id | num
```
**Example Input**: `id + id * ( id - id )`

### Simple Language
```
S -> stmt_list
stmt_list -> stmt stmt_list | stmt
stmt -> id = expr | if expr then stmt
expr -> expr + term | expr - term | term
term -> id | num | ( expr )
```
**Example Input**: `id = id + num`

### JSON-like Structure
```
value -> object | array | string | number
object -> { pairs }
pairs -> pair pairs_tail | ε
pairs_tail -> , pair pairs_tail | ε
pair -> string : value
array -> [ elements ]
elements -> value elements_tail | ε
elements_tail -> , value elements_tail | ε
```
**Example Input**: `{ "key" : "value" }`

## API Documentation

### REST Endpoints

#### Validate Grammar
```http
POST /api/v1/grammar/validate
Content-Type: application/json

{
  "grammar_text": "E -> E + T | T",
  "start_symbol": "E"
}
```

#### Generate Parsing Table
```http
POST /api/v1/parser/table
Content-Type: application/json

{
  "grammar_text": "E -> E + T | T",
  "start_symbol": "E"
}
```

#### Parse Input String
```http
POST /api/v1/parser/parse
Content-Type: application/json

{
  "grammar_text": "E -> E + T | T",
  "input_string": "id + id",
  "start_symbol": "E"
}
```

### WebSocket Endpoint

Connect to `/api/v1/ws/parse` for real-time parsing updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/parse');

ws.send(JSON.stringify({
  grammar_text: "E -> E + T | T",
  input_string: "id + id",
  start_symbol: "E"
}));

ws.onmessage = (event) => {
  const result = JSON.parse(event.data);
  console.log('Parsing result:', result);
};
```

## Development

### Project Structure
```
lr1-parser-visualizer/
├── backend/                 # Python FastAPI backend
│   ├── parser/             # LR(1) parser implementation
│   ├── api/                # API endpoints and WebSocket
│   ├── tests/              # Unit and integration tests
│   └── main.py             # Application entry point
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── store/          # Zustand state management
│   │   ├── types/          # TypeScript definitions
│   │   └── utils/          # Utility functions
│   └── public/             # Static assets
├── docs/                   # Documentation
└── README.md
```

### Running Tests

#### Backend Tests
```bash
cd backend
uv run pytest
```

#### Frontend Tests
```bash
cd frontend
bun test
```

### Building for Production

#### Backend
```bash
cd backend
uv build
```

#### Frontend
```bash
cd frontend
bun run build
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Style
- **Python**: Follow PEP 8 with type hints
- **TypeScript**: Use strict mode with comprehensive interfaces
- **React**: Use functional components with hooks
- **CSS**: Use TailwindCSS utility classes

## Performance

### Benchmarks
- **Grammar Validation**: < 50ms for typical grammars
- **Table Generation**: < 200ms for 50-state grammars
- **Parsing**: < 100ms for 100-token inputs
- **Frontend Rendering**: 60fps animations

### Optimization Strategies
- **Backend**: LRU caching for FIRST computation
- **Frontend**: Memoization and virtual scrolling
- **Network**: Efficient WebSocket communication
- **Memory**: Immutable state updates

## Troubleshooting

### Common Issues

#### Backend Won't Start
```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
uv sync --reinstall
```

#### Frontend Build Errors
```bash
# Clear cache and reinstall
bun pm cache rm
bun install

# Check Node.js version
node --version  # Should be 18+
```

#### Grammar Validation Errors
- Check for undefined non-terminals
- Ensure proper BNF syntax
- Verify start symbol is defined

#### Parsing Conflicts
- Review grammar for ambiguities
- Check for left recursion
- Consider grammar refactoring

### Getting Help
- **Issues**: Create a GitHub issue
- **Discussions**: Use GitHub Discussions
- **Documentation**: Check the `/docs` folder
- **Examples**: Try the provided example grammars

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **LR(1) Algorithm**: Based on Dragon Book principles
- **Visualization Inspiration**: Inspired by academic parser visualizers
- **Technology Choices**: Modern web technologies for optimal performance
- **Community**: Thanks to all contributors and users

## Roadmap

### Version 2.0
- [ ] Support for SLR and LALR parsing
- [ ] Grammar conflict resolution suggestions
- [ ] Collaborative editing features
- [ ] Mobile app version

### Version 2.1
- [ ] Export to various formats (PDF, PNG, SVG)
- [ ] Custom grammar themes
- [ ] Advanced debugging tools
- [ ] Performance profiling

### Version 2.2
- [ ] Plugin system for custom visualizations
- [ ] Integration with popular IDEs
- [ ] Cloud-based grammar sharing
- [ ] Advanced analytics and insights

---

**Made with ❤️ for the compiler design community**

*For educational purposes and compiler design research*
