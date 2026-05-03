#!/usr/bin/env python3
"""Storyteller — one-shot installer.

Usage:
    python3 setup.py              # interactive install
    python3 setup.py --dry-run    # show what would happen, install backend deps,
                                  # but don't write settings.py, don't download,
                                  # don't run the smoke test
    python3 setup.py --force      # re-download corpus data even if data/ is populated

Cross-platform: macOS / Linux / WSL / Windows. Uses pathlib + list-form
subprocess + shutil.which to find executables (handles .exe and .cmd on Windows).
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


# ============================================================
# Constants
# ============================================================

REPO_ROOT = Path(__file__).resolve().parent
BACKEND = REPO_ROOT / "storyteller_backend"
FRONTEND = REPO_ROOT / "storyteller_frontend"
DATA = REPO_ROOT / "data"
ENV_FILE = BACKEND / ".env"
ENV_EXAMPLE = BACKEND / ".env.example"
SETTINGS_FILE = BACKEND / "config" / "settings.py"

# Public Drive folder containing chroma_db/, bm25_indexes/, processed_chunks/, corpus_registry.json
GDRIVE_URL = "https://drive.google.com/drive/folders/1iidSrv-En0VMZSNoDGswP1G_Tm3Amstw?usp=sharing"

MIN_PYTHON = (3, 12)
MIN_NODE = 18

GEMINI_KEY_NAME = "GEMINI_API_KEY"
OPENAI_KEY_NAME = "OPENAI_API_KEY"
PLACEHOLDER_VALUES = {
    "your-gemini-api-key-here",
    "your-openai-api-key-here",
    "sk-your-openai-api-key-here",
}


# ============================================================
# Pretty printing
# ============================================================

def info(msg: str) -> None:
    print(f"  {msg}")


def step(msg: str) -> None:
    print(f"\n▶ {msg}")


def ok(msg: str) -> None:
    print(f"  ✓ {msg}")


def warn(msg: str) -> None:
    print(f"  ⚠ {msg}")


def err(msg: str) -> None:
    print(f"  ✗ {msg}", file=sys.stderr)


# ============================================================
# Pure helpers (unit-testable; no I/O)
# ============================================================

def parse_node_major(version_string: str) -> Optional[int]:
    """Extract the major version from a `node --version` output like 'v20.10.0'."""
    match = re.match(r"v?(\d+)\.", version_string.strip())
    return int(match.group(1)) if match else None


def parse_provider_choice(raw: str) -> Optional[str]:
    """Map a free-form prompt response to 'gemini' / 'openai' / None.

    Empty string defaults to gemini.
    """
    s = raw.strip().lower()
    if s in ("", "g", "gemini"):
        return "gemini"
    if s in ("o", "openai"):
        return "openai"
    return None


def env_has_real_key(env_text: str, key_name: str) -> bool:
    """Return True if env_text contains an uncommented `key_name=<non-placeholder>` line."""
    for raw_line in env_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if not line.startswith(f"{key_name}="):
            continue
        value = line.split("=", 1)[1].strip().strip('"').strip("'")
        if value and value not in PLACEHOLDER_VALUES:
            return True
        return False
    return False


def apply_provider_to_settings(settings_text: str, provider: str) -> str:
    """Return settings_text with `provider: Provider = Provider.<X>` set to the chosen provider.

    Raises ValueError if the assignment isn't found.
    """
    target = f"Provider.{provider.upper()}"
    pattern = re.compile(r"^(\s*provider:\s*Provider\s*=\s*)Provider\.\w+", re.MULTILINE)
    if not pattern.search(settings_text):
        raise ValueError("Could not find 'provider: Provider = Provider.X' assignment in settings.py")
    return pattern.sub(rf"\1{target}", settings_text, count=1)


# ============================================================
# Step implementations
# ============================================================

def check_prereqs() -> None:
    step("Checking prerequisites…")

    # Python (we are running, so this just gates by version)
    if sys.version_info < MIN_PYTHON:
        err(
            f"Need Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+; "
            f"have {sys.version_info.major}.{sys.version_info.minor}"
        )
        sys.exit(1)
    ok(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # Poetry
    poetry = shutil.which("poetry")
    if not poetry:
        err("Poetry not found on PATH.")
        info("  Install: https://python-poetry.org/docs/#installation")
        sys.exit(1)
    poetry_version = subprocess.run(
        [poetry, "--version"], capture_output=True, text=True, check=False
    ).stdout.strip()
    ok(poetry_version or "Poetry (version unknown)")

    # Node
    node = shutil.which("node")
    if not node:
        err("Node.js not found on PATH.")
        info("  Install: https://nodejs.org/")
        sys.exit(1)
    node_version_raw = subprocess.run(
        [node, "--version"], capture_output=True, text=True, check=False
    ).stdout.strip()
    major = parse_node_major(node_version_raw)
    if major is None or major < MIN_NODE:
        err(f"Need Node.js {MIN_NODE}+; have {node_version_raw or 'unknown'}")
        sys.exit(1)
    ok(f"Node.js {node_version_raw}")

    # npm (may be a .cmd on Windows; shutil.which handles that)
    npm = shutil.which("npm")
    if not npm:
        err("npm not found on PATH (usually bundled with Node.js).")
        sys.exit(1)


def prompt_provider() -> str:
    step("Provider choice")
    while True:
        raw = input("  Which provider? [G]emini (free) / [O]penAI (paid) [G]: ")
        choice = parse_provider_choice(raw)
        if choice:
            ok(f"Provider: {choice}")
            return choice
        warn("Please answer G or O.")


def show_env_instructions(provider: str, dry_run: bool) -> None:
    step("API key configuration")

    key_name = GEMINI_KEY_NAME if provider == "gemini" else OPENAI_KEY_NAME
    key_url = (
        "https://aistudio.google.com/apikey"
        if provider == "gemini"
        else "https://platform.openai.com/api-keys"
    )

    info(f"You need to add your {provider.upper()} API key to your .env file.")
    info("")
    if not ENV_FILE.exists():
        rel_example = ENV_EXAMPLE.relative_to(REPO_ROOT)
        rel_env = ENV_FILE.relative_to(REPO_ROOT)
        info(f"  1. Copy the template:")
        info(f"       cp {rel_example} {rel_env}")
        info(f"  2. Open {rel_env} in any text editor.")
    else:
        rel_env = ENV_FILE.relative_to(REPO_ROOT)
        info(f"  1. Open {rel_env} in any text editor.")
    info(f"  2. Set:  {key_name}=<paste your key>")
    if provider == "openai":
        info(f"           (uncomment the line if it starts with #)")
    info(f"  3. Save the file.")
    info("")
    info(f"  Get a key from: {key_url}")
    info("")

    if dry_run:
        ok("(dry-run) skipping wait + verification")
        return

    while True:
        try:
            input("  Press Enter when your .env is ready (or Ctrl-C to abort)... ")
        except (KeyboardInterrupt, EOFError):
            print()
            err("Aborted.")
            sys.exit(130)

        if not ENV_FILE.exists():
            warn(f"{ENV_FILE.relative_to(REPO_ROOT)} not found yet; please copy and edit it first.")
            continue
        if env_has_real_key(ENV_FILE.read_text(encoding="utf-8"), key_name):
            ok(f"{key_name} present in .env")
            return
        warn(f"{key_name} is missing or still set to a placeholder; please update .env.")


def update_provider_setting(provider: str, dry_run: bool) -> None:
    step("Provider toggle in settings.py")
    if not SETTINGS_FILE.exists():
        err(f"{SETTINGS_FILE} not found.")
        sys.exit(1)

    text = SETTINGS_FILE.read_text(encoding="utf-8")
    try:
        new_text = apply_provider_to_settings(text, provider)
    except ValueError as e:
        err(str(e))
        sys.exit(1)

    if new_text == text:
        ok(f"settings.py already on Provider.{provider.upper()}; no change.")
        return
    if dry_run:
        ok(f"(dry-run) would update settings.py: provider = Provider.{provider.upper()}")
        return
    SETTINGS_FILE.write_text(new_text, encoding="utf-8")
    ok(f"Updated settings.py: provider = Provider.{provider.upper()}")


def install_backend(dry_run: bool) -> None:
    # poetry install runs in dry-run too — it's idempotent and required for downstream
    step("Installing backend dependencies (poetry install)…")
    poetry = shutil.which("poetry")
    if poetry is None:
        err("Poetry not on PATH.")
        sys.exit(1)
    result = subprocess.run([poetry, "install"], cwd=BACKEND, check=False)
    if result.returncode != 0:
        err("poetry install failed.")
        sys.exit(1)
    ok("Backend dependencies installed.")


def install_frontend(dry_run: bool) -> None:
    step("Installing frontend dependencies (npm install)…")
    npm = shutil.which("npm")
    if npm is None:
        err("npm not on PATH.")
        sys.exit(1)
    result = subprocess.run([npm, "install"], cwd=FRONTEND, check=False)
    if result.returncode != 0:
        err("npm install failed.")
        sys.exit(1)
    ok("Frontend dependencies installed.")


def _flatten_data_after_download() -> None:
    """If gdown nested the contents under a single subdir, lift them up to data/."""
    if (DATA / "corpus_registry.json").exists():
        return  # already flat
    candidates = [d for d in DATA.iterdir() if d.is_dir() and (d / "corpus_registry.json").exists()]
    if len(candidates) != 1:
        warn(
            f"Couldn't auto-flatten downloaded data: expected exactly one nested folder "
            f"with corpus_registry.json, found {len(candidates)}."
        )
        return
    nested = candidates[0]
    info(f"Flattening downloaded data: moving contents of {nested.name}/ up into data/")
    for item in nested.iterdir():
        target = DATA / item.name
        if target.exists():
            warn(f"  skipping {item.name} (already exists in data/)")
            continue
        shutil.move(str(item), str(target))
    try:
        nested.rmdir()
    except OSError:
        warn(f"  {nested.name}/ not empty; leaving it.")


def download_corpus(dry_run: bool, force: bool) -> None:
    step("Corpus data")
    DATA.mkdir(exist_ok=True)

    already_populated = (
        (DATA / "corpus_registry.json").exists()
        and (DATA / "chroma_db").exists()
    )
    if already_populated and not force:
        ok("data/ already populated; skipping download. (Use --force to redownload.)")
        return

    if dry_run:
        ok(f"(dry-run) would download from: {GDRIVE_URL}")
        ok(f"(dry-run) would land into:    {DATA}")
        return

    try:
        import gdown  # type: ignore[import-not-found]
    except ImportError:
        err("gdown not available. Did 'poetry install' succeed?")
        info("  Run: cd storyteller_backend && poetry install")
        sys.exit(1)

    info("Downloading corpus data from Google Drive (this may take several minutes)…")
    try:
        gdown.download_folder(
            GDRIVE_URL,
            output=str(DATA),
            quiet=False,
            use_cookies=False,
        )
    except Exception as e:
        err(f"Download failed: {e}")
        info("  You can manually download from:")
        info(f"  {GDRIVE_URL}")
        info(f"  and copy the contents into: {DATA}/")
        sys.exit(1)

    _flatten_data_after_download()

    if not (DATA / "corpus_registry.json").exists():
        warn("corpus_registry.json not found in data/ after download.")
        warn(f"Inspect {DATA}/ and resolve manually before running the app.")
        return
    ok("Corpus data downloaded.")


def smoke_test(dry_run: bool) -> None:
    step("Smoke test")
    if dry_run:
        ok("(dry-run) would import HybridRetriever and load the mahabharata corpus.")
        return

    poetry = shutil.which("poetry")
    if poetry is None:
        err("Poetry not on PATH.")
        sys.exit(1)

    code = (
        "from embed_retrieve.retriever import HybridRetriever; "
        "r = HybridRetriever(corpus_name='mahabharata'); "
        "print(f'mahabharata: {r.chroma_collection.count()} vectors')"
    )
    result = subprocess.run(
        [poetry, "run", "python", "-c", code],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        err("Smoke test failed:")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        info("  Most common cause: chroma_db folders need a `_<provider>` suffix.")
        info("  Inspect data/chroma_db/ — folders should be named e.g. mahabharata_gemini/.")
        sys.exit(1)
    ok(result.stdout.strip())


def final_message() -> None:
    step("Ready 🎉")
    info("To run Storyteller, open two terminals:")
    info("")
    info("  Terminal 1 (backend):")
    info("     cd storyteller_backend && poetry run python -m api.main")
    info("")
    info("  Terminal 2 (frontend):")
    info("     cd storyteller_frontend && npm run dev")
    info("")
    info("Then open http://localhost:3000 in your browser.")


# ============================================================
# Entry point
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="Storyteller one-shot installer.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen; don't edit settings.py, don't download, don't run smoke test. "
        "(poetry install / npm install still run.)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download corpus data even if data/ is already populated.",
    )
    args = parser.parse_args()

    print("Storyteller setup")
    print("=================")
    if args.dry_run:
        info("Mode: DRY-RUN (no settings.py edits, no download, no smoke test)")

    try:
        check_prereqs()
        provider = prompt_provider()
        show_env_instructions(provider, dry_run=args.dry_run)
        update_provider_setting(provider, dry_run=args.dry_run)
        install_backend(dry_run=args.dry_run)
        install_frontend(dry_run=args.dry_run)
        download_corpus(dry_run=args.dry_run, force=args.force)
        smoke_test(dry_run=args.dry_run)
        final_message()
    except KeyboardInterrupt:
        print()
        err("Aborted.")
        sys.exit(130)


if __name__ == "__main__":
    main()
