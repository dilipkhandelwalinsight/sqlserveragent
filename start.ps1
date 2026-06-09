# Enterprise SQL Server AI Agent — Launcher
# Run this script to start the Streamlit web UI

Set-Location $PSScriptRoot

# Install Python dependencies if needed
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found. Install Python 3.9+ and add to PATH." -ForegroundColor Red
    exit 1
}

Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
python -m pip install -r requirements.txt --quiet

Write-Host ""
Write-Host "🚀 Starting Enterprise SQL Server AI Agent..." -ForegroundColor Green
Write-Host "   Open your browser at: http://localhost:8501" -ForegroundColor Cyan
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

python -m streamlit run app.py `
    --server.port 8501 `
    --server.headless false `
    --browser.gatherUsageStats false `
    --theme.base dark `
    --theme.primaryColor "#1565c0" `
    --theme.backgroundColor "#0d1b2a" `
    --theme.secondaryBackgroundColor "#1e2d40" `
    --theme.textColor "#e0e0e0"
