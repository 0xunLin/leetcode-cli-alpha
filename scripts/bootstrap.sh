#!/usr/bin/env bash
set -euo pipefail
proj_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "[bootstrap] Project root: $proj_root"
cd "$proj_root"

if ! command -v python >/dev/null 2>&1; then
  echo "Python not found on PATH. Install Python 3.10+ and re-run." >&2
  exit 1
fi

venv_dir="$proj_root/.venv"
if [[ ! -d "$venv_dir" ]]; then
  echo "[bootstrap] Creating virtual environment at $venv_dir ..."
  python -m venv "$venv_dir"
else
  echo "[bootstrap] Virtual environment already exists."
fi

python_exe="$venv_dir/bin/python"
pip_exe="$venv_dir/bin/pip"

echo "[bootstrap] Upgrading pip..."
"$pip_exe" install --upgrade pip setuptools wheel

if [[ -f "requirements.txt" ]]; then
  echo "[bootstrap] Installing requirements..."
  "$pip_exe" install -r requirements.txt
else
  echo "[bootstrap] requirements.txt not found; skipping."
fi

echo "[bootstrap] Installing extras (beautifulsoup4, python-dotenv, typer)..."
"$pip_exe" install beautifulsoup4 python-dotenv typer --upgrade

echo "[bootstrap] Installing Playwright browsers..."
"$python_exe" -m playwright install || echo "[bootstrap] playwright install failed"

if [[ -f ".env.example" && ! -f ".env" ]]; then
  cp .env.example .env
  echo "[bootstrap] Created .env from .env.example. Fill in API keys and credentials."
fi

echo ""
echo "[bootstrap] Done. Next steps:"
echo "  1) Activate venv: source .venv/bin/activate"
echo "  2) Edit .env and add your keys (GEMINI_API_KEY, LEETCODE_EMAIL etc)."
echo "  3) Create Playwright auth (optional): python save_playwright_auth.py"
echo "  4) Try: python cli.py pull two-sum"