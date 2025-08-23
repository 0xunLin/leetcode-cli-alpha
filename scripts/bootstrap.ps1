# bootstrap.ps1 - LC-AT setup (Windows PowerShell)

Write-Host "📦 Setting up LC-AT (LeetCode CLI Assistant)..."

# Move into project root (the folder where this script lives)
Push-Location $PSScriptRoot

# 1. Create venv if missing
if (!(Test-Path ".venv")) {
    Write-Host "🔧 Creating virtual environment..."
    python -m venv .venv
}

# 2. Activate venv
Write-Host "🔧 Activating virtual environment..."
& .\.venv\Scripts\Activate.ps1

# 3. Upgrade pip
Write-Host "⬆️ Upgrading pip..."
pip install --upgrade pip

# 4. Install dependencies
if (Test-Path "requirements.txt") {
    Write-Host "📥 Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
}
Write-Host "📥 Installing extras..."
pip install playwright beautifulsoup4 python-dotenv

# 5. Install Playwright browsers
Write-Host "🌐 Installing Playwright browsers..."
python -m playwright install

# 6. Copy .env.example if .env doesn’t exist
if (!(Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
    Write-Host "⚙️ Created .env (please edit it with your API keys and credentials)."
}

Pop-Location

Write-Host "`n✅ Setup complete! Next steps:"
Write-Host "  .\\.venv\\Scripts\\Activate.ps1"
Write-Host "  python cli.py pull two-sum"
