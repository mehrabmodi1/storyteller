# Storyteller — Generative Interactive Narratives

An AI-powered storytelling app that turns classic literature (or any text corpus) into a branching, interactive narrative. Users guide the story through choices; each chapter is grounded in retrieved source material and optionally illustrated.

Built with **LangGraph + FastAPI** (backend) and **React + Vite + ReactFlow** (frontend). Supports Google **Gemini** (free tier available) and **OpenAI** as interchangeable providers for chat / embeddings / images.

---

## What it does

- Generates a branching narrative graph that grows as the user picks choices
- Streams story text token-by-token via SSE
- Generates an illustration for each chapter (DALL-E 2 or Gemini image)
- Grounds every chapter in retrieved source-text chunks (hybrid BM25 + vector search via ChromaDB)
- Saves journeys; reload them later
- Six built-in storyteller personas with distinct voices and themes

---

## Tech stack

- **Backend:** Python 3.12, Poetry, FastAPI + uvicorn (port `8000`), LangGraph, LangChain, ChromaDB, `rank-bm25`
- **Frontend:** React 18, Vite (port `3000`, HMR), TypeScript, ReactFlow, Tailwind CSS
- **Providers:** Gemini (default, free tier) or OpenAI (paid)

---

## Project structure

```
storyteller/
├── pyproject.toml          # Poetry deps (Python)
├── poetry.lock
├── storyteller_backend/
│   ├── api/                # FastAPI entry point + routes (stories, journeys, personas, corpuses)
│   ├── services/           # LangGraph story agent, image generator, chat-model factory
│   ├── embed_retrieve/     # Corpus ingestion + retrieval (build_database.py, retriever.py)
│   ├── models/             # Pydantic models
│   ├── config/             # settings.py, personas.json, .env(.example)
│   └── tests/              # pytest suite
├── storyteller_frontend/
│   ├── package.json
│   └── src/                # App.tsx, components/, hooks/, services/api.ts
├── data/
│   ├── chroma_db/          # Per-corpus, per-provider vector DBs (gitignored)
│   ├── bm25_indexes/       # Per-corpus BM25 indexes (gitignored)
│   ├── processed_chunks/   # Per-corpus chunk caches (gitignored)
│   └── corpus_registry.json  # Tracked: per-corpus paths
├── raw_texts/              # Source PDFs / text files (gitignored)
├── saved_graphs/           # User journey JSONs (gitignored)
├── documentation/
│   ├── manual-setup.md         # Step-by-step install guide (non-technical users)
│   ├── project_documentation.md # Architecture & developer reference
│   └── next_steps.md           # Historical roadmap + current status
└── CLAUDE.md               # Developer guide for AI assistants
```

---

## Quick start

### Prerequisites

