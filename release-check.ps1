# release-check.ps1 - automated GitHub release readiness check
# Usage:
#   .\release-check.ps1              # full check (git + secrets + versions + tests + build + compose)
#   .\release-check.ps1 -SkipTests   # quick pass without pytest/build/compose
#   .\release-check.ps1 -Branch main # use a different expected branch

param(
    [string]$Branch = "master",
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$script:Failures = New-Object System.Collections.Generic.List[string]
$script:Warnings  = New-Object System.Collections.Generic.List[string]

function Step($name) { Write-Host "`n==> $name" -ForegroundColor Cyan }
function Ok($msg)    { Write-Host "   OK   $msg" -ForegroundColor Green }
function Warn($msg)  { Write-Host "   WARN $msg" -ForegroundColor Yellow; $script:Warnings.Add($msg) }
function Fail($msg)  { Write-Host "   FAIL $msg" -ForegroundColor Red;   $script:Failures.Add($msg) }

# --- 0. Repo root -----------------------------------------------------
Step "Repo root"
$root = git rev-parse --show-toplevel 2>$null
if ($LASTEXITCODE -ne 0) { Fail "not a git repository"; exit 1 }
Set-Location $root
Ok $root

# --- 1. Forbidden files in index --------------------------------------
Step "Forbidden files tracked by git"
$forbidden = git ls-files | Select-String -Pattern '(^|/)(\.env|\.env\.docker)$|(^|/)\.venv/|node_modules/|\.db$|\.sqlite3?$|__pycache__/|^dist/|frontend/dist/|\.pytest_cache/'
if ($forbidden) { $forbidden | ForEach-Object { Fail "tracked: $_" } } else { Ok "no .env / venv / node_modules / db / caches tracked" }

# --- 2. Secret scan ----------------------------------------------------
Step "Secret scan"
$hotPattern = '(BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[0-9A-Z]{16}|xox[bap]-[A-Za-z0-9-]{10,})'
$hot = git grep -n -I -iE $hotPattern 2>$null
if ($hot) { $hot | ForEach-Object { Fail "possible real secret: $_" } } else { Ok "no high-confidence secrets (keys/tokens)" }

$suspectPattern = '(password|secret|api_key|apikey|token)\s*[=:]\s*["'']?[A-Za-z0-9][A-Za-z0-9_\-]{6,}'
$suspects = git grep -n -I -iE $suspectPattern 2>$null |
    Where-Object { $_ -notmatch "change-me|placeholder|dummy|postgres:postgres|your[-_]|example" } |
    Where-Object { $_ -notmatch "access_token\s*=|refresh_token\s*=|hashed_password\s*=\s*hash_password|token_type|Authorization.*Bearer|blacklist_token\(|decode_token\(|create_access_token|create_refresh_token" }
if ($suspects) { Warn "$($suspects.Count) line(s) mention secret-like assignments - review manually:"; $suspects | Select-Object -First 8 | ForEach-Object { Write-Host "     $_" -ForegroundColor DarkYellow } }
else { Ok "no suspicious assignments beyond known placeholders" }

# --- 3. Branch ----------------------------------------------------------
Step "Branch"
$current = git branch --show-current
if ($current -eq $Branch) { Ok "on '$current'" } else { Fail "on '$current', expected '$Branch'" }

# --- 4. Version consistency --------------------------------------------
Step "Version consistency"
$ver = @{}
if (Test-Path "backend/app/main.py") {
    $raw = Get-Content backend/app/main.py -Raw
    if ($raw -match 'version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"') { $ver["backend"] = $Matches[1] }
}
if (Test-Path "frontend/package.json") {
    try { $ver["frontend"] = (Get-Content frontend/package.json -Raw | ConvertFrom-Json).version } catch {}
}
if ($ver.Count -eq 0) {
    Warn "no version markers found to compare"
} elseif (($ver.Values | Sort-Object -Unique).Count -eq 1) {
    $pairs = ($ver.GetEnumerator() | ForEach-Object { "$($_.Key):$($_.Value)" }) -join ","
    Ok "all versions equal ($pairs)"
} else {
    $pairs = ($ver.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join ","
    Fail "version mismatch: $pairs"
}

# --- 5. Tests / build / compose -----------------------------------------
if (-not $SkipTests) {
    # native tools write progress/warnings to stderr; PS5.1 would treat that as fatal
    $script:EapPrev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    Step "Backend tests (pytest)"
    Push-Location backend
    & ".\.venv\Scripts\python.exe" -m pytest tests -q -p no:cacheprovider 2>&1 | Select-Object -Last 1 | Write-Host
    if ($LASTEXITCODE -eq 0) { Ok "backend suite green" } else { Fail "backend tests failed" }
    Pop-Location

    Step "Frontend: vitest / tsc / lint / build"
    Push-Location frontend
    npm test -- --run 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Ok "vitest green" } else { Fail "vitest failed" }
    npx tsc -b 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Ok "tsc clean" } else { Fail "typecheck failed" }
    npm run lint 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Ok "lint clean" } else { Fail "lint failed" }
    npm run build 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Ok "vite build ok" } else { Fail "build failed" }
    Pop-Location

    Step "docker compose config"
    docker compose config --quiet 2>$null
    if ($LASTEXITCODE -eq 0) { Ok "dev compose valid" } else { Fail "docker-compose.yml invalid" }
    if (Test-Path ".env.docker") {
        docker compose --env-file .env.docker -f docker-compose.yml -f docker-compose.prod.yml config --quiet 2>$null
        if ($LASTEXITCODE -eq 0) { Ok "prod compose valid" } else { Fail "prod compose merge invalid" }
    } else {
        Warn ".env.docker missing locally - prod compose not validated (cp .env.docker.example .env.docker)"
    }
    $ErrorActionPreference = $script:EapPrev
} else {
    Step "Tests/build/compose"
    Warn "skipped by -SkipTests"
}

# --- Verdict --------------------------------------------------------------
Write-Host ""
Write-Host ("=" * 60)
if ($script:Failures.Count -gt 0) {
    Write-Host "RED: NOT READY - $($script:Failures.Count) blocker(s):" -ForegroundColor Red
    $script:Failures | ForEach-Object { Write-Host "   - $_" -ForegroundColor Red }
    exit 1
}
Write-Host "GREEN: READY FOR GITHUB" -ForegroundColor Green
if ($script:Warnings.Count -gt 0) {
    Write-Host "YELLOW: $($script:Warnings.Count) warning(s) to eyeball:" -ForegroundColor Yellow
    $script:Warnings | ForEach-Object { Write-Host "   - $_" -ForegroundColor Yellow }
}
exit 0
