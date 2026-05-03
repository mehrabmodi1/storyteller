# Storyteller — Manual Setup

A step-by-step guide to install and run Storyteller on your machine.

**This guide assumes:**
- You've already cloned the repository.
- You have a folder of pre-built corpus data downloaded somewhere on your computer (typically a `storyteller_data` archive shared by the maintainer, containing `chroma_db/`, `bm25_indexes/`, etc.).

For project architecture and developer-level documentation, see [`project_documentation.md`](project_documentation.md).

---

## 1. Install prerequisites

You need three things on your machine. Skip any you already have.

- **Python 3.12 or later** — [download](https://www.python.org/downloads/)
- **Poetry 2.x** (Python's dependency manager) — [install instructions](https://python-poetry.org/docs/#installation)
- **Node.js 18 or later** — [download](https://nodejs.org/)

Verify each in a terminal:

```bash
python3 --version    # 3.12.x or higher
poetry --version     # Poetry (version 2.x.x)
node --version       # v18.x.x or higher
```

If any command isn't found, finish installing it before continuing.

---

## 2. Get an API key

Storyteller needs at least one provider key. Pick **one** option:

### Option A — Gemini (free tier, no credit card)

1. Visit <https://aistudio.google.com/apikey>
2. Click **Create API key**
3. Copy the key somewhere safe — you'll paste it in the next step.

### Option B — OpenAI (paid, full features including images)

1. Visit <https://platform.openai.com/api-keys>
2. Click **Create new secret key**
3. Copy the key.

---

## 3. Configure the API key

Open a terminal and navigate into the cloned repo:

```bash
cd <path-to-cloned-repo>/storyteller_backend
cp .env.example .env
```

Open `.env` in any text editor. You'll see:

```
GEMINI_API_KEY=your-gemini-api-key-here
# OPENAI_API_KEY=sk-your-openai-api-key-here
```

- **If you're using Gemini:** replace `your-gemini-api-key-here` with the key from step 2.
- **If you're using OpenAI:** delete the `#` at the start of the second line, then replace `sk-your-openai-api-key-here` with your key.

Save and close the file.

### If you chose OpenAI, also switch the active provider

Open `storyteller_backend/config/settings.py` in a text editor. Near the top of the `Config` class, find:

```python
provider: Provider = Provider.GEMINI
```

Change it to:

```python
provider: Provider = Provider.OPENAI
```

Save the file.

---

## 4. Install dependencies

### Backend

```bash
cd <path-to-cloned-repo>/storyteller_backend
poetry install
```

This downloads all Python packages. The first run takes a couple of minutes.

### Frontend

```bash
cd <path-to-cloned-repo>/storyteller_frontend
npm install
```

This downloads JavaScript packages. Also a few minutes the first time.

---

## 5. Drop in the pre-built corpus data

### Where to download

Pre-built corpus embeddings (Chroma vectors, BM25 indexes, chunk caches, and registry) are hosted on Google Drive:

**[Storyteller corpus data — Google Drive](https://drive.google.com/drive/folders/1iidSrv-En0VMZSNoDGswP1G_Tm3Amstw?usp=sharing)**

Download the folder (or its individual subfolders) to your machine. The contents look like:

```
<download>/
├── chroma_db/
├── bm25_indexes/
├── processed_chunks/
└── corpus_registry.json
```

### Where to put it

Copy everything inside the downloaded folder into the repo's `data/` directory:

```bash
cp -R <download>/. <path-to-cloned-repo>/data/
```

> Replace `<download>` with the actual download path, e.g. `~/Downloads/storyteller_data`.

### Add the provider suffix to chroma folders (if needed)

Look inside `data/chroma_db/`. If you see folders **without** an `_openai` or `_gemini` suffix:

```
data/chroma_db/mahabharata
data/chroma_db/odyssey
...
```

…they need to be renamed to match your provider. Run **one** of these (the matching one for your provider):

**For OpenAI:**
```bash
cd <path-to-cloned-repo>/data/chroma_db
for c in arabian_nights jataka_tales locus_platform_docs mahabharata odyssey volsunga_saga; do
  mv "$c" "${c}_openai"
done
```

**For Gemini:**
```bash
cd <path-to-cloned-repo>/data/chroma_db
for c in arabian_nights jataka_tales locus_platform_docs mahabharata odyssey volsunga_saga; do
  mv "$c" "${c}_gemini"
done
```

If the folder names already end in `_openai` or `_gemini`, you can skip this step.

---

## 6. Run Storyteller

You'll need **two** terminal windows (or two tabs) — one for the backend, one for the frontend.

### Terminal 1 — backend

```bash
cd <path-to-cloned-repo>/storyteller_backend
poetry run python -m api.main
```

You should see `Application startup complete` and the server listening on port 8000.

### Terminal 2 — frontend

```bash
cd <path-to-cloned-repo>/storyteller_frontend
npm run dev
```

You should see Vite report `Local: http://localhost:3000`.

---

## 7. Open the app

Open your web browser and go to:

**<http://localhost:3000>**

You should see the Storyteller UI. Pick a corpus, pick a persona, type a prompt, and submit. The story should stream in within a few seconds.

---

## Troubleshooting

**Backend exits with `GEMINI_API_KEY is required` (or `OPENAI_API_KEY`):**
The `.env` file is missing the right key. Re-check step 3.

**Backend logs `Collection [<corpus>_chunks] does not exist` when you submit a prompt:**
The chroma folder for that corpus is missing or has the wrong name. Re-check step 5 — folder names must end in `_openai` or `_gemini` matching your provider.

**Frontend shows "Network Error" when submitting:**
The backend isn't running, or isn't on port 8000. Check Terminal 1.

**Backend logs a `429` quota error mid-story (Gemini only):**
You've hit Gemini's free-tier daily cap. Wait until tomorrow, enable billing on your Google project, or switch to OpenAI (see step 3).

**Stories generate but no images appear (Gemini only):**
Image generation on Gemini's free tier is disabled by Google (quota = 0). Either enable Gemini billing, or switch the provider to OpenAI for full functionality. Story text generation still works fine without images.

For deeper troubleshooting and architectural detail, see [`project_documentation.md`](project_documentation.md).
