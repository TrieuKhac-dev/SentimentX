<#
.SYNOPSIS
  Cài JDK 17 (Temurin, bản LTS) cho dự án SentimentX — KHÔNG cần quyền admin.

.DESCRIPTION
  VÌ SAO CẦN JAVA?
  Bộ tách từ chính chủ của PhoBERT (RDRSegmenter, nằm trong VnCoreNLP) là một chương
  trình Java, được gọi từ Python qua pyjnius (JNI). pyjnius tìm JVM qua biến môi trường
  JDK_HOME rồi JAVA_HOME, và nếu không thấy thì báo lỗi "Unable to find JAVA_HOME".

  CÁCH CÀI NÀY: tải ZIP rồi giải nén vào thư mục NGƯỜI DÙNG
      %USERPROFILE%\.jdks\temurin-17
    - Không cần quyền admin, không ghi gì vào Program Files.
    - Gỡ ra chỉ cần xoá thư mục.
    - Mọi người trong dự án dùng đúng một dòng 17.0.x LTS nhờ API của Adoptium, nên số
      liệu đo được (số token, kết quả tách từ) so sánh được với nhau.

  CÁCH KHÁC (cần quyền admin, vẫn dùng được nhưng phải tự đặt JAVA_HOME):
      winget install EclipseAdoptium.Temurin.17.JDK

.PARAMETER Major
  Phiên bản Java LTS (mặc định 17). Chỉ dùng khi bản 17 gặp trục trặc với jar cũ:
  thử -Major 11 (xem docs/04_experiments/02_phase3_input.md §3).

.PARAMETER Force
  Cài lại kể cả khi đã có JDK dùng được.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\setup_java.ps1

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\setup_java.ps1 -Major 11 -Force
#>

[CmdletBinding()]
param(
    [int]$Major = 17,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
# Tắt thanh tiến trình của Invoke-WebRequest: nó in ra hàng trăm dòng "Writing web
# request..." làm thông báo thật khó đọc (và chậm hơn đáng kể trên PowerShell 5.1).
$ProgressPreference = 'SilentlyContinue'

# Console Windows mặc định dùng bảng mã cũ (cp850/cp1252) nên tiếng Việt in ra bị mất
# dấu. Ép về UTF-8 để thông báo đọc được.
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

# Windows PowerShell 5.1 mặc định có thể chưa bật TLS 1.2 -> mọi lệnh HTTPS đều lỗi.
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
} catch {
    Write-Verbose "Không đổi được SecurityProtocol: $_"
}

function Write-Step($message) { Write-Host "==> $message" -ForegroundColor Cyan }
function Write-Ok($message) { Write-Host "    $message" -ForegroundColor Green }

function Test-JdkHome([string]$path) {
    # Điều kiện "dùng được" là có jvm.dll: pyjnius cần đúng thư viện này, chỉ có file
    # java.exe trên PATH là chưa đủ.
    if ([string]::IsNullOrWhiteSpace($path)) { return $false }
    if (Test-Path (Join-Path $path 'bin\server\jvm.dll')) { return $true }
    return (Test-Path (Join-Path $path 'bin\java.exe'))
}

function Add-UserPath([string]$entry) {
    $current = [Environment]::GetEnvironmentVariable('Path', 'User')
    if ([string]::IsNullOrWhiteSpace($current)) { $current = '' }
    $parts = @($current.Split(';') | Where-Object { $_ -ne '' })
    if ($parts -contains $entry) { return $false }
    $updated = (@($parts) + $entry) -join ';'
    [Environment]::SetEnvironmentVariable('Path', $updated, 'User')
    return $true
}

$jdkRoot = Join-Path $env:USERPROFILE '.jdks'
$target = Join-Path $jdkRoot ("temurin-{0}" -f $Major)

Write-Step "Kiểm tra Java đang có trên máy"
$candidates = @(
    $env:JDK_HOME, $env:JAVA_HOME, $target,
    'C:\Program Files\Eclipse Adoptium',
    'C:\Program Files\Java',
    'C:\Program Files\Microsoft',
    (Join-Path $env:LOCALAPPDATA 'Programs\Eclipse Adoptium')
) | Where-Object { $_ }

$already = $null
foreach ($candidate in $candidates) {
    if (-not (Test-Path $candidate)) { continue }
    if (Test-JdkHome $candidate) { $already = $candidate; break }
    $child = Get-ChildItem $candidate -Directory -ErrorAction SilentlyContinue |
        Where-Object { Test-JdkHome $_.FullName } | Select-Object -First 1
    if ($child) { $already = $child.FullName; break }
}

