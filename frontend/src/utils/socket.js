import { io } from 'socket.io-client';
import { getGuestSeenQuestions } from './guestSeen';

class SocketManager {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.lastRoomCode = null;
    this.lastPlayerName = null;
    this.lastGrade = null;
    this.lastTheme = null;
    this.isReconnecting = false;
  }

  connect() {
    if (this.socket) return this.socket;

    const socketUrl = window.location.origin;

    this.socket = io(socketUrl, {
      path: '/socket.io',
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 10,
      timeout: 20000
    });

    this.socket.on('connect', () => {
      this.connected = true;

      if (this.lastRoomCode && this.lastPlayerName && this.isReconnecting) {
        setTimeout(() => {
          this.socket.emit('join_game', {
            player_name: this.lastPlayerName,
            room_code: this.lastRoomCode,
            grade: this.lastGrade,
            theme: this.lastTheme,
            guest_seen_questions: getGuestSeenQuestions()
          });
          this.isReconnecting = false;
        }, 500);
      }
    });

    this.socket.on('disconnect', (reason) => {
      this.connected = false;

      if (reason === 'transport close' || reason === 'ping timeout') {
        this.isReconnecting = true;
      }
    });

    this.socket.on('reconnect_failed', () => {
      this.isReconnecting = false;
    });

    return this.socket;
  }

  setRoomInfo(playerName, roomCode, grade = null, theme = null) {
    this.lastPlayerName = playerName;
    this.lastRoomCode = roomCode;
    this.lastGrade = grade;
    this.lastTheme = theme;
  }

  clearRoomInfo() {
    this.lastPlayerName = null;
    this.lastRoomCode = null;
    this.lastGrade = null;
    this.lastTheme = null;
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
