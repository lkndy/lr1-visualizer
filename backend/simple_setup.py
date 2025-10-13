#!/usr/bin/env python3
"""
Simple setup script for LR(1) Parser Visualizer
Falls back to pip if uv has issues
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and handle errors gracefully"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False

def main():
    print("🚀 Simple LR(1) Parser Visualizer Setup")
    
    # Try uv first
    print("\n📦 Trying uv setup...")
    if run_command("uv --version", "Checking uv"):
        if run_command("uv python install 3.11", "Installing Python 3.11"):
            if run_command("uv python pin 3.11", "Pinning Python version"):
                if run_command("uv venv", "Creating virtual environment"):
                    if run_command("uv sync --group dev", "Installing dependencies with uv"):
                        print("\n🎉 uv setup successful!")
                        return
    
    # Fallback to pip
    print("\n📦 Falling back to pip setup...")
    if run_command("python3 -m venv .venv", "Creating virtual environment"):
        if run_command("source .venv/bin/activate && pip install --upgrade pip", "Upgrading pip"):
            if run_command("source .venv/bin/activate && pip install -r requirements.txt", "Installing dependencies with pip"):
                print("\n🎉 pip setup successful!")
                return
    
    print("\n❌ All setup methods failed!")
    sys.exit(1)

if __name__ == "__main__":
    main()
