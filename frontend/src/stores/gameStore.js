import { writable } from 'svelte/store';

const initialState = {
  phase: 'home', // home, lobby, submitting_fake, voting, showing_results, final_test, game_over
  roomCode: null,
  roomName: null,
  roomGroup: null,
  roomIcon: null,
  playerName: null,
  playerId: null,
  isHost: false,
  players: [],
  selectedGrade: null,
  selectedTheme: null,
  topic: null,
  currentQuestion: null,
  currentRound: 0,
  maxRounds: 10,
  options: [],
  submittedAnswer: false,
  votedAnswer: false,
  results: null,
  leaderboard: [],
  finalQuestions: [],
  finalConcepts: [],
  finalTestDuration: 120,
  finalProgress: null,
  error: null
};

export const gameState = writable({ ...initialState });

export const updateGameState = (updates) => {
  gameState.update((state) => ({ ...state, ...updates }));
};

export const resetGameState = () => {
  gameState.set({ ...initialState });
};

export const setError = (message) => {
  gameState.update((state) => ({ ...state, error: message }));
  setTimeout(() => {
    gameState.update((state) => ({ ...state, error: null }));
  }, 5000);
};
