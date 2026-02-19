#!/bin/bash
# =============================================================
# Agentic RAG Masterclass — Launch Script
# Double-click this file to start all services and open the UI
# =============================================================

PROJECT_DIR="/Users/toney/Exploring/claude-code-agentic-rag-masterclass"
BACKEND_PORT=8001
FRONTEND_PORT=5173
SUPABASE_API_PORT=54321

# Full paths to venv binaries (so script works from any location)
UVICORN="$PROJECT_DIR/backend/venv/bin/uvicorn"
PYTHON="$PROJECT_DIR/backend/venv/bin/python"

# Ensure Homebrew / nvm / node are on PATH when launched from Finder
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.nvm/versions/node/$(ls $HOME/.nvm/versions/node 2>/dev/null | tail -1)/bin:$PATH"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "========================================="
echo "  Agentic RAG Masterclass — Starting Up"
echo "========================================="
echo ""

# --------------------------------------------------
# 1. Check Docker is running (needed for Supabase)
# --------------------------------------------------
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker is not running.${NC}"
    echo "Please start Docker Desktop and try again."
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi
echo -e "${GREEN}Docker is running${NC}"

# --------------------------------------------------
# 2. Start Supabase (if not already running)
# --------------------------------------------------
echo ""
echo "Checking Supabase..."
cd "$PROJECT_DIR"

if curl -s "http://127.0.0.1:${SUPABASE_API_PORT}/rest/v1/" > /dev/null 2>&1; then
    echo -e "${GREEN}Supabase is already running on port ${SUPABASE_API_PORT}${NC}"
else
    echo -e "${YELLOW}Starting Supabase...${NC}"
    npx supabase start
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Supabase started${NC}"
    else
        echo -e "${RED}Failed to start Supabase${NC}"
        read -p "Press Enter to close..."
        exit 1
    fi
fi

# --------------------------------------------------
# 3. Stop existing backend/frontend if running
# --------------------------------------------------
echo ""
echo "Cleaning up old processes..."

# Kill any existing process on backend port
BACKEND_PID=$(lsof -ti:${BACKEND_PORT} 2>/dev/null)
if [ -n "$BACKEND_PID" ]; then
    echo "  Stopping old backend (PID $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null
    sleep 1
fi

# Kill any existing process on frontend port
FRONTEND_PID=$(lsof -ti:${FRONTEND_PORT} 2>/dev/null)
if [ -n "$FRONTEND_PID" ]; then
    echo "  Stopping old frontend (PID $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null
    sleep 1
fi

# --------------------------------------------------
# 4. Start Backend (FastAPI + uvicorn)
# --------------------------------------------------
echo ""
echo "Starting backend on port ${BACKEND_PORT}..."
cd "$PROJECT_DIR/backend"
"$UVICORN" main:app --reload --port=${BACKEND_PORT} > /tmp/rag-backend.log 2>&1 &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID (log: /tmp/rag-backend.log)"

# Wait for backend to be ready
echo "  Waiting for backend..."
for i in {1..15}; do
    if curl -s "http://localhost:${BACKEND_PORT}/api/health" > /dev/null 2>&1; then
        echo -e "  ${GREEN}Backend is ready${NC}"
        break
    fi
    if [ $i -eq 15 ]; then
        echo -e "  ${RED}Backend did not start in time. Check /tmp/rag-backend.log${NC}"
        read -p "Press Enter to close..."
        exit 1
    fi
    sleep 1
done

# --------------------------------------------------
# 5. Start Frontend (Vite dev server)
# --------------------------------------------------
echo ""
echo "Starting frontend on port ${FRONTEND_PORT}..."
cd "$PROJECT_DIR/frontend"
npm run dev > /tmp/rag-frontend.log 2>&1 &
FRONTEND_PID=$!
echo "  Frontend PID: $FRONTEND_PID (log: /tmp/rag-frontend.log)"

# Wait for frontend to be ready
echo "  Waiting for frontend..."
for i in {1..15}; do
    if curl -s "http://localhost:${FRONTEND_PORT}" > /dev/null 2>&1; then
        echo -e "  ${GREEN}Frontend is ready${NC}"
        break
    fi
    if [ $i -eq 15 ]; then
        echo -e "  ${YELLOW}Frontend may still be starting — opening browser anyway${NC}"
    fi
    sleep 1
done

# --------------------------------------------------
# 6. Open browser
# --------------------------------------------------
echo ""
echo "Opening browser..."
open "http://localhost:${FRONTEND_PORT}"

# --------------------------------------------------
# Done!
# --------------------------------------------------
echo ""
echo "========================================="
echo -e "  ${GREEN}All services running!${NC}"
echo "========================================="
echo ""
echo "  Frontend:  http://localhost:${FRONTEND_PORT}"
echo "  Backend:   http://localhost:${BACKEND_PORT}"
echo "  Supabase:  http://127.0.0.1:${SUPABASE_API_PORT}"
echo "  Studio:    http://127.0.0.1:54323"
echo ""
echo "  Logs:"
echo "    Backend:  /tmp/rag-backend.log"
echo "    Frontend: /tmp/rag-frontend.log"
echo ""
echo "Press Ctrl+C or close this window to stop backend & frontend."
echo ""

# Keep the window open and wait — kill children on exit
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "Backend and frontend stopped. (Supabase left running.)"
    exit 0
}
trap cleanup INT TERM

# Wait for both background processes
wait
