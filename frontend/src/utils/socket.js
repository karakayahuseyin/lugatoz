import { io } from 'socket.io-client';

class SocketManager {
  constructor() {
    this.socket = null;
    this.connected = false;
  }

  connect() {
    if (this.socket) return this.socket;

    // Socket.IO balant1s1
    // Production'da window.location.origin kullanarak doğru URL'yi al
    const socketUrl = window.location.origin;

    this.socket = io(socketUrl, {
      path: '/socket.io',
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    });

    this.socket.on('connect', () => {
      console.log(' Socket balant1s1 kuruldu:', this.socket.id);
      this.connected = true;
    });

    this.socket.on('disconnect', () => {
      console.log(' Socket balant1s1 kesildi');
      this.connected = false;
    });

    this.socket.on('error', (error) => {
      console.error('Socket hatas1:', error);
    });

    return this.socket;
  }

  disconnect() {
    if (this.socket) {
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
}

export const socketManager = new SocketManager();
