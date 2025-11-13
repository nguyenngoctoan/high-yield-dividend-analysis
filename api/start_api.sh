#!/bin/bash

# Start Dividend API Server
# Development server with hot reload

echo "🚀 Starting Dividend API..."
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated"
    echo "Run: source venv/bin/activate"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found"
    echo "Please create .env with Supabase credentials"
    exit 1
fi

# Install API requirements if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing API requirements..."
    pip install -r api/requirements.txt
fi

# Start server
echo "✅ Starting FastAPI server on http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/v1/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

cd "$(dirname "$0")/.." || exit 1
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
