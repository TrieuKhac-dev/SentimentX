# Tải trọng số Qwen3 về máy — dùng chung cho cả nhóm, KHÔNG commit (data/models/ nằm trong
# .gitignore: 8 GB thì không đưa vào git được, nhưng phải tải được CÙNG MỘT BẢN).
#
# Cách dùng:
#     powershell -ExecutionPolicy Bypass -File scripts\setup_qwen_model.ps1
#     powershell -ExecutionPolicy Bypass -File scripts\setup_qwen_model.ps1 -Model Qwen/Qwen3-0.6B
#
# VÌ SAO PHẢI CÓ SCRIPT NÀY (đã gặp thật trong lúc làm)
# ----------------------------------------------------
# 1. `hf download` từ huggingface.co ở máy này ĐỨNG ở ~95-116 MB rồi không tiến triển; dừng
#    tiến trình thì cache còn 0 GB (không tái sử dụng được). Một kết nối đơn chỉ ~1,3-1,9 MB/s.
# 2. Hai tiến trình tải chạy chồng nhau thì GIÀNH file khoá trong `.locks/` của hub, cả hai
#    đứng chờ nhau ("Still waiting to acquire lock ... elapsed 170s") mà không báo lỗi rõ.
# 3. Vòng lặp gọi curl TUẦN TỰ chỉ có MỘT kết nối -> đo được 0,06-0,5 MB/s; chia 8 khối chạy
#    song song thì được ~6-8 MB/s. Nên phải chạy song song thật (nhiều tiến trình).
# 4. `curl -I` (HEAD) tới ModelScope trả về RỖNG, nên nếu lấy kích thước file bằng HEAD thì
#    script tính ra 0 khối, KHÔNG tải gì mà cũng KHÔNG báo lỗi. Vì vậy kích thước lấy từ API
#    của HF (request nhỏ vẫn chạy được) và cuối cùng LUÔN kiểm lại kích thước đã nối.
#
# Kiểm tra sau khi tải: script in bảng kích thước từng file và báo OK/SAI.
param(
    [string]$Model = 'Qwen/Qwen3-4B-Instruct-2507',
    [string]$OutDir = '',
    [int]$ChunkMB = 300,
    [int]$Parallel = 6
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not $OutDir) { $OutDir = Join-Path $root ('data\models\' + ($Model -split '/')[-1]) }
$msBase = 'https://www.modelscope.cn/models/' + $Model + '/resolve/master'
$parts = Join-Path $OutDir '_parts'
New-Item -ItemType Directory -Force -Path $OutDir, $parts | Out-Null

Write-Host ('Tải {0} -> {1}' -f $Model, $OutDir)

# 1) Danh sách file + kích thước, lấy từ API của HF (request nhỏ; HEAD tới ModelScope trả rỗng)
$tree = curl.exe -sL -m 60 ("https://huggingface.co/api/models/{0}/tree/main?recursive=true" -f $Model) | ConvertFrom-Json
if (-not $tree) { throw "Không lấy được danh sách file từ API của HF cho $Model" }

$weights = @{}
foreach ($entry in $tree) {
    if ($entry.type -ne 'file') { continue }
    if ($entry.path -like '*.safetensors' -and $entry.path -notlike '*.index.json') {
        $weights[$entry.path] = [int64]$entry.size
    }
}
if ($weights.Count -eq 0) { throw "Không thấy file .safetensors nào cho $Model" }

# 2) File nhỏ (config + tokenizer + chat template)
#    LƯU Ý: xoá file tải về mà RỖNG. Repo không có `chat_template.jinja` thì curl tạo file
#    0 byte, và file rỗng đó CHE MẤT template hợp lệ trong `tokenizer_config.json` — tokenizer
#    sẽ không có template, prompt thành chuỗi rỗng, model sinh ra rác mà không báo lỗi gì.
foreach ($name in @('config.json', 'generation_config.json', 'tokenizer.json',
                    'tokenizer_config.json', 'vocab.json', 'merges.txt',
                    'chat_template.jinja', 'model.safetensors.index.json')) {
    $target = Join-Path $OutDir $name
    curl.exe -sL -m 300 -o $target "$msBase/$name"
    $size = (Get-Item $target -ErrorAction SilentlyContinue).Length
    if ($size -gt 0) {
        Write-Host ('  nho: {0} ({1} bytes)' -f $name, $size)
    } else {
        Remove-Item $target -Force -ErrorAction SilentlyContinue
        Write-Host ('  nho: {0} -> KHONG CO trong repo (da xoa file rong)' -f $name)
    }
}

# Kiểm tra chat template: phải có, nếu không thì prompt sẽ rỗng (xem ghi chú ở trên)
$jinja = Join-Path $OutDir 'chat_template.jinja'
$hasJinja = (Test-Path $jinja) -and ((Get-Item $jinja).Length -gt 0)
$hasStored = $false
$tokenizerConfig = Join-Path $OutDir 'tokenizer_config.json'
if (Test-Path $tokenizerConfig) {
    $hasStored = (Select-String -Path $tokenizerConfig -Pattern '"chat_template"' -SimpleMatch | Measure-Object).Count -gt 0
}
if (-not ($hasJinja -or $hasStored)) {
    Write-Host 'CANH BAO: khong thay chat template (chat_template.jinja hoac tokenizer_config.json)'
    Write-Host '         -> prompt se RONG va model sinh ra rac. Kiem tra lai ten model.'
}


# 3) Chia mỗi file trọng số thành các khối và tải SONG SONG.
#    Mỗi khối là một tiến trình riêng (Start-Process). HAI chi tiết quyết định thành/bại:
#      - gọi curl trong vòng lặp TUẦN TỰ chỉ cho MỘT kết nối (đo được 0,06-0,5 MB/s);
#      - `--speed-limit/--speed-time`: một kết nối ĐỨNG mà không có ngưỡng này sẽ chặn
#        worker tới `--max-time` (đã gặp: đứng 15 phút ở giữa các lô, tải không nhích mà
#        cũng không báo lỗi). Có ngưỡng thì kết nối chậm bị cắt sau 30 giây và tự nối tiếp.
$chunk = [int64]$ChunkMB * 1MB
$workerDir = Join-Path $env:TEMP ('sx_worker_' + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Force -Path $workerDir | Out-Null

foreach ($shard in $weights.Keys) {
    $total = $weights[$shard]
    $count = [Math]::Ceiling($total / $chunk)
    Write-Host ('  {0}: {1} khoi ({2:N0} bytes)' -f $shard, $count, $total)

    for ($i = 0; $i -lt $count; $i += $Parallel) {
        $running = @()
        for ($j = $i; $j -lt [Math]::Min($i + $Parallel, $count); $j++) {
            $start = [int64]$j * $chunk
            $end = [Math]::Min($start + $chunk - 1, $total - 1)
            $file = Join-Path $parts "$shard.$j"
            $worker = Join-Path $workerDir "khoi_$j.ps1"
            $script = @"
`$file = '$file'
`$expect = $($end - $start + 1)
for (`$try = 1; `$try -le 20; `$try++) {
    `$have = 0
    if (Test-Path `$file) { `$have = (Get-Item `$file).Length }
    if (`$have -ge `$expect) { break }
    `$lo = $start + `$have
    curl.exe -sL --max-time 600 --speed-limit 100000 --speed-time 30 --retry 2 -r "`$lo-$end" -o "`$file.part" "$msBase/$shard"
    if ((Test-Path "`$file.part") -and (Get-Item "`$file.part").Length -gt 0) {
        if (`$have -gt 0) {
            cmd /c copy /b "`$file"+"`$file.part" "`$file.tmp" > `$null 2>`$null
            Move-Item -Force "`$file.tmp" `$file
        } else {
            Move-Item -Force "`$file.part" `$file
        }
    }
    Remove-Item "`$file.part" -Force -ErrorAction SilentlyContinue
}
"@
            $script | Out-File -Encoding utf8 $worker
            $running += Start-Process -FilePath 'powershell.exe' `
                -ArgumentList '-ExecutionPolicy', 'Bypass', '-File', $worker `
                -WindowStyle Hidden -PassThru
        }
        $running | Wait-Process
        $got = 0
        for ($j = $i; $j -lt [Math]::Min($i + $Parallel, $count); $j++) {
            $got += (Get-Item (Join-Path $parts "$shard.$j") -ErrorAction SilentlyContinue).Length
        }
        Write-Host ('    lo {0}: {1:N1} MB' -f $i, ($got / 1MB))
    }
}
Remove-Item $workerDir -Recurse -Force -ErrorAction SilentlyContinue

# 4) Nối các khối thành file hoàn chỉnh
foreach ($shard in $weights.Keys) {
    $target = Join-Path $OutDir $shard
    $list = Get-ChildItem $parts -Filter "$shard.*" | Sort-Object { [int]($_.Name -split '\.')[-1] }
    if (-not $list) { throw "Không có khối nào cho $shard" }
    if (Test-Path $target) { Remove-Item $target -Force }
    cmd /c copy /b ($list.FullName -join '+') "$target" > $null 2>&1
}
Remove-Item $parts -Recurse -Force -ErrorAction SilentlyContinue

# 5) Kiểm tra kích thước — KHÔNG tin là đã xong chỉ vì script chạy hết
$problems = 0
Write-Host ''
Write-Host 'Kiểm tra kích thước:'
foreach ($shard in ($weights.Keys | Sort-Object)) {
    $got = (Get-Item (Join-Path $OutDir $shard) -ErrorAction SilentlyContinue).Length
    $ok = ($got -eq $weights[$shard])
    if (-not $ok) { $problems++ }
    $mark = 'SAI'
    if ($ok) { $mark = 'OK' }
    Write-Host ('  {0,-42} {1,15:N0} / {2,15:N0}  {3}' -f $shard, $got, $weights[$shard], $mark)
}

if ($problems -gt 0) {
    Write-Host ''
    Write-Host 'CÓ FILE SAI KÍCH THƯỚC — chạy lại script (nó nối tiếp từ chỗ đã có).'
    exit 1
}
Write-Host ''
Write-Host ('Xong. Nạp model bằng: python run_qwen_eval.py --model "{0}"' -f $OutDir)
