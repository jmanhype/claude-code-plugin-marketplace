#!/bin/bash
# DSPy Setup Helper
# Sets up DSPy environment with GEPA optimizer and dependencies

set -e

echo "🔧 Setting up DSPy environment for Code Safety Monitor..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1-2)
REQUIRED_VERSION="3.9"

if (( $(echo "$PYTHON_VERSION < $REQUIRED_VERSION" | bc -l) )); then
    echo "❌ Python 3.9+ required (found $PYTHON_VERSION)"
    exit 1
fi

echo "✓ Python version: $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

echo "✓ DSPy installed: $(python -c 'import dspy; print(dspy.__version__)')"
echo "✓ Control Arena installed: $(python -c 'import control_arena; print(control_arena.__version__)')"

# Check API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo ""
    echo "⚠️  OPENAI_API_KEY not set"
    echo "Set it with:"
    echo "  export OPENAI_API_KEY='your-key-here'"
    echo ""
else
    echo "✓ OPENAI_API_KEY configured"
fi

# Create directories
echo "Creating directories..."
mkdir -p models datasets logs/safety_audits reports figures

echo "✓ Directory structure created"

# Test installation
echo ""
echo "Testing DSPy installation..."
python3 << EOF
import dspy
from code_safety_monitor.src import CodeSafetyMonitor

print("✓ Import successful")

# Test monitor creation
monitor = CodeSafetyMonitor()
print("✓ Monitor instantiation successful")
EOF

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Set OPENAI_API_KEY if not already set"
echo "  2. Load training data: /load-control-arena --dataset control-tax"
echo "  3. Train monitor: /train-monitor"
echo "  4. Optimize with GEPA: /optimize-gepa"
echo ""
