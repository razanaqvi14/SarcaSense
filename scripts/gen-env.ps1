# Windows PowerShell equivalent of gen-env.sh: creates .env with fresh random secrets.
# Run from anywhere:  powershell -ExecutionPolicy Bypass -File scripts\gen-env.ps1
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (Test-Path .env) {
    Write-Error ".env already exists; leaving it untouched."
    exit 1
}

function New-Hex([int]$bytes) {
    $b = New-Object byte[] $bytes
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
    -join ($b | ForEach-Object { $_.ToString("x2") })
}

$lines = Get-Content .env.example | ForEach-Object {
    if     ($_ -like "POSTGRES_PASSWORD=*") { "POSTGRES_PASSWORD=$(New-Hex 24)" }
    elseif ($_ -like "SECRET_KEY=*")        { "SECRET_KEY=$(New-Hex 32)" }
    else                                    { $_ }
}
# ASCII on purpose: Windows PowerShell 5.1's default UTF-8 adds a BOM that breaks docker compose.
Set-Content -Path .env -Value $lines -Encoding ascii
Write-Host "Created .env (COOKIE_SECURE=false for local http; set true behind HTTPS)."