if ($already -and -not $Force) {
    Write-Ok "Đã có JDK dùng được: $already"
    $target = $already
} else {
    Write-Step "Tải JDK $Major (Temurin, LTS) từ Adoptium"
    $api = "https://api.adoptium.net/v3/assets/latest/$Major/hotspot" +
           "?os=windows&architecture=x64&image_type=jdk"
    $assets = Invoke-RestMethod -Uri $api -UseBasicParsing
    if (-not $assets) { throw "Adoptium không trả về bản JDK $Major cho Windows x64." }

    $package = $assets[0].binary.package
    $release = $assets[0].release_name
    Write-Ok ("Bản sẽ cài: {0} ({1:N1} MB)" -f $release, ($package.size / 1MB))

    $zip = Join-Path $env:TEMP $package.name
    if (Test-Path $zip) { Remove-Item $zip -Force }
    Write-Step "Đang tải: $($package.link)"
    Invoke-WebRequest -Uri $package.link -OutFile $zip -UseBasicParsing

    # Nếu mạng bị chặn, file tải về là một trang HTML lỗi vài KB -> chặn ngay.
    $size = (Get-Item $zip).Length
    if ($size -lt 50MB) {
        throw ("File tải về chỉ có {0:N1} MB (đã lưu ở {1}) — có thể mạng bị chặn." -f `
            ($size / 1MB), $zip)
    }

    $hash = (Get-FileHash -Algorithm SHA256 -Path $zip).Hash.ToLower()
    if ($hash -ne $package.checksum.ToLower()) {
        throw "Mã băm không khớp (mong đợi $($package.checksum), nhận $hash). Dừng lại."
    }
    Write-Ok "Đã kiểm tra SHA256: $hash"

    $staging = Join-Path $env:TEMP ("sentimentx-jdk-" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $staging -Force | Out-Null
    Write-Step "Giải nén"
    Expand-Archive -Path $zip -DestinationPath $staging -Force
    $extracted = Get-ChildItem $staging -Directory | Select-Object -First 1
    if (-not $extracted) { throw "Trong file ZIP không có thư mục JDK nào." }

    if (Test-Path $target) { Remove-Item $target -Recurse -Force }
    New-Item -ItemType Directory -Path $jdkRoot -Force | Out-Null
    Move-Item -Path $extracted.FullName -Destination $target
    Remove-Item $staging -Recurse -Force
    Remove-Item $zip -Force
    Write-Ok "Đã cài vào: $target"
}

Write-Step "Đặt biến môi trường (mức người dùng, không cần admin)"
# Đặt cả JDK_HOME và JAVA_HOME: pyjnius kiểm tra JDK_HOME trước, còn nhiều công cụ Java
# khác chỉ đọc JAVA_HOME.
[Environment]::SetEnvironmentVariable('JDK_HOME', $target, 'User')
[Environment]::SetEnvironmentVariable('JAVA_HOME', $target, 'User')
$added = Add-UserPath (Join-Path $target 'bin')

# Đặt luôn cho tiến trình PowerShell đang chạy, để kiểm tra được ngay bên dưới.
$env:JDK_HOME = $target
$env:JAVA_HOME = $target
$env:Path = "$(Join-Path $target 'bin');$env:Path"

Write-Ok "JDK_HOME  = $target"
Write-Ok "JAVA_HOME = $target"
if ($added) { Write-Ok "Đã thêm vào PATH (mức người dùng): $target\bin" }
else { Write-Ok "PATH đã có sẵn: $target\bin" }

Write-Step "Kiểm tra lại"
$javaExe = Join-Path $target 'bin\java.exe'
if (-not (Test-Path $javaExe)) { throw "Không thấy $javaExe — cài đặt không thành công." }
& $javaExe -version
Write-Ok ("jvm.dll có mặt: " + (Test-Path (Join-Path $target 'bin\server\jvm.dll')))

Write-Host ""
Write-Host "Xong. Bước tiếp theo (tải model tách từ chính chủ):" -ForegroundColor Cyan
Write-Host "    powershell -ExecutionPolicy Bypass -File scripts\setup_vncorenlp.ps1"
Write-Host "Cửa sổ terminal đang mở chưa thấy JAVA_HOME mới, nhưng dự án tự tìm JDK trong"
Write-Host "%USERPROFILE%\.jdks nên chạy được ngay, không cần mở lại terminal."
