# Storyteller - Generative Interactive Narratives

An AI-powered storytelling application that creates branching, interactive narratives from classic literature and custom text corpuses. Built with LangGraph, FastAPI, and React.

## What is Storyteller?

Storyteller generates unique, branching narratives where users guide the story through choices. Each story chapter is accompanied by AI-generated images in an impressionist style. The application uses RAG (Retrieval-Augmented Generation) to ground stories in source material while maintaining creative freedom.

**Key Features:**
- Branching narrative graphs that grow with user choices
- DALL-E 3 generated images for each chapter
- Multiple text corpuses (Mahabharata, Odyssey, Arabian Nights, etc.)
- 5 storyteller personas with unique voices
- Save and reload story journeys
- Real-time streaming story generation

## Project Structure

This is a **dual-project monorepo** with independently deployable backend and frontend:

```
storyteller/
├── storyteller_backend/      # Python FastAPI backend
├── storyteller_frontend/     # React/Vite frontend (coming in Phase 2)
├── data/                     # Shared: Vector databases, embeddings
├── saved_graphs/             # Shared: User story journeys
├── src/                      # Legacy code (reference only)
└── documentation/            # Project documentation
```

### Backend (`storyteller_backend/`)
- **Tech Stack:** Python 3.11+, FastAPI, LangGraph, LangChain, ChromaDB
- **Purpose:** Story generation agent, corpus retrieval, API server
- **Independent deployment:** Can be deployed separately to Railway, Render, etc.

### Frontend (`storyteller_frontend/`) - Phase 2
- **Tech Stack:** React 19, Vite, TypeScript, ReactFlow, Tailwind CSS
- **Purpose:** Graph visualization, user interface
- **Independent deployment:** Can be deployed separately to Vercel, Netlify, etc.

## Quick Start

### Prerequisites
- Python 3.11 or later
- Node.js 18.0 or later (for frontend, Phase 2)
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### 1. Backend Setup

```bash
# Navigate to backend
cd storyteller_backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run the server
python -m uvicorn api.main:app --reload
```

Backend will be available at: http://localhost:8000

API documentation: http://localhost:8000/docs

### 2. Frontend Setup (Phase 2 - Coming Soon)

```bash
# Navigate to frontend
cd storyteller_frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Edit .env.local to set API URL

# Run development server
npm run dev
```

Frontend will be available at: http://localhost:3000

## Documentation

- **[MANUAL_SETUP.md](documentation/MANUAL_SETUP.md)** - Detailed setup instructions
- **[next_steps.md](documentation/next_steps.md)** - Implementation plan and architecture decisions
- **Backend README** - `storyteller_backend/README.md` (coming soon)
- **Frontend README** - `storyteller_frontend/README.md` (Phase 2)

## Available Corpuses

The system currently includes 6 pre-processed text corpuses:

1. **The Mahabharata** - Ancient Indian epic
2. **The Odyssey** - Homer's classic Greek epic
3. **The Arabian Nights** - Collection of Middle Eastern folk tales
4. **The Volsunga Saga** - Norse legendary saga
5. **The Jataka Tales** - Buddhist birth stories
6. **Locus Platform Documentation** - Technical documentation example

### Adding New Corpuses

See `documentation/next_steps.md` for instructions on ingesting custom text files.

## Storyteller Personas

Choose from 5 distinct storyteller personalities:

- **Grandmother** - Warm, nurturing, traditional storytelling
- **Scholar** - Analytical, educational, contextual
- **Poet** - Lyrical, metaphorical, artistic
- **Historian** - Factual, chronological, detailed
- **Mystic** - Spiritual, symbolic, philosophical

Each persona has a unique color theme and narrative voice.

## Architecture

### Self-Hosted Deployment (Current - Phase 1)
Users run both backend and frontend locally with their own OpenAI API keys.

### Hybrid Deployment (Future - Phase 2+)
- Backend deployed to cloud (Railway, Render, AWS Lambda)
- Frontend runs locally OR deployed to Vercel/Netlify
- Users configure frontend to point to deployed backend URL

### Authentication Modes
- **Phase 1:** Self-hosted (API key in `.env` file)
- **Phase 2+:** Per-request key (key sent in HTTP headers)
- **Phase 3+:** Credit system (users buy credits, platform manages OpenAI)

See `documentation/next_steps.md` for detailed architecture discussion.

## Testing

```bash
# Backend tests
cd storyteller_backend
pytest tests/ -v --cov=api --cov=services

# Frontend tests (Phase 2)
cd storyteller_frontend
npm test
```

## Development Status

### Completed (Legacy `src/` code)
- Multi-corpus RAG system
- LangGraph story generation agent
- Persona system with theming
- DALL-E 3 image generation
- FastAPI server with SSE streaming
- Next.js frontend with ReactFlow visualization

### In Progress (Phase 1)
- Modular backend refactoring (`storyteller_backend/`)
- Clean service layer architecture
- Comprehensive testing suite
- Improved configuration management

### Planned (Phase 2+)
- Lightweight Vite + React frontend (`storyteller_frontend/`)
- Swappable graph visualization libraries
- Error boundaries and better error handling
- Deployment configurations (Docker, cloud platforms)

## Contributing

Created by [Mehrab Modi](https://github.com/mehrabmodi)

Contributions, issues, and feature requests are welcome!

## License

MIT License

Copyright (c) 2025 Mehrab Modi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph) and [LangChain](https://github.com/langchain-ai/langchain)
- Image generation powered by [OpenAI DALL-E 3](https://openai.com/dall-e-3)
- Graph visualization using [ReactFlow](https://reactflow.dev/)
- Embeddings stored in [ChromaDB](https://www.trychroma.com/)
- Layout algorithm by [ELK (Eclipse Layout Kernel)](https://www.eclipse.org/elk/)

---

*"Story is our only boat for sailing on the river of time."* - Ursula K. Le Guin

