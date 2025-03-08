
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#F7F7F8',
        userBubble: '#DCF8C6',
        aiBubble: '#FFFFFF',
        sidebarBg: '#EAEAEB',
      },
    },
  },
  plugins: [],
}
