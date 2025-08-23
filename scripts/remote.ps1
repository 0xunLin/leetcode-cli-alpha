Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoUrl = "https://github.com/0xunLin/leetcode-cli-alpha.git"
$projDir = "leetcode-cli-alpha"

# Clone if missing
if (-not (Test-Path $projDir)) {
    Write-Output "[remote] Cloning repo from $repoUrl ..."
    git clone $repoUrl
} else {
    Write-Output "[remote] Repo already exists, pulling latest ..."
    Push-Location $projDir
    git pull
    Pop-Location
}

Push-Location $projDir

# Run bootstrap
Write-Output "[remote] Running bootstrap.ps1 ..."
& powershell -ExecutionPolicy Bypass -File "scripts/bootstrap.ps1"

# Create .env if missing
if ((Test-Path ".env.example") -and -not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Output "[remote] Created .env from .env.example"
}

Pop-Location

Write-Output "`n✅ Project ready. Next steps:"
Write-Output "  cd $projDir"
Write-Output "  Open '.env' and set values:"
Write-Output "    GEMINI_API_KEY        (optional) your Gemini / Google GenAI API key"
Write-Output "    GEMINI_MODEL, GEMINI_ENDPOINT (only if using custom model/endpoint)"
Write-Output "    LEETCODE_EMAIL, LEETCODE_PASSWORD (optional, for first-time login)"
Write-Output "    LEETCODE_AUTH_STATE   (optional, Playwright storage state JSON)"
Write-Output "`n⚠️  Security: never commit .env, auth files, or API keys."
