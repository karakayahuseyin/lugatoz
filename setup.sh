#!/bin/bash

echo "=€ ÖzBilig Kurulum Scripti"
echo "========================="

# Backend kurulumu
echo ""
echo "=æ Backend ba1ml1l1klar1 kuruluyor..."
cd backend

if [ ! -d "venv" ]; then
    echo "Virtual environment olu_turuluyor..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

cd ..

# Frontend kurulumu
echo ""
echo "=æ Frontend ba1ml1l1klar1 kuruluyor..."
cd frontend
npm install
cd ..

echo ""
echo " Kurulum tamamland1!"
echo ""
echo "Ba_latmak için: ./start.sh"
echo ""
