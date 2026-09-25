# Phụ lục - Bảng commit

> Đọc file này khi: cần đặt commit message cho một task nhỏ.
> Liên quan: `docs/00_workflow/05_git_commits.md`

## Quy ước

- Tiếng Anh, thể mệnh lệnh, dạng `type(scope): subject`, tiêu đề không quá 72 ký tự.
- Một commit là một task nhỏ; sau commit dự án vẫn phải chạy được.
- Cần giải thích "vì sao" thì thêm phần body, cách tiêu đề một dòng trống.

## Type

| Type       | Dùng khi                                        |
| ---------- | ----------------------------------------------- |
| `feat`     | thêm khả năng mới                               |
| `fix`      | sửa lỗi                                         |
| `refactor` | đổi cấu trúc code, không đổi hành vi            |
| `test`     | thêm hoặc sửa test                              |
| `docs`     | tài liệu, chú thích, mẫu env                    |
| `chore`    | việc lặt vặt: cấu trúc, phụ thuộc, cấu hình git |
| `ci`       | thay đổi CI                                     |

## Scope thường dùng

`repo`, `git`, `env`, `config`, `paths`, `datasets`, `versioning`, `experiments`, `labels`,
`preprocessing`, `evaluation`, `tracking`, `mlflow`, `resume`, `templates`, `notebook`,
`preflight`, `scripts`, `reports`, `cli`, `ci`, `deps`, `docs`, `data`, `assets`

Scope mới thì thêm vào danh sách này ngay khi dùng lần đầu, để bảng dưới và lịch sử git không nói
hai chuyện khác nhau. Bảng commit theo giai đoạn ở dưới là dự kiến; commit THỰC TẾ nằm ở mục cuối
file, vì chạy thật thì phát sinh việc không có trong dự kiến.

## Danh sách commit theo giai đoạn

| Giai đoạn | Commit                                                                    |
| ----- | ------------------------------------------------------------------------- |
| P0    | `chore(repo): scaffold refactored project tree`                           |
| P0    | `chore(assets): move shared plotly asset into data/assets`                |
| P0    | `chore(git): ignore data by extension and keep folder placeholders`       |
| P0    | `docs(env): add env templates for local and colab`                        |
| P0    | `chore: initial import of refactored project`                             |
| P1    | `feat(config): add central paths config`                                  |
| P1    | `feat(paths): add paths module with env overrides`                        |
| P1    | `feat(runtime): add colab detection and env loading`                      |
| P1    | `refactor(config): route all paths through paths module`                  |
| P1    | `refactor(datasets): derive raw dir from paths`                           |
| P1    | `test(paths): cover resolution and env overrides`                         |
| P2    | `refactor(config): split pipeline config into versioned files`            |
| P2    | `refactor(config): split dataset config into per-version files`           |
| P2    | `feat(versioning): build data version id from ds pl and src segments`     |
| P2    | `feat(versioning): guard immutable versioned configs`                     |
| P2    | `refactor(cli): require explicit version in runners`                      |
| P2    | `test(versioning): cover id and guard`                                    |
| P3    | `feat(config): add shared experiment configs`                             |
| P3    | `feat(experiments): merge config layers with per-key source tracking`     |
| P3    | `feat(experiments): hash merged config and merged prompt`                 |
| P3    | `feat(experiments): validate roles single dataset and leakage`            |
| P3    | `feat(experiments): derive required paths`                                |
| P3    | `feat(experiments): add duplicate guard`                                  |
| P3    | `test(experiments): cover merge overrides and validation`                 |
| P4    | `feat(labels): add label space registry`                                  |
| P4    | `feat(preprocessing): project labels from task config`                    |
| P4    | `feat(evaluation): add scorers registry`                                  |
| P4    | `feat(runlog): write run log and error file only on failure`              |
| P4    | `feat(tracking): add trackers registry`                                   |
| P4    | `feat(tracking): write run metadata with attempts and provenance`         |
| P4    | `feat(mlflow): configure dagshub remote and smoke test`                   |
| P4    | `feat(resume): chunk predictions and resume by sample`                    |
| P4    | `test(evaluation): add metric tests`                                      |
| P5    | `feat(repo): fetch and verify pinned commit`                              |
| P5    | `feat(scripts): add pin script writing repo url sha and exp dir`          |
| P5    | `feat(templates): add experiment and prompt templates`                    |
| P5    | `feat(notebook): add first experiment notebook`                           |
| P5    | `feat(preflight): check paths device and drive`                           |
| P5    | `feat(scripts): add new experiment scaffolder`                            |
| P6    | `feat(scripts): generate registry model input and metrics matrix reports` |
| P6    | `feat(ci): add repository checks script`                                  |
| P6    | `ci: add github actions workflow for experiment branch`                   |
| P6    | `chore(deps): add ci colab and base requirements`                         |
| P6    | `docs(workflow): add workflow rules ci terms commits and conventions`     |
| P6    | `docs(config): add configuration reference`                               |
| P6    | `docs(experiments): add metrics and reference publication pages`          |
| P7    | `feat(data): rebuild dataset version from raw`                            |
| P7    | `feat(data): regenerate eda and pipeline reports`                         |
| P7    | `feat(experiments): run baseline prompt experiments`                      |
| P7    | `docs(experiments): record baseline results against reference`            |

