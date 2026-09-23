<#
.SYNOPSIS
  Tải model tách từ chính chủ (VnCoreNLP/RDRSegmenter) cho PhoBERT — không dùng `wget`.

.DESCRIPTION
  VÌ SAO CÓ SCRIPT NÀY?
  Hàm `py_vncorenlp.download_model()` gọi `wget` qua `os.system`, mà Windows không có
  wget: nó sẽ không tải được gì rồi báo lỗi khó hiểu. Script này tải bằng PowerShell,
  kiểm tra kích thước từng file, và có thể chạy lại nhiều lần (file đã có thì bỏ qua).

  TẢI VỀ data/models/vncorenlp/:
      VnCoreNLP-1.2.jar                       chương trình Java của VnCoreNLP
      models/wordsegmenter/vi-vocab           từ điển của bộ tách từ
      models/wordsegmenter/wordsegmenter.rdr  model RDRSegmenter

  Chừng đó là đủ để tách từ. Các phần pos / ner / parse chỉ tải khi dùng -All.

.PARAMETER All
  Tải thêm model cho pos / ner / parse (không cần cho phép đo token, nhưng cần nếu sau
  này muốn gán nhãn từ loại / thực thể).

.PARAMETER Force
  Tải lại kể cả khi file đã có.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\setup_vncorenlp.ps1

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\setup_vncorenlp.ps1 -All -Force
#>

[CmdletBinding()]
param(
    [switch]$All,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
# Tắt thanh tiến trình của Invoke-WebRequest: nó in ra hàng trăm dòng "Writing web
# request..." làm thông báo thật khó đọc (và chậm hơn đáng kể trên PowerShell 5.1).
$ProgressPreference = 'SilentlyContinue'

# Console Windows mặc định dùng bảng mã cũ (cp850/cp1252) nên tiếng Việt in ra bị mất
# dấu. Ép về UTF-8 để thông báo đọc được.
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
} catch {
    Write-Verbose "Không đổi được SecurityProtocol: $_"
}

function Write-Step($message) { Write-Host "==> $message" -ForegroundColor Cyan }
function Write-Ok($message) { Write-Host "    $message" -ForegroundColor Green }

$repoRoot = Split-Path -Parent $PSScriptRoot
$modelDir = Join-Path $repoRoot 'data\models\vncorenlp'
$base = 'https://raw.githubusercontent.com/vncorenlp/VnCoreNLP/master'

# Mỗi dòng: đường dẫn trên repo + kích thước TỐI THIỂU. Kích thước dùng để phát hiện
# trường hợp tải về được một trang HTML lỗi vài KB mà tưởng là thành công; các mức dưới
# đây đặt theo kích thước THẬT của file (đã kiểm bằng Content-Length), không phải đoán.
$files = @(
    @{ Path = 'VnCoreNLP-1.2.jar';                       Min = 10MB },   # thật: ~27 MB
    @{ Path = 'models/wordsegmenter/vi-vocab';           Min = 100KB },  # thật: 526 KB
    @{ Path = 'models/wordsegmenter/wordsegmenter.rdr';  Min = 50KB }    # thật: 128 KB
)
if ($All) {
    $files += @(
        @{ Path = 'models/postagger/vi-tagger';           Min = 100KB },
        @{ Path = 'models/ner/vi-500brownclusters.xz';    Min = 100KB },
        @{ Path = 'models/ner/vi-ner.xz';                 Min = 100KB },
        @{ Path = 'models/ner/vi-pretrainedembeddings.xz'; Min = 10MB },
        @{ Path = 'models/dep/vi-dep.xz';                 Min = 100KB }
    )
}

function Test-JavaHome([string]$path) {
    # Điều kiện cần là jvm.dll (pyjnius nạp JVM qua thư viện này), không chỉ java.exe.
    # (Không đặt tên tham số là $home: đó là biến tự động chỉ-đọc của PowerShell.)
    if ([string]::IsNullOrWhiteSpace($path)) { return $false }
    return [bool](Test-Path (Join-Path $path 'bin\server\jvm.dll'))
}

Write-Step "Kiểm tra Java"
$jdk = $env:JAVA_HOME
if (-not (Test-JavaHome $jdk)) {
    # setup_java.ps1 cài JDK vào thư mục người dùng; nhánh này để chạy được ngay trong
    # phiên terminal đang mở (chưa đọc lại biến môi trường vừa đặt).
    $jdk = Join-Path $env:USERPROFILE '.jdks\temurin-17'
}
if (-not (Test-JavaHome $jdk)) {
    throw ("Chưa thấy JDK (cần có bin\server\jvm.dll). Chạy trước:`n" +
           "    powershell -ExecutionPolicy Bypass -File scripts\setup_java.ps1")
}
# Đặt cho tiến trình PowerShell này để pyjnius (chạy trong python bên dưới) tìm thấy.
$env:JAVA_HOME = $jdk
$env:JDK_HOME = $jdk
Write-Ok "JDK: $jdk"

Write-Step "Kiểm tra thư viện py-vncorenlp"
python -c "import py_vncorenlp" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Ok "Chưa có, đang cài bằng pip..."
    python -m pip install py-vncorenlp
    if ($LASTEXITCODE -ne 0) { throw "Cài py-vncorenlp thất bại." }
}
Write-Ok "Đã có py-vncorenlp"

New-Item -ItemType Directory -Path $modelDir -Force | Out-Null

foreach ($file in $files) {
    $destination = Join-Path $modelDir ($file.Path -replace '/', '\')
    Write-Step "Tải $($file.Path)"
    if ((Test-Path $destination) -and -not $Force) {
        Write-Ok "Đã có, bỏ qua: $destination"
        continue
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Invoke-WebRequest -Uri "$base/$($file.Path)" -OutFile $destination -UseBasicParsing

    $size = (Get-Item $destination).Length
    if ($size -lt $file.Min) {
        Remove-Item $destination -Force
        # Một chuỗi mẫu duy nhất cho -f: tránh lỗi thứ tự toán tử khi nối chuỗi.
        $message = "File {0} chỉ có {1:N0} bytes (mong đợi từ {2:N0} trở lên) — có " +
                   "thể mạng bị chặn. Kiểm tra kết nối rồi chạy lại."
        throw ($message -f $file.Path, $size, $file.Min)
    }
    Write-Ok ("{0:N0} bytes" -f $size)
}

Write-Step "Chạy thử tách từ (đúng cách dự án gọi)"
$smoke = Join-Path $env:TEMP 'sentimentx_smoke_segmenter.py'
@'
# -*- coding: utf-8 -*-
import json
import os
import sys

# Console Windows mặc định không phải UTF-8 -> in tiếng Việt sẽ lỗi UnicodeEncodeError.
# Đây cũng là việc mà mọi entrypoint của dự án đều làm.
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.getcwd())

from src.preprocessing.segmenters import vncorenlp

print(json.dumps(vncorenlp.info(), ensure_ascii=False, indent=2))
print("kết quả tách từ:", vncorenlp.segment("Son đẹp nhưng ship lâu"))
'@ | Set-Content -Path $smoke -Encoding UTF8
Push-Location $repoRoot
python $smoke
Pop-Location
Remove-Item $smoke -Force

Write-Host ""
Write-Host "Xong. Kiểm tra lại bằng:" -ForegroundColor Cyan
Write-Host "    python run_token_stats.py --list-segmenters"
Write-Host "    python run_token_stats.py --dataset cosmetics"
