/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{svelte,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#06b6d4',     // Turkuaz (Cyan)
        secondary: '#84cc16',   // Limon Yeşili (Lime)
        success: '#06b6d4',     // Turkuaz
        danger: '#ef4444',      // Kırmızı (hata mesajları için)
        warning: '#84cc16',     // Limon Yeşili
        turquoise: '#06b6d4',   // Turkuaz
        lime: '#84cc16',        // Limon Yeşili
      }
    },
  },
  plugins: [],
}