## Commit THỰC TẾ của đợt P4/P5/P6 (đọc khi cần tra nguồn gốc một thay đổi)

Chạy thật thì phát sinh việc không có trong bảng dự kiến ở trên (lỗi chỉ lộ ra khi chạy model hoặc
khi mở notebook trên Colab), nên commit thực tế không trùng tên. Ghi lại đây.

| Giai đoạn | Commit thực tế (mới nhất ở dưới) |
| --- | --- |
| P4/P5 | `refactor(evaluation): move the experiment loop into a library the notebook calls` |
| P5 | `fix(prompts): never derive the examples file from a prompt path` |
| P5 T6 | `feat(experiments): add scripts/new_experiment.py to scaffold an experiment` |
| P5 T4 | `feat(experiments): create exp001 - Qwen3-4B CoT prompt, scored on val` |
| P5 | `chore(experiments): pin commit fe180947 into the exp001 notebook` |
| P5 | `fix(preflight): a bad prompt path becomes a reported problem, not a crash` |
| P5 | `fix(evaluation): put an overridden model in the result folder name` |
| P4 | `docs(plan): record the real interrupt-resume run and close P4, tick P5 tasks` |
| P5 T3 | `fix(notebook): fetch the pinned commit before importing src` |
| P6 T1 | `feat(reports): generate registry model input and metrics matrix reports` |
| P6 T2 | `feat(ci): add repository checks script` |
| P6 | `fix(reports): keep metric matrix columns unique` |
| P6 | `fix(evaluation): sampling falls back to the model card, not to 1.0` (kèm phần truyền `root` cho các lệnh git của `checks`) |
| P6 | `fix(run): stash old results when running, not when planning` |
| P6 | `chore(ci): list the checks in one place, drop the one-sample smoke run` |
| P6 | `chore(ci): catch tracked scratch files in check 2, drop the one that slipped in` |
| P6 | `fix(checks): check 2 must not die when git cannot list files` |
| P5 | `chore(experiments): pin commit 8e79c0d into the exp001 notebook` |
| P7 T1 (sớm) | `fix(hashing): make file digests independent of line endings` |
| P7 T1 | `feat(preflight): report missing raw data first, with a runnable command` |
| P5 | `fix(notebooks): bootstrap must survive a second run, and stay in sync with the template` |
| P7 T1 | `chore(data): rebuild the dataset under the corrected version id` |
| P6 T4 | `chore(deps): add ci colab and base requirements` |
| P6 T5 | `docs(workflow): add the colab runbook` |
| P6 T4 | `feat(runtime): find the group's Drive folder by its marker, not its name` |
| P5 | `feat(notebook): do the whole Colab setup in the bootstrap cell` |
| P6 T5 | `docs(workflow): the colab runbook is now three steps` |
| P6 T5 | `docs(plan): sync the phase status table` |
| P6 T5 | `docs(workflow): the notebook does the colab setup itself` |
| P6 T5 | `docs(readme): bring the front page to the current layout` |
| P6 T3 | `test(ci): skip dataset tests where there is no data` |
| P6 T3 | `feat(ci): check documentation links` |
| P6 T3 | `ci: add github actions workflow for experiment branch` |
| P6 | `fix(scripts): the documented --title now fills notes` |
| P6 T5 | `docs(config): prompt paths resolve from the experiment folder first` |
| P7 T2 | `feat(data): regenerate eda and pipeline reports` |
| P7 T5 | `docs(plan): record the prepared handover package` |

