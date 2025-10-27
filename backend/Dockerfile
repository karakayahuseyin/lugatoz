FROM python:3.11-slim

WORKDIR /app

# Ba1ml1l1klar1 kopyala ve y�kle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY . .

# Port
EXPOSE 8000

# Sunucuyu ba_lat (production için workers kullan)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--reload"]