- **Python 3.12+**
- **Poetry 2.x** ([install](https://python-poetry.org/docs/#installation))
- **Node.js 18+**
- A provider API key — pick one:
  - **[Gemini](https://aistudio.google.com/apikey)** — free tier, no card required (recommended for first-time setup)
  - **[OpenAI](https://platform.openai.com/api-keys)** — paid, full functionality (images included)

### One-command install

From the repo root:

```bash
python3 setup.py
```

The script verifies your prerequisites, prompts you for a provider, walks you through adding your API key to `.env`, installs backend + frontend dependencies, downloads the pre-built corpus data from Google Drive, and runs a smoke test. Re-running is safe and idempotent.

Useful flags: `--dry-run` (no settings/data changes), `--force` (re-download corpus data).

For a step-by-step manual fallback, see [`documentation/manual-setup.md`](documentation/manual-setup.md).

> **Important:** dependencies are managed by Poetry. Do **not** run `pip install` — version drift in `chromadb` will silently destroy embedded vector data.

### Run the app

When `setup.py` finishes, open two terminals:

```bash
# Terminal 1 — backend (port 8000)
cd storyteller_backend && poetry run python -m api.main

# Terminal 2 — frontend (port 3000, HMR)
cd storyteller_frontend && npm run dev
```

Verify:

```bash
curl http://localhost:8000/health    # → {"status": "healthy", ...}
open http://localhost:3000           # Storyteller UI
```

API docs: <http://localhost:8000/docs>

---

## Choosing a provider

The default provider is **Gemini** (free tier, no billing required). You can switch to OpenAI in one line.

The active provider is set in [`storyteller_backend/config/settings.py`](storyteller_backend/config/settings.py):

```python
class Config:
    provider: Provider = Provider.GEMINI   # or Provider.OPENAI
```

Each provider's models, RPM, and other knobs are bundled in the `PROVIDER_PROFILES` dict in the same file. Switching providers automatically swaps `chat_model`, `embedding_model`, `image_model`, and rate limits.

### Gemini (free tier — default)

The fastest way to try Storyteller without a credit card. Google's free tier is enough to ingest the bundled corpora and run a handful of story journeys per day. Daily caps and pricing change frequently, so check current limits at <https://aistudio.google.com/rate-limit> if you hit one.

**Structural caveat:** image generation on Gemini is paywalled — free-tier image quota is `0`. Stories still generate fine; they just come without illustrations. Once billing is enabled the image model works normally.

The default chat model is `gemini-2.5-flash-lite`, chosen for higher per-day throughput. `gemini-2.5-flash` produces noticeably richer prose but caps usage tightly on the free tier — see the comment in [`settings.py`](storyteller_backend/config/settings.py) for when to flip.

**Setup:**
1. Get a key at <https://aistudio.google.com/apikey>.
2. Set `GEMINI_API_KEY` in `storyteller_backend/.env`.
3. Confirm `provider: Provider = Provider.GEMINI` in `settings.py` (default).

### OpenAI (paid)

Full functionality including image generation, with usage limits that won't realistically constrain this app. You're paying per call (typically pennies per story), so there's no daily cap to plan around.

**Setup:**
1. Get a key at <https://platform.openai.com/api-keys>.
2. Set `OPENAI_API_KEY` in `storyteller_backend/.env`.
3. In `settings.py`, set `provider: Provider = Provider.OPENAI`.
4. Restart the backend.

---

## Corpora

A corpus is a body of source text the storyteller draws from. Each corpus has its own vector DB (`data/chroma_db/<corpus>_<provider>/`) and BM25 index (`data/bm25_indexes/<corpus>_bm25.pkl`). The registry of corpora lives in [`data/corpus_registry.json`](data/corpus_registry.json).

### Built-in corpora

| Corpus | Chunks | Source |
|---|---|---|
| `mahabharata` | 3870 | Ancient Indian epic |
| `arabian_nights` | 484 | Middle Eastern folk tales |
| `locus_platform_docs` | 227 | Technical documentation example |
| `odyssey` | 218 | Homer's Greek epic |
| `volsunga_saga` | 106 | Norse legendary saga |
| `jataka_tales` | 25 | Buddhist birth stories |

### Building a corpus (ingestion)

Ingestion = chunk the source text, generate per-chunk context summaries (LLM call, cached), embed each chunk (provider-specific, written to ChromaDB), and build a BM25 index. The pipeline is **resumable** — if interrupted (e.g. by a daily quota hit), re-running picks up where it left off.

```bash
cd storyteller_backend
poetry run python -m embed_retrieve.build_database --corpus <name>

# Or via the management CLI:
poetry run python -m embed_retrieve.manage_corpuses build <name>
poetry run python -m embed_retrieve.manage_corpuses list
```

Add `--force-rebuild` to rebuild even if a BM25 index already exists.

**API calls used during ingestion:**
- One **chat** call per chunk for the contextual summary (skipped if cached in `data/processed_chunks/<corpus>/`).
- One **embedding** call per chunk (skipped if already in the target Chroma collection).
- One BM25 build at the end (no API calls).

For pre-built corpora, summaries are already cached, so re-ingesting under a new provider only costs embedding calls. At ~3 s/embedding on Gemini's 20 RPM free-tier limit:

| Corpus | Embedding-only ETA |
|---|---|
| jataka_tales (25) | ~1.5 min |
| volsunga_saga (106) | ~5 min |
| odyssey (218) | ~11 min |
| locus_platform_docs (227) | ~11 min |
| arabian_nights (484) | ~24 min |
| mahabharata (3870) | ~3.2 hours (will hit the 1000/day embedding cap mid-run) |

### Path conventions

- ChromaDB: `data/chroma_db/<corpus>_<provider>/<corpus>_chunks/`
- BM25 (provider-agnostic): `data/bm25_indexes/<corpus>_bm25.pkl`

The same `_<provider>` suffix is applied by both the build script (writer) and the retriever (reader) via the shared `embed_retrieve/paths.py` helper.

### Adding a new corpus

```bash
poetry run python -m embed_retrieve.manage_corpuses add \
  <name> "<Display Name>" "<description>" raw_texts/<source>.pdf --file-type pdf
```

This appends an entry to `data/corpus_registry.json`. Then run `build` (above) to ingest.

> **Note:** the build script currently only handles **PDF** sources via PyMuPDF. Text-source corpora must have their `processed_chunks/<name>/` cache pre-populated.

---

## Personas

Six storyteller personalities live in [`storyteller_backend/config/personas.json`](storyteller_backend/config/personas.json), each with a distinct system prompt, temperature, and color theme:

- **Grandmother** — warm, gentle, nostalgic
- **Professor** — formal, academic, contextual
- **Extreme Summariser** — bulleted facts only, no prose
- **HAL 9000** — calm, eerily logical, breaks the fourth wall
- **Pirate** — boisterous, dramatic, "Aarrr!"
- **Freud** — psychoanalytic narration

The selected persona's `system_prompt` is fed to the chat model; the color theme drives the frontend styling.

---

## Testing

```bash
cd storyteller_backend
poetry run pytest tests/ -v
```

Tests cover the path helper, registry-driven build, provider profile resolution, story-generation node behavior, and screen-prompt classification. The interactive scripts in `embed_retrieve/test_*.py` are out-of-scope for pytest (they're manual smoke tests).

---

## Architecture

- **Story generation** ([`services/story_agent.py`](storyteller_backend/services/story_agent.py)) is a LangGraph state machine. Nodes: `screen_prompt → build_path_context → generate_search_query → retrieve_chunks → generate_story → update_graph_with_story → generate_choices → update_graph_with_choices`. Image generation runs in parallel as soon as enough story text streams in.
- **Provider abstraction** ([`config/settings.py`](storyteller_backend/config/settings.py)) — a `Provider` `StrEnum` and a `ProviderProfile` dataclass map each provider to its models / RPMs / langchain provider keys. Adding a new provider = one new entry in `PROVIDER_PROFILES`.
- **Chat model factory** ([`services/llm.py`](storyteller_backend/services/llm.py)) — `get_chat_llm()` is the single construction site for chat models. It applies `thinking_budget=0` for Gemini automatically (without it, `gemini-2.5-flash` consumes the entire output budget on internal reasoning, producing ~40-word truncated stories instead of 700-word ones).
- **Retrieval** is hybrid: top-K BM25 + top-K vector search (Reciprocal Rank Fusion). See [`embed_retrieve/retriever.py`](storyteller_backend/embed_retrieve/retriever.py).

For a deeper dive, see [`documentation/project_documentation.md`](documentation/project_documentation.md). For a fully step-by-step installation walkthrough (assumes a downloaded corpus snapshot), see [`documentation/manual-setup.md`](documentation/manual-setup.md). For historical project plans, see [`documentation/next_steps.md`](documentation/next_steps.md).

---

## Contributing

Created by [Mehrab Modi](https://github.com/mehrabmodi). Issues and PRs welcome.

## License

MIT — Copyright (c) 2025 Mehrab Modi. See full notice at end of file.

## Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) and [LangChain](https://github.com/langchain-ai/langchain)
- [ChromaDB](https://www.trychroma.com/) for embedded vector storage
- [ReactFlow](https://reactflow.dev/) for graph visualization
- [ELK](https://www.eclipse.org/elk/) for graph layout
- OpenAI [DALL·E 2](https://openai.com/dall-e-2) and Google [Gemini](https://ai.google.dev/) image generation

---

*"Story is our only boat for sailing on the river of time."* — Ursula K. Le Guin

---

<details>
<summary>MIT License (full text)</summary>

Copyright (c) 2025 Mehrab Modi

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

</details>
