# Instala llama.cpp (CPU, Windows) e o modelo Q4_K_M em %USERPROFILE%\.llm. Idempotente.
# Precisa de ~7 GB livres em disco (modelo 5,63 GB + binários).
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$home_llm = Join-Path $env:USERPROFILE '.llm'
$bin = Join-Path $home_llm 'bin'
$models = Join-Path $home_llm 'models'
New-Item -ItemType Directory -Force -Path $bin, $models | Out-Null

$drive = Get-PSDrive -Name ($env:USERPROFILE.Substring(0, 1))
Write-Host ("Espaço livre: {0:N1} GB (necessário ~7 GB)" -f ($drive.Free / 1GB))

# Binário: a release "latest" pode não ter binários; pega a primeira das últimas 10 que tenha o asset.
if (Get-ChildItem -Path $bin -Recurse -Filter 'llama-server.exe' -ErrorAction SilentlyContinue) {
    Write-Host 'llama-server.exe já existe; pulando.'
} else {
    $releases = Invoke-RestMethod -Uri 'https://api.github.com/repos/ggml-org/llama.cpp/releases?per_page=10' -Headers @{ 'User-Agent' = 'llm-local' }
    $asset = $null
    foreach ($r in $releases) {
        $asset = $r.assets | Where-Object { $_.name -match '^llama-b\d+-bin-win-cpu-x64\.zip$' } | Select-Object -First 1
        if ($asset) { break }
    }
    if (-not $asset) { throw 'Nenhuma release recente com llama-bNNN-bin-win-cpu-x64.zip.' }
    $zip = Join-Path $env:TEMP $asset.name
    Write-Host "Baixando $($asset.name)..."
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zip
    Expand-Archive -Path $zip -DestinationPath $bin -Force
    Remove-Item $zip
}

$gguf = Join-Path $models 'DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic.i1-Q4_K_M.gguf'
$url = 'https://huggingface.co/mradermacher/DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic-i1-GGUF/resolve/main/DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic.i1-Q4_K_M.gguf'
# Download em .part (retomável com -C -); só vira .gguf quando completo.
if (Test-Path $gguf) {
    Write-Host 'Modelo já existe; pulando.'
} else {
    Write-Host 'Baixando modelo (5,63 GB; retomável se interromper)...'
    curl.exe -fL -C - -o "$gguf.part" $url
    if ($LASTEXITCODE -ne 0) { throw 'Falha no download do modelo; rode o script de novo para retomar.' }
    Move-Item "$gguf.part" $gguf
}
Write-Host 'Pronto. Teste com: llm status'