Hai điều rút ra từ hai lần chạy notebook trên Colab, ghi lại vì cả hai chỉ lộ ra ở máy MỚI:

- Thứ tự trong ô bootstrap là chịu lực: kéo mã nguồn TRƯỚC khi `import src`, và kéo đúng commit đã
  ghim. Sau khi kéo xong còn phải xoá bộ nhớ đệm import của kernel (`sys.path_importer_cache`), vì
  câu trả lời "thư mục này không có gói `src`" đã bị nhớ từ lúc máy còn trống.
- Mọi phép băm nội dung file phải chuẩn hoá kiểu xuống dòng. Windows ghi CRLF, Colab ghi LF, và mã
  phiên bản dữ liệu hai máy đã lệch nhau vì đúng chuyện đó.

## Đợt sửa sau khi rà soát kế hoạch (25/09/2026)

Rà lại `docs/06_plan/` so với code, rồi sửa những chỗ lệch. Commit thực tế của đợt này:

| Việc | Commit |
| --- | --- |
| Bỏ file `mlflow.db` (kho dữ liệu của máy chủ MLflow chạy tại chỗ) khỏi git, thêm quy tắc bỏ qua | `chore(git): stop tracking the local mlflow store` |
| Test đường dẫn không còn phụ thuộc biến môi trường của máy đang chạy | `test(paths): keep the path tests independent of the shell overrides` |
| Giải đường dẫn prompt/ví dụ MỘT LẦN lúc nạp, và hỗ trợ ô nhớ `{system_prompt}` | `fix(prompts): read the prompt side files once, and support the system block` |
| Bảng tổng hợp `model_input` đọc đúng file số đo do `run_token_stats.py` ghi; tên file lấy từ `configs/paths.yaml` | `fix(reports): collect the token stats files into the model input table` |
| `run.log` có nhãn `[CONFIG]`; `run_meta.json` có `task`, `overrides`, `data.roles/rows/eval_lock`, `env.device`; mã run MLflow ở dòng `[TRACK]` | `feat(tracking): put the config in use and the device into the run record` |
| Sửa mâu thuẫn trong P4, task lặp trong P5, bảng scope; ghi việc chưa làm vào backlog | `docs(plan): fix the contradictions and record what was left undone` |
| Bỏ dải `print("=" * 70)` ở 7 cửa vào dòng lệnh | `style(cli): drop the printed banner dividers` |
| Ghim lại `exp001` vào bản code đã sửa (pin cũ không chạy được thí nghiệm này) | `chore(experiments): pin 5c99f38 so exp001 reads its prompt files` |
| Preflight báo thiếu `bitsandbytes` kể cả khi máy thiếu `torch` (đây là nguyên nhân CI đỏ) | `fix(preflight): name the missing pieces even when torch itself is missing` |
| Cây Drive trong tài liệu khớp gói bàn giao: thêm `README.md`, `notebooks/<model>/<method>/expNNN.ipynb`, `processing_log.json`, `raw_meta.yaml`, và cảnh báo hai khoá gốc trong `.env.colab` | `docs(workflow): the Drive tree is the one the package carries` |
| Ghi lại cây mới của gói bàn giao (16 file) và vì sao phải ghim lại | `docs(plan): record the handover layout` |
| Đọc tệp env chịu được BOM, và ghi tệp env gửi kèm bằng UTF-8 có BOM (chữ tiếng Việt trong tệp cũ đã bị hỏng do vòng `Get-Content`/`Set-Content` của PowerShell 5.1) | `fix(runtime): read env files tolerantly of a byte order mark` + `docs(workflow): the shipped env file carries a BOM, and say why` |
| Ghim lại `exp001` (bản code đọc env an toàn với BOM) | `chore(experiments): pin d9a705f so the handover reads its env file safely` |
| Kiểu số nạp model chọn theo máy (T4 không có bf16), và kiểu đã dùng được ghi lại | `fix(evaluation): pick the number type the GPU actually supports` |
| Preflight nói rõ torch là bản CPU hay bản CUDA khi không thấy GPU | `fix(preflight): name the torch build when no GPU is visible` |
| Bảng tra lỗi Colab thêm hai dòng: phiên CPU / torch bị cài đè, và T4 dùng fp16 | `docs(workflow): the colab error table now covers the no-gpu and T4 cases` |
| Giữ lượt chạy 4 mẫu lần hai, sau khi đổi kiểu số | `chore(experiments): keep the second four-sample run, now that the number type is recorded` |
| Ghim lại `exp001` để lượt chạy trên T4 dùng đúng kiểu số | `chore(experiments): pin 1ae179a so the T4 run picks the right number type` |
| Trang hướng dẫn chạy notebook trên máy cá nhân | `docs(workflow): add the page for running the notebook on a local machine` |
| Notebook gọi `plan()` mà không truyền `batch_size`, còn plan không lấy từ config: lượt chạy chết ở `range(0, n, None)` | `fix(run): a plan without a batch size reads it from the model config` |
| Ô chạy đọc `SENTIMENTX_MODEL` để dùng trọng số có sẵn trên máy | `feat(notebook): let a machine point at the weights it already has` |
| Giữ lượt chạy thứ ba, đi đúng đường của notebook (batch từ config, model từ biến môi trường) | `chore(experiments): keep the run made through the path the notebook uses` |
| Ghim lại `exp001` (bản code có sửa `batch_size`) | `chore(experiments): pin 6247e73 so the reader gets the batch size fix` |
| Chỉ nhận bf16 khi máy có hỗ trợ THẬT, không nhận bản giả lập phần mềm (T4 của Colab) | `fix(evaluation): ask for real bf16 support, not software emulation` |
| Khoá tập đánh giá ghi MỘT LẦN ngay khi tạo dữ liệu, vào `data/processed/<mã>/eval_lock.json` (bản v0 cũng có khoá) | `feat(versioning): write the evaluation lock next to the data` |
| Preflight kiểm `test.csv` theo khoá ghi cùng dữ liệu, không chỉ theo giá trị khai trong config | `fix(preflight): verify the test set against the lock stored with the data` |
| Tài liệu về chỗ đặt khoá: dataset config, luật 11, đầu ra pipeline, công bố tham chiếu, cây Drive | `docs(config): the evaluation lock lives with the data, from the first version` |
| CI cho phép `eval_lock.json` được git theo dõi (metadata, như `processing_log.json`) | `fix(checks): the evaluation lock is metadata, so CI must not flag it` |
| `repo.prepare()` không gỡ `origin` và không fetch `--depth 1` trên repo máy cá nhân (mất ref `origin/*`, repo thành nông) | `fix(repo): take the pinned commit without touching the developer's remotes` |
| Ghi lại hai việc của máy cá nhân: kernel cần `ipykernel`, và `git fetch origin` một lần để có `origin/experiment` | `docs(env): document the local Jupyter kernel and the one-time fetch` |
| `repo.prepare()` cập nhật ref `origin/<nhánh>` trước khi kết luận (ref trong máy cũ ngay sau khi push) | `fix(repo): refresh the branch ref before judging the pinned commit` |
| Ghim lại notebook exp001 (`75cbdb6`) và đính chính sha ghi sai trong chính commit ghim | `chore(experiments): pin 75cbdb6 into the exp001 notebook`, `docs(experiments): name the sha the pin actually wrote` |
