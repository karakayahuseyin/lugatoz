// Player color utilities

export const playerColors = {
  blue: {
    bg: 'bg-blue-100',
    border: 'border-blue-300',
    text: 'text-blue-800',
    badge: 'bg-blue-500',
    gradient: 'from-blue-100 to-blue-200'
  },
  red: {
    bg: 'bg-red-100',
    border: 'border-red-300',
    text: 'text-red-800',
    badge: 'bg-red-500',
    gradient: 'from-red-100 to-red-200'
  },
  orange: {
    bg: 'bg-orange-100',
    border: 'border-orange-300',
    text: 'text-orange-800',
    badge: 'bg-orange-500',
    gradient: 'from-orange-100 to-orange-200'
  },
  green: {
    bg: 'bg-green-100',
    border: 'border-green-300',
    text: 'text-green-800',
    badge: 'bg-green-500',
    gradient: 'from-green-100 to-green-200'
  }
};

export function getPlayerColor(color) {
  return playerColors[color] || playerColors.blue;
}
