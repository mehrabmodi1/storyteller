# Storyteller — Setup

A guide to install and run Storyteller on your machine.

This guide assumes you've already cloned the repository.

For project architecture and developer-level documentation, see [`project_documentation.md`](project_documentation.md).

---

## Recommended: one-command install

A setup script handles dependency install, corpus download, and smoke-test in a single run. Most users should use this path.

### 1. Install prerequisites

You need three things installed already:

- **Python 3.12 or later** — [download](https://www.python.org/downloads/)
- **Poetry 2.x** (Python's dependency manager) — [install instructions](https://python-poetry.org/docs/#installation)
- **Node.js 18 or later** — [download](https://nodejs.org/)

The script will fail fast and tell you which one is missing if any are not on PATH.

### 2. Run the setup script

From the cloned repo's root directory:

```bash
python3 setup.py
```

The script will:

1. Verify the prerequisites are present.
2. Ask which provider you want (Gemini free / OpenAI paid).
3. Prompt you to add your API key to `storyteller_backend/.env`. **You write the key yourself in your editor of choice — the script never handles it.** It then verifies the key is set before proceeding.
4. Update `config/settings.py` to your chosen provider (if needed).
5. Run `poetry install` (backend) and `npm install` (frontend).
6. Download the pre-built corpus data from Google Drive into `data/`.
7. Run a smoke test: load the Mahabharata corpus through the retriever and report its vector count.

The script is idempotent — re-running is safe and skips work that's already done.

### Useful flags

- `--dry-run` — show what would happen without editing `settings.py`, downloading, or running the smoke test. (Dependency installs still run; they're idempotent.)
- `--force` — re-download corpus data even if `data/` is already populated.

### 3. Run the app

When the script finishes, open two terminals:

```bash
# Terminal 1 — backend (port 8000)
cd storyteller_backend && poetry run python -m api.main

# Terminal 2 — frontend (port 3000)
cd storyteller_frontend && npm run dev
```

Open <http://localhost:3000> in your browser.

---

## Manual fallback

If the setup script doesn't work for you (e.g. corporate network blocking Google Drive, or you'd rather do each step yourself), follow these:

### A. Configure your API key

```bash
cd <repo>/storyteller_backend
cp .env.example .env
```

Open `.env` and set:
- `GEMINI_API_KEY=<your key>` — get one from <https://aistudio.google.com/apikey>, **or**
- `OPENAI_API_KEY=sk-<your key>` — get one from <https://platform.openai.com/api-keys>

If you chose OpenAI, also edit `storyteller_backend/config/settings.py` and change `provider: Provider = Provider.GEMINI` to `Provider.OPENAI`.

### B. Install dependencies

```bash
cd <repo>/storyteller_backend && poetry install
cd <repo>/storyteller_frontend && npm install
```

### C. Download corpus data

Manually download from **[Storyteller corpus data — Google Drive](https://drive.google.com/drive/folders/1iidSrv-En0VMZSNoDGswP1G_Tm3Amstw?usp=sharing)** and copy the contents into `<repo>/data/`. After copying, the directory should contain `chroma_db/`, `bm25_indexes/`, `processed_chunks/`, and `corpus_registry.json`.

### D. Run the app

Same as step 3 above.

---

## Troubleshooting

**`GEMINI_API_KEY is required` (or `OPENAI_API_KEY`):**
The `.env` file is missing the key, or you set the wrong provider's key. Re-check section A.

**`Collection [<corpus>_chunks] does not exist` when submitting a story:**
The chroma folder layout doesn't match the active provider. Inspect `data/chroma_db/` — folders should end in `_openai` or `_gemini` matching what `config/settings.py` is set to. The setup script handles this on download; for manual installs, the Drive snapshot is laid out for the default provider, so this only comes up if you switched providers without re-downloading.

**Frontend shows "Network Error" when submitting:**
Backend isn't running, or isn't on port 8000. Check Terminal 1.

**`429` quota error mid-story (Gemini only):**
You've hit Gemini's free-tier daily cap. Wait until tomorrow, enable billing on your Google project, or switch to OpenAI.

**Stories generate but no images appear (Gemini only):**
Image generation is paywalled on Gemini's free tier. Either enable Gemini billing or switch the provider to OpenAI for full functionality. Story text generation still works fine.

For deeper troubleshooting and architectural detail, see [`project_documentation.md`](project_documentation.md).
