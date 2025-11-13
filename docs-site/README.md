# Dividend API Documentation Site

Stripe-inspired documentation site for the Dividend API.

## Features

- **3-Column Layout**: Navigation | Content | Code Examples
- **Dark Mode**: Full dark mode support
- **Interactive Code**: Syntax-highlighted examples in Python, JavaScript, and cURL
- **Responsive**: Mobile-friendly design
- **Search**: Documentation search (coming soon)
- **Fast**: Built with Next.js 14 for optimal performance

## Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Open http://localhost:3000
```

## Structure

```
docs-site/
├── app/                    # Next.js app directory
│   ├── page.tsx           # Homepage
│   ├── layout.tsx         # Root layout
│   └── api/               # API documentation
│       ├── layout.tsx     # 3-column layout
│       └── [slug]/        # Individual API pages
├── components/             # React components
│   ├── Navigation.tsx     # Left sidebar
│   ├── CodePanel.tsx      # Right sidebar
│   ├── Header.tsx         # Top header
│   └── CodeBlock.tsx      # Code highlighting
└── lib/                    # Utilities
    ├── api-content.ts     # Documentation content
    └── code-examples.ts   # Code examples
```

## Design System

### Colors

- **Brand**: Green (#22c55e) - Dividend-focused
- **Background**: Slate-950 (dark), White (light)
- **Text**: Slate-100 (dark), Slate-900 (light)
- **Accent**: Blue for interactive elements

### Typography

- **Body**: Inter
- **Code**: JetBrains Mono

### Layout

- **Navigation**: 240px fixed width
- **Content**: Flexible width (max 1024px)
- **Code Panel**: 400px fixed width

## Development

### Adding New Pages

1. Create new page in `app/api/[slug]/page.tsx`
2. Add navigation item in `components/Navigation.tsx`
3. Add code examples in `lib/code-examples.ts`

### Customizing Styles

Edit `tailwind.config.ts` for colors and theme customization.

### Adding Code Examples

```typescript
// lib/code-examples.ts
export const codeExamples = {
  '/api/stocks': {
    python: `import requests...`,
    javascript: `fetch(...)...`,
    curl: `curl https://...`,
  },
};
```

## Deployment

### Vercel (Recommended)

```bash
npm install -g vercel
vercel deploy
```

### Docker

```bash
docker build -t dividend-docs .
docker run -p 3000:3000 dividend-docs
```

### Static Export

```bash
npm run build
npm run export
```

## Full Implementation

See `../docs/STRIPE_DOCS_IMPLEMENTATION.md` for complete code and implementation details.

## Roadmap

- [ ] Search functionality
- [ ] Interactive API playground
- [ ] Code runner (try API calls directly)
- [ ] Version switcher (v1, v2)
- [ ] Changelog page
- [ ] Status page integration

## License

MIT
