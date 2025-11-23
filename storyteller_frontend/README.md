# Storyteller Frontend

Lightweight React SPA for interactive storytelling with graph visualization.

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool (fast HMR)
- **Tailwind CSS** - Styling
- **ReactFlow** - Graph visualization
- **ELK** - Automatic graph layout

## Prerequisites

- Node.js 18+ 
- npm
- Backend server running on `http://localhost:8000`

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Create environment file:**
   ```bash
   # Create .env.local with:
   VITE_API_BASE_URL=http://localhost:8000
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

   App will be available at `http://localhost:3000`

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Check TypeScript types

## Project Structure

```
src/
├── components/       # React components
│   ├── admin/       # Admin panel (CRUD for personas/corpuses)
│   ├── controls/    # Input controls
│   ├── dropdowns/   # Dropdown selectors
│   ├── graph-views/ # Graph visualization (swappable)
│   └── layout/      # Layout components
├── context/         # React Context for global state
├── hooks/           # Custom React hooks
├── services/        # API client functions
├── types/           # TypeScript type definitions
├── utils/           # Utility functions
└── styles/          # Global CSS

```

## Architecture Highlights

- **Modular Components:** Small, focused components (< 200 lines each)
- **Swappable Graph Views:** Easy to experiment with different visualization libraries
- **Type Safety:** Full TypeScript coverage
- **DRY Principle:** BaseDropdown eliminates code duplication
- **Custom Hooks:** Reusable logic for SSE, localStorage, theming

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000` |

## Development

The frontend communicates with the backend via REST API and Server-Sent Events (SSE):

- **REST:** User data, personas, corpuses, journeys
- **SSE:** Streaming story generation

See backend documentation for API details.

## Building for Production

```bash
npm run build
```

Output will be in `dist/` directory.

## License

Private project.

