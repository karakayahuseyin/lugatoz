import { writable } from 'svelte/store';

// User authentication store
function createUserStore() {
  const { subscribe, set, update } = writable({
    userId: null,
    username: null,
    isLoggedIn: false
  });

  return {
    subscribe,
    set,
    update,

    // Login user
    login: (userId, username) => {
      const userData = { userId, username, isLoggedIn: true };
      set(userData);
      // Save to localStorage
      localStorage.setItem('lugatoz_user', JSON.stringify(userData));
    },

    // Logout user
    logout: () => {
      set({ userId: null, username: null, isLoggedIn: false });
      localStorage.removeItem('lugatoz_user');
    },

    // Load user from localStorage
    loadFromStorage: () => {
      const stored = localStorage.getItem('lugatoz_user');
      if (stored) {
        try {
          const userData = JSON.parse(stored);
          set(userData);
          return userData;
        } catch (e) {
          localStorage.removeItem('lugatoz_user');
        }
      }
      return null;
    },

    // Update username
    updateUsername: (newUsername) => {
      update(state => {
        const newState = { ...state, username: newUsername };
        localStorage.setItem('lugatoz_user', JSON.stringify(newState));
        return newState;
      });
    }
  };
}

export const userStore = createUserStore();
