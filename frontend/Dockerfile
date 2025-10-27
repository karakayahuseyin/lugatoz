FROM node:18-alpine

WORKDIR /app

# Ba1ml1l1klar1 kopyala ve yükle
COPY package*.json ./
RUN npm install

# Uygulama kodunu kopyala
COPY . .

# Port
EXPOSE 5173

# Development server ba_lat
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
