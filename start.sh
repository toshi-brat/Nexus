#!/bin/bash
set -e
echo "⚡ Starting NEXUS Trading System..."
echo ""

echo "→ [1/2] Starting FastAPI backend on :8000 ..."
cd backend
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -q -r requirements.txt
cp ../.env.example ../.env 2>/dev/null || true
python main.py &
BACKEND_PID=$!
cd ..

echo "→ [2/2] Starting React frontend on :5173 ..."
cd frontend
npm install --silent
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ NEXUS is running!"
echo "   Dashboard  →  http://localhost:5173"
echo "   API Docs   →  http://localhost:8000/docs"
echo ""
echo "Ctrl+C to stop both servers."
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
