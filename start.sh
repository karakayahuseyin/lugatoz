#!/bin/bash

echo "<� �zBilig Ba_lat1l1yor..."
echo "========================"

# Backend'i arka planda ba_lat
echo ""
echo "=' Backend ba_lat1l1yor..."
cd backend
source venv/bin/activate
python -m app.main &
BACKEND_PID=$!
cd ..

# Biraz bekle
sleep 3

# Frontend'i ba_lat
echo ""
echo "<� Frontend ba_lat1l1yor..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo " Sunucular ba_lat1ld1!"
echo ""
echo "=� Frontend: http://localhost:5173"
echo "=� Backend: http://localhost:8000"
echo "=� Admin: http://localhost:5173/admin.html"
echo ""
echo "Durdurmak i�in Ctrl+C'ye bas1n"

# Trap SIGINT to kill both processes
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

# Wait for both processes
wait
