# Repository Guidelines

## Project Structure & Module Organization
- Core scripts live in the repo root: `gen_devotion_audio.py`, `gen_bread_audio.py`, `gen_gemini_tts_audio.py`, `gen_google_tts_audio.py`, and helpers like `bible_parser.py`, `tts.py`, `tts2.py`.
- Shared utilities (e.g., Bible reference normalization) stay in `bible_parser.py`; import from there rather than duplicating logic.
- Temporary exports default to `/Users/mhuo/Downloads/`; keep repo clean of generated `.mp3`/`.aiff` by respecting `.gitignore`.
- Place experimental agents or notebooks under a new `experiments/` directory to avoid cluttering the root.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: create an isolated Python 3.11+ environment.
- `pip install -r requirements.txt`: install Google Cloud TTS, edge-tts, pydub, and other runtime deps.
- `python gen_devotion_audio.py` (or any other `gen_*` script): generate devotion audio using the script’s configured voices and paths.
- `python m4a2mp3.py <input.m4a>`: convert existing audio assets when you only need transcoding.

## Coding Style & Naming Conventions
- Follow PEP 8: 4-space indentation, snake_case for functions/modules, UPPER_CASE for constants like voice IDs.
- Keep script entry points under `if __name__ == "__main__":` so modules stay importable.
- Use descriptive suffixes (`*_audio.py`, `*_tts.py`) for new generators to signal purpose.
- Run `python -m compileall .` or a quick `ruff`/`flake8` pass locally if available to catch syntax issues.

## Testing Guidelines
- No formal test suite exists; add targeted smoke scripts under `tests/` that import shared helpers and call key functions with short sample text.
- Before pushing, run the relevant `python gen_*` script with a trimmed input paragraph and verify the MP3 in `/Users/mhuo/Downloads/`.
- Validate Bible reference parsing by calling `bible_parser.convert_bible_reference` in a REPL and confirming tone-mark safe output.

## Commit & Pull Request Guidelines
- Follow the existing history’s succinct imperative style: `add gen_gemini_tts`, `rename to gen_google_tts_audio.py`.
- Each PR should describe the devotional workflow impacted, any new environment variables, and attach short audio diffs or console excerpts when useful.
- Reference Jira/GitHub issues in the description (`Fixes #123`) and call out credential or path changes explicitly.

## Security & Configuration Tips
- Store Google Cloud JSON keys outside the repo and point to them via `GOOGLE_APPLICATION_CREDENTIALS`.
- Never commit generated audio or credentials; verify `.gitignore` before staging.
- Document required voices or region-specific settings at the top of each script so agents can rotate keys without code archaeology.
