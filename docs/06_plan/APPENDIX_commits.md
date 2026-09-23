# Phụ lục — Bảng commit

> Đọc file này khi: cần đặt commit message cho một việc nhỏ.
> Liên quan: `docs/00_workflow/05_git_commits.md`

## Quy ước

- Tiếng Anh, thể mệnh lệnh, dạng `type(scope): subject`, tiêu đề không quá 72 ký tự.
- Một commit là một việc nhỏ; sau commit dự án vẫn phải chạy được.
- Cần giải thích "vì sao" thì thêm phần body, cách tiêu đề một dòng trống.

## Type

| Type | Dùng khi |
|---|---|
| `feat` | thêm khả năng mới |
| `fix` | sửa lỗi |
| `refactor` | đổi cấu trúc code, không đổi hành vi |
| `test` | thêm hoặc sửa test |
| `docs` | tài liệu, chú thích, mẫu env |
| `chore` | việc lặt vặt: cấu trúc, phụ thuộc, cấu hình git |
| `ci` | thay đổi CI |

## Scope thường dùng

`repo`, `git`, `env`, `config`, `paths`, `datasets`, `versioning`, `experiments`, `labels`,
`preprocessing`, `evaluation`, `tracking`, `mlflow`, `resume`, `templates`, `notebook`,
`preflight`, `scripts`, `ci`, `docs`, `data`, `assets`

## Danh sách commit theo phase

| Phase | Commit |
|---|---|
| P0 | `chore(repo): scaffold refactored project tree` |
| P0 | `chore(assets): move shared plotly asset into data/assets` |
| P0 | `chore(git): ignore data by extension and keep folder placeholders` |
| P0 | `docs(env): add env templates for local and colab` |
| P0 | `chore: initial import of refactored project` |
| P1 | `feat(config): add central paths config` |
| P1 | `feat(paths): add paths module with env overrides` |
| P1 | `feat(runtime): add colab detection and env loading` |
| P1 | `refactor(config): route all paths through paths module` |
| P1 | `refactor(datasets): derive raw dir from paths` |
| P1 | `test(paths): cover resolution and env overrides` |
| P2 | `refactor(config): split pipeline config into versioned files` |
| P2 | `refactor(config): split dataset config into per-version files` |
| P2 | `feat(versioning): build data version id from ds pl and src segments` |
| P2 | `feat(versioning): guard immutable versioned configs` |
| P2 | `refactor(cli): require explicit version in runners` |
| P2 | `test(versioning): cover id and guard` |
| P3 | `feat(config): add shared experiment configs` |
| P3 | `feat(experiments): merge config layers with per-key source tracking` |
| P3 | `feat(experiments): hash merged config and merged prompt` |
| P3 | `feat(experiments): validate roles single dataset and leakage` |
| P3 | `feat(experiments): derive required paths` |
| P3 | `feat(experiments): add duplicate guard` |
| P3 | `test(experiments): cover merge overrides and validation` |
| P4 | `feat(labels): add label space registry` |
| P4 | `feat(preprocessing): project labels from task config` |
| P4 | `feat(evaluation): add scorers registry` |
| P4 | `feat(runlog): write run log and error file only on failure` |
| P4 | `feat(tracking): add trackers registry` |
| P4 | `feat(tracking): write run metadata with attempts and provenance` |
| P4 | `feat(mlflow): configure dagshub remote and smoke test` |
| P4 | `feat(resume): chunk predictions and resume by sample` |
| P4 | `test(evaluation): add metric tests` |
| P5 | `feat(repo): fetch and verify pinned commit` |
| P5 | `feat(scripts): add pin script writing repo url sha and exp dir` |
| P5 | `feat(templates): add experiment and prompt templates` |
| P5 | `feat(notebook): add first experiment notebook` |
| P5 | `feat(preflight): check paths device and drive` |
| P5 | `feat(scripts): add new experiment scaffolder` |
| P6 | `feat(scripts): generate registry model input and metrics matrix reports` |
| P6 | `feat(ci): add repository checks script` |
| P6 | `ci: add github actions workflow for experiment branch` |
| P6 | `chore(deps): add ci colab and base requirements` |
| P6 | `docs(workflow): add workflow rules ci terms commits and conventions` |
| P6 | `docs(config): add configuration reference` |
| P6 | `docs(experiments): add metrics and reference publication pages` |
| P7 | `feat(data): rebuild dataset version from raw` |
| P7 | `feat(data): regenerate eda and pipeline reports` |
| P7 | `feat(experiments): run baseline prompt experiments` |
| P7 | `docs(experiments): record baseline results against reference` |
