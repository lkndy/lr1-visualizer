#!/bin/bash

echo "🚀 Setting up LR(1) Parser Visualizer..."

# Check if Python 3.11+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version check passed"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

node_version=$(node --version | cut -d'v' -f2 | cut -d. -f1)
if [ "$node_version" -lt 18 ]; then
    echo "❌ Node.js 18+ is required. Current version: $(node --version)"
    exit 1
fi

echo "✅ Node.js version check passed"

# Setup backend
echo "📦 Setting up backend..."
cd backend

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# Create isolated virtual environment with uv (if it doesn't exist)
echo "Creating isolated Python environment..."
uv venv --python 3.11

# Install Python dependencies using uv (no pip!)
echo "Installing Python dependencies with uv..."
uv sync --dev

echo "✅ Backend setup complete"

# Setup frontend
echo "📦 Setting up frontend..."
cd ../frontend

# Install Bun if not present
if ! command -v bun &> /dev/null; then
    echo "Installing Bun package manager..."
    curl -fsSL https://bun.sh/install | bash
    source $HOME/.bashrc
fi

# Install frontend dependencies
echo "Installing frontend dependencies..."
bun install

echo "✅ Frontend setup complete"

echo ""
echo "🎉 Setup complete! To start the application:"
echo ""
echo "Backend:"
echo "  cd backend"
echo "  uv run python main.py  # Uses uv's virtual environment automatically"
echo "  # OR manually: source .venv/bin/activate && python main.py"
echo ""
echo "Frontend:"
echo "  cd frontend && bun run dev"
echo ""
echo "Then open http://localhost:3000 in your browser"
echo ""
echo "💡 The backend now uses an isolated Python environment at backend/.venv/"
