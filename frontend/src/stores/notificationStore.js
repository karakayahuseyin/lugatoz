import { writable } from 'svelte/store';

const { subscribe, update } = writable([]);
let nextId = 0;

export const notifications = {
  subscribe,
  show: (message, type = 'info', duration = 3000) => {
    const id = nextId++;
    const notification = { id, message, type, duration };

    update(notifications => [...notifications, notification]);

    // Auto remove after duration
    setTimeout(() => {
      update(notifications => notifications.filter(n => n.id !== id));
    }, duration + 300); // Extra time for animation
  },
  success: (message, duration = 3000) => {
    notifications.show(message, 'success', duration);
  },
  error: (message, duration = 4000) => {
    notifications.show(message, 'error', duration);
  },
  warning: (message, duration = 3500) => {
    notifications.show(message, 'warning', duration);
  },
  info: (message, duration = 3000) => {
    notifications.show(message, 'info', duration);
  },
  remove: (id) => {
    update(notifications => notifications.filter(n => n.id !== id));
  }
};
