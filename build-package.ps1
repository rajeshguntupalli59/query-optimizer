# build-package.ps1 — Build a clean client delivery ZIP
# Usage: powershell -ExecutionPolicy Bypass -File build-package.ps1

$version  = "1.0"
$name     = "queryoptimizer-v$version"
$root     = $PSScriptRoot
$out      = "$root\dist"
$staging  = "$out\$name"
$zipPath  = "$out\$name.zip"

Write-Host "Building $name.zip ..."

# Clean previous build
if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
if (Test-Path $zipPath)  { Remove-Item $zipPath  -Force }
New-Item -ItemType Directory -Path $staging | Out-Null

# Files and directories to include (whitelist approach)
$include = @(
    "backend",
    "frontend",
    "docs",
    "data",
    "docker-compose.yml",
    ".env.example",
    "setup.ps1",
    "setup.sh",
    "README.md",
    "CHANGELOG.md",
    "LICENSE"
)

# Directories/files to exclude within the included tree
$excludeNames = @(
    ".venv",
    "__pycache__",
    "*.pyc",
    "node_modules",
    ".git",
    ".gitignore",
    "dist",
    "build",
    ".claude",
    "*.log",
    ".secret_key",
    "queryoptimizer.db",
    "tools"          # seller-only keygen scripts
)

foreach ($item in $include) {
    $src = Join-Path $root $item
    if (-not (Test-Path $src)) {
        Write-Warning "  Skipping (not found): $item"
        continue
    }
    $dst = Join-Path $staging $item
    if (Test-Path $src -PathType Container) {
        Copy-Item $src $dst -Recurse -Force
    } else {
        $parentDir = Split-Path $dst -Parent
        if (-not (Test-Path $parentDir)) { New-Item -ItemType Directory -Path $parentDir | Out-Null }
        Copy-Item $src $dst -Force
    }
}

# Remove excluded items from the staging tree
foreach ($pattern in $excludeNames) {
    Get-ChildItem $staging -Recurse -Force -Include $pattern |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

# Create an empty data/ placeholder so volume mount works on first run
$dataDir = Join-Path $staging "data"
if (-not (Test-Path $dataDir)) { New-Item -ItemType Directory -Path $dataDir | Out-Null }
New-Item -ItemType File -Path (Join-Path $dataDir ".gitkeep") -Force | Out-Null

# Zip
Compress-Archive -Path "$staging\*" -DestinationPath $zipPath -Force

# Summary
$sizeMB = [math]::Round((Get-Item $zipPath).Length / 1MB, 2)
Write-Host ""
Write-Host "Done: $zipPath ($sizeMB MB)"
Write-Host ""
Write-Host "Contents:"
Get-ChildItem $staging | ForEach-Object { Write-Host "  $($_.Name)" }
Write-Host ""
Write-Host "Deliver $name.zip to the client."
