# start_local_access.ps1

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "   AI Resume Interviewer - Local Access Setup      " -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# 1. Check for ngrok
if (-not (Test-Path ".\ngrok.exe")) {
    Write-Error "ngrok.exe not found in current directory!"
    exit 1
}

# 2. Stop existing ngrok (to prevent conflict)
Get-Process ngrok -ErrorAction SilentlyContinue | Stop-Process -Force

# 3. Create/Overwrite ngrok config for Port 3000
$ngrokConfigFileContent = @"
version: "2"
tunnels:
  frontend:
    addr: 3000
    proto: http
"@
Set-Content -Path "ngrok-tunnels.yml" -Value $ngrokConfigFileContent

# 4. Start ngrok
Write-Host "Starting ngrok tunnel for Frontend (Port 3000)..." -ForegroundColor Green
# Try to find default config for auth token
$defaultConfig = "$env:LOCALAPPDATA\ngrok\ngrok.yml"
if (-not (Test-Path $defaultConfig)) {
    $defaultConfig = "$env:USERPROFILE\.ngrok2\ngrok.yml"
}

$argsList = "start --all --config=`"$defaultConfig`" --config=.\ngrok-tunnels.yml --log=stdout"
if (-not (Test-Path $defaultConfig)) {
    Write-Warning "Default ngrok config not found. Authtoken might be missing."
    $argsList = "start --all --config=.\ngrok-tunnels.yml --log=stdout"
}

$ngrokProcess = Start-Process -FilePath ".\ngrok.exe" -ArgumentList $argsList -RedirectStandardOutput "ngrok.log" -RedirectStandardError "ngrok.err" -PassThru -WindowStyle Minimized

# 5. Wait and Fetch URL
Write-Host "Waiting for tunnel..."
Start-Sleep -Seconds 5

try {
    $tunnelsResponse = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop
}
catch {
    Write-Error "Failed to query ngrok API. Check ngrok.err."
    exit 1
}

$publicUrl = ""
foreach ($tunnel in $tunnelsResponse.tunnels) {
    if ($tunnel.config.addr -match "3000") {
        $publicUrl = $tunnel.public_url
        break
    }
}

if (-not $publicUrl) {
    Write-Error "Could not find frontend tunnel!"
    exit 1
}

Write-Host "---------------------------------------------------"
Write-Host "Public URL : $publicUrl" -ForegroundColor Magenta
Write-Host "---------------------------------------------------"

# 6. Update .env
$envPath = ".env"
$envContent = Get-Content -Path $envPath -Raw

function Upsert-EnvVar {
    param($content, $key, $value)
    $pattern = "(?m)^$key=.*$"
    $newLine = "$key=$value"
    if ($content -match $pattern) {
        return $content -replace $pattern, $newLine
    } else {
        return $content + "`n$newLine"
    }
}

$envContent = Upsert-EnvVar -content $envContent -key "FRONTEND_URL" -value $publicUrl
$envContent = Upsert-EnvVar -content $envContent -key "NEXT_PUBLIC_API_URL" -value $publicUrl
# Add to CORS
$corsValue = "http://localhost:3000,$publicUrl"
$envContent = Upsert-EnvVar -content $envContent -key "CORS_ORIGINS" -value $corsValue

Set-Content -Path $envPath -Value $envContent
Write-Host "Updated .env configuration." -ForegroundColor Green

Write-Host "`nIMPORTANT NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. STOP your currently running 'npm run dev' and 'uvicorn' terminals."
Write-Host "2. RESTART them to pick up the new .env changes."
Write-Host "3. Open $publicUrl/candidate?... on your device."
Write-Host "4. READ PRESENTATION_GUIDE.md for verification steps!" -ForegroundColor Cyan
Start-Process "PRESENTATION_GUIDE.md"
