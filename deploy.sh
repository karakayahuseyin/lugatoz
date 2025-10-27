#!/bin/bash

echo "LügaTöz Production Deployment"
echo "================================"

# Renk kodları
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Development container'larını durdur
echo -e "${YELLOW}Development container'ları durduruluyor...${NC}"
docker compose down

# Production build
echo -e "${YELLOW}Production build başlıyor...${NC}"
docker compose -f docker-compose.prod.yml build

# Container'ları başlat
echo -e "${YELLOW}Production container'ları başlatılıyor...${NC}"
docker compose -f docker-compose.prod.yml up -d

# Durumu kontrol et
sleep 3
echo -e "\n${GREEN}Deployment tamamlandı!${NC}\n"

# Container durumunu göster
docker compose -f docker-compose.prod.yml ps

# IP adresini göster
IP=$(hostname -I | awk '{print $1}')
echo -e "\n${GREEN}Erişim Bilgileri:${NC}"
echo -e "   Oyun: http://${IP}:8080"
echo -e "   Admin: http://${IP}:8080/#admin"
echo -e "   Backend API: http://${IP}:8000"
echo -e "\n${YELLOW}Multiplayer test için farklı cihazlardan yukarıdaki IP'ye bağlanın!${NC}\n"

# Logları takip et
echo -e "${YELLOW}Logları takip etmek için: docker compose -f docker-compose.prod.yml logs -f${NC}"
