#!/usr/bin/env bash
set -euo pipefail

repo_url="https://github.com/0xunLin/leetcode-cli-alpha.git"
proj_dir="leetcode-cli-alpha"

if [ ! -d "$proj_dir" ]; then
  echo "[remote] Cloning repo from $repo_url ..."
  git clone "$repo_url"
else
  echo "[remote] Repo already exists, pulling latest ..."
  (cd "$proj_dir" && git pull)
fi

cd "$proj_dir"

echo "[remote] Running bootstrap.sh ..."
bash scripts/bootstrap.sh

if [[ -f ".env.example" && ! -f ".env" ]]; then
  cp .env.example .env
  echo "[remote] Created .env from .env.example"
fi

echo ""
echo "✅ Project ready. Next steps:"
echo "  cd $proj_dir"
echo "  Open '.env' and set values:"
echo "    GEMINI_API_KEY        (optional) your Gemini / Google GenAI API key"
echo "    GEMINI_MODEL, GEMINI_ENDPOINT (only if using custom model/endpoint)"
echo "    LEETCODE_EMAIL, LEETCODE_PASSWORD (optional, for first-time login)"
echo "    LEETCODE_AUTH_STATE   (optional, Playwright storage state JSON)"
echo ""
echo "⚠️  Security: never commit .env, auth files, or API keys."
