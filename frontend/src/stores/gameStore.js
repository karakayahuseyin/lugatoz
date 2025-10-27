import { writable } from 'svelte/store';

// Oyun durumu store
export const gameState = writable({
  phase: 'home', // home, lobby, submitting_fake, voting, showing_results, final_test, game_over
  roomCode: null,
  playerName: null,
  playerId: null,
  isHost: false,
  players: [],
  currentQuestion: null,
  currentRound: 0,
  maxRounds: 10,
  options: [],
  submittedAnswer: false,
  votedAnswer: false,
  results: null,
  leaderboard: [],
  finalQuestions: [],
  error: null
});

// Store yardımcı fonksiyonları
export const updateGameState = (updates) => {
  gameState.update(state => ({ ...state, ...updates }));
};

export const resetGameState = () => {
  gameState.set({
    phase: 'home',
    roomCode: null,
    playerName: null,
    playerId: null,
    isHost: false,
    players: [],
    currentQuestion: null,
    currentRound: 0,
    maxRounds: 10,
    options: [],
    submittedAnswer: false,
    votedAnswer: false,
    results: null,
    leaderboard: [],
    finalQuestions: [],
    error: null
  });
};

export const setError = (message) => {
  gameState.update(state => ({ ...state, error: message }));
  // 5 saniye sonra hatayı temizle
  setTimeout(() => {
    gameState.update(state => ({ ...state, error: null }));
  }, 5000);
};
