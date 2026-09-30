# -*- coding: utf-8 -*-
"""MẶT TIỀN cho ô notebook: ô notebook CHỈ được import từ `src.api`.

VÌ SAO CÓ THƯ MỤC NÀY
Notebook ghim MỘT commit rồi chạy rất lâu sau đó, còn `src/` thì đổi chỗ liên tục. Nếu ô notebook
trỏ thẳng `from src.workflow import repo` thì mỗi lần chuyển nhà một file là phải sửa 12 notebook -
mà notebook đã ghim thì không sửa được nữa. Có mặt tiền thì chuyển nhà chỉ sửa file trong đây.

BA LUẬT (đều có test chặn ở `tests/api/test_api.py`)
1. Ô notebook chỉ import từ `src.api`, không import thẳng vào ruột `src/`.
2. File trong `src/api/` CHỈ re-export: docstring + import + `__all__`. Không viết logic ở đây.
3. Mã trong `src/` KHÔNG BAO GIỜ import `src.api` (chặn vòng import).

CHIA VÙNG
Mỗi vùng ứng với một nhóm của `src/`, nên chuyển nhà TRONG một nhóm chỉ sửa file vùng; chuyển nhà
KHÁC nhóm thì sửa file vùng + một dòng ở đây. Ô notebook KHÔNG cần biết tên vùng: nó vẫn viết
`from src.api import paths, repo, runtime` như trước.
"""

from src.api.core import config, dataset, paths, registry, runlog, utils, versioning  # noqa: F401
from src.api.experiments import (encoder_run, experiment_run, experiments,  # noqa: F401
                                 model_config, prompts)
from src.api.reporting import reports  # noqa: F401
from src.api.tracking import run_meta, tracking  # noqa: F401
from src.api.workflow import (bootstrap, checks, end_session, end_session_on_error,  # noqa: F401
                              notebooks, preflight, repo, resume, runtime)

__all__ = ["bootstrap", "checks", "config", "dataset", "encoder_run", "end_session",
           "end_session_on_error", "experiment_run", "experiments", "model_config", "notebooks",
           "paths", "preflight", "prompts", "registry", "repo", "reports", "resume", "run_meta",
           "runlog", "runtime", "tracking", "utils", "versioning"]

