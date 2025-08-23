Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $projRoot

Write-Output "[bootstrap] Project root: $projRoot"

# Check python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found on PATH. Install Python 3.10+ and re-run."
    Exit 1
}

$venvDir = Join-Path $projRoot ".venv"
if (-not (Test-Path $venvDir)) {
    Write-Output "[bootstrap] Creating virtual environment at $venvDir ..."
    python -m venv $venvDir
} else {
    Write-Output "[bootstrap] Virtual environment already exists."
}

$pythonExe = Join-Path $venvDir "Scripts\python.exe"
$pipExe = Join-Path $venvDir "Scripts\pip.exe"

# Ensure pip exists (fall back to system python -m pip)
if (-not (Test-Path $pipExe)) {
    Write-Output "[bootstrap] pip not found in venv; using python -m pip ..."
    & $pythonExe -m ensurepip --upgrade
}

Write-Output "[bootstrap] Upgrading pip..."
& $pipExe install --upgrade pip setuptools wheel

# Install requirements
$req = Join-Path $projRoot "requirements.txt"
if (Test-Path $req) {
    Write-Output "[bootstrap] Installing requirements from requirements.txt ..."
    & $pipExe install -r $req
} else {
    Write-Output "[bootstrap] requirements.txt not found; skipping."
}

# Install some extras used by the project (idempotent)
Write-Output "[bootstrap] Installing extras (beautifulsoup4, python-dotenv, typer) ..."
& $pipExe install beautifulsoup4 python-dotenv typer --upgrade

# Install playwright browsers (idempotent)
Write-Output "[bootstrap] Installing Playwright browsers (may take a minute) ..."
try {
    & $pythonExe -m playwright install
} catch {
    Write-Warning "[bootstrap] playwright install failed: $_"
}

# Create .env from example if missing
$envExample = Join-Path $projRoot ".env.example"
$envFile = Join-Path $projRoot ".env"
if ((Test-Path $envExample) -and -not (Test-Path $envFile)) {
    Copy-Item $envExample $envFile
    Write-Output "[bootstrap] Created .env from .env.example. Fill in API keys and credentials."
}

Write-Output ''
Write-Output '[bootstrap] Done. Next steps:'
Write-Output '  1) Activate venv: .\.venv\Scripts\Activate.ps1'
Write-Output '  2) Edit .env and add your keys (GEMINI_API_KEY, LEETCODE_EMAIL etc).'
Write-Output '  3) Create Playwright auth (optional): python save_playwright_auth.py'
Write-Output '  4) Try: python cli.py pull two-sum'

Pop-Location