#!/bin/bash
# Quick start script for the HTTP Ingestion Server

echo "=================================="
echo "HTTP Ingestion Server - Quick Start"
echo "=================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please copy .env.example to .env and configure your credentials"
    exit 1
fi

# Check if INGESTION_API_KEY is set
if ! grep -q "INGESTION_API_KEY" .env || grep -q "INGESTION_API_KEY=your-secure-random-api-key-here" .env; then
    echo "⚠️  Warning: INGESTION_API_KEY not configured"
    echo ""
    echo "Generating a secure API key..."
    API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    echo ""
    echo "Generated API key: $API_KEY"
    echo ""
    echo "Add this to your .env file:"
    echo "INGESTION_API_KEY=$API_KEY"
    echo ""
    exit 1
fi

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installing server dependencies..."
    pip install flask python-dotenv gunicorn
    echo ""
fi

echo "✅ Starting HTTP Ingestion Server..."
echo ""
echo "Server will be available at:"
echo "  - http://localhost:8000"
echo "  - http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python3 -m server.app
