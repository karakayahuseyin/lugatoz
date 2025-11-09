import { io } from 'socket.io-client';

class SocketManager {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.lastRoomCode = null;
    this.lastPlayerName = null;
    this.isReconnecting = false;
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
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 10, // Daha fazla deneme
      timeout: 20000
    });

    this.socket.on('connect', () => {
      console.log('✅ Socket bağlantısı kuruldu:', this.socket.id);
      this.connected = true;

      // Eğer daha önce bir odadaysa, otomatik yeniden katıl
      if (this.lastRoomCode && this.lastPlayerName && this.isReconnecting) {
        console.log('🔄 Odaya yeniden bağlanılıyor:', this.lastRoomCode);
        setTimeout(() => {
          this.socket.emit('join_game', {
            player_name: this.lastPlayerName,
            room_code: this.lastRoomCode
          });
          this.isReconnecting = false;
        }, 500);
      }
    });

    this.socket.on('disconnect', (reason) => {
      console.log('⚠️ Socket bağlantısı kesildi:', reason);
      this.connected = false;

      // Eğer sunucu kapatmadıysa (transport close veya ping timeout), yeniden bağlanma işareti
      if (reason === 'transport close' || reason === 'ping timeout') {
        this.isReconnecting = true;
      }
    });

    this.socket.on('reconnect', (attemptNumber) => {
      console.log('🔄 Yeniden bağlanıldı! Deneme:', attemptNumber);
    });

    this.socket.on('reconnect_attempt', (attemptNumber) => {
      console.log('🔄 Yeniden bağlanma denemesi:', attemptNumber);
    });

    this.socket.on('reconnect_failed', () => {
      console.error('❌ Yeniden bağlanma başarısız!');
      this.isReconnecting = false;
    });

    this.socket.on('error', (error) => {
      console.error('Socket hatası:', error);
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
