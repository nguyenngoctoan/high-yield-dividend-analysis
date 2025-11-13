import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // GitHub color palette
        'github': {
          canvas: {
            DEFAULT: '#ffffff',
            subtle: '#f6f8fa',
            inset: '#f6f8fa',
          },
          fg: {
            DEFAULT: '#1f2328',
            muted: '#656d76',
            subtle: '#6e7781',
          },
          border: {
            DEFAULT: '#d0d7de',
            muted: '#d8dee4',
          },
          accent: {
            fg: '#0969da',
            emphasis: '#0969da',
            muted: '#54aeff',
            subtle: '#ddf4ff',
          },
          success: {
            fg: '#1a7f37',
            emphasis: '#1f883d',
            muted: '#4ac26b',
            subtle: '#dafbe1',
          },
          danger: {
            fg: '#d1242f',
            emphasis: '#cf222e',
            muted: '#ff8182',
            subtle: '#ffebe9',
          },
          attention: {
            fg: '#9a6700',
            emphasis: '#bf8700',
            muted: '#d4a72c',
            subtle: '#fff8c5',
          },
        },
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Noto Sans', 'Helvetica', 'Arial', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'SF Mono', 'Menlo', 'Consolas', 'Liberation Mono', 'monospace'],
      },
      fontSize: {
        'xs': ['12px', '1.5'],
        'sm': ['14px', '1.5'],
        'base': ['14px', '1.5'],
        'lg': ['16px', '1.5'],
        'xl': ['20px', '1.25'],
        '2xl': ['24px', '1.25'],
        '3xl': ['32px', '1.25'],
      },
    },
  },
  plugins: [],
};

export default config;
