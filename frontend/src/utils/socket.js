import { io } from 'socket.io-client';

class SocketManager {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.lastRoomCode = null;
    this.lastPlayerName = null;
    this.isReconnecting = false;
    this.connectionListeners = [];  // Bağlantı durumu değişikliği dinleyicileri
    this.reconnectAttempt = 0;
  }

  // Bağlantı durumu değişikliği dinleyicisi ekle
  onConnectionChange(callback) {
    this.connectionListeners.push(callback);
    // Mevcut durumu hemen bildir
    callback(this.connected, this.isReconnecting);
    return () => {
      this.connectionListeners = this.connectionListeners.filter(cb => cb !== callback);
    };
  }

  // Bağlantı durumu değişikliğini bildir
  notifyConnectionChange() {
    this.connectionListeners.forEach(cb => cb(this.connected, this.isReconnecting, this.reconnectAttempt));
  }

  connect() {
    if (this.socket) return this.socket;

    // Socket.IO bağlantısı
    // Production'da window.location.origin kullanarak doğru URL'yi al
    const socketUrl = window.location.origin;

    this.socket = io(socketUrl, {
      path: '/socket.io',
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 500,         // İlk deneme 500ms sonra
      reconnectionDelayMax: 3000,     // Maksimum 3 saniye bekle
      reconnectionAttempts: 20,       // 20 kez dene
      timeout: 30000,                 // 30 saniye bağlantı timeout
      forceNew: false,                // Mevcut bağlantıyı kullan
      upgrade: true,                  // Polling'den WebSocket'e upgrade
      rememberUpgrade: true,          // Upgrade'i hatırla
    });

    this.socket.on('connect', () => {
      this.connected = true;
      this.reconnectAttempt = 0;
      this.notifyConnectionChange();

      // Eğer daha önce bir odadaysa, otomatik yeniden katıl
      if (this.lastRoomCode && this.lastPlayerName && this.isReconnecting) {
        setTimeout(() => {
          this.socket.emit('join_game', {
            player_name: this.lastPlayerName,
            room_code: this.lastRoomCode
          });
          this.isReconnecting = false;
          this.notifyConnectionChange();
        }, 300);
      }
    });

    this.socket.on('disconnect', (reason) => {
      this.connected = false;

      // Eğer sunucu kapatmadıysa, yeniden bağlanma işareti
      if (reason === 'transport close' || reason === 'ping timeout' || reason === 'transport error') {
        this.isReconnecting = true;
      }
      this.notifyConnectionChange();
    });

    this.socket.on('reconnect', () => {
      this.reconnectAttempt = 0;
      this.notifyConnectionChange();
    });

    this.socket.on('reconnect_attempt', (attemptNumber) => {
      this.reconnectAttempt = attemptNumber;
      this.isReconnecting = true;
      this.notifyConnectionChange();
    });

    this.socket.on('reconnect_failed', () => {
      this.isReconnecting = false;
      this.notifyConnectionChange();
    });

    this.socket.on('error', () => {
      this.notifyConnectionChange();
    });

    return this.socket;
  }

  // Oda bilgilerini sakla (yeniden bağlanma için)
  setRoomInfo(playerName, roomCode) {
    this.lastPlayerName = playerName;
    this.lastRoomCode = roomCode;
  }

  // Oda bilgilerini temizle
  clearRoomInfo() {
    this.lastPlayerName = null;
    this.lastRoomCode = null;
    this.isReconnecting = false;
  }

  disconnect() {
    if (this.socket) {
      this.clearRoomInfo();
      this.socket.disconnect();
      this.socket = null;
      this.connected = false;
    }
  }

  emit(event, data) {
    if (this.socket) {
      this.socket.emit(event, data);
    }
  }

  on(event, callback) {
    if (this.socket) {
      this.socket.on(event, callback);
    }
  }

  off(event, callback) {
    if (this.socket) {
      this.socket.off(event, callback);
    }
  }

  getSocket() {
    return this.socket;
  }
}

export const socketManager = new SocketManager();
