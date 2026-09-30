# -*- coding: utf-8 -*-
"""Lớp NỀN dùng chung: cấu hình, đường dẫn, tiện ích, mã phiên bản, danh mục dataset.

VÌ SAO GOM LẠI: `src/` từng có 19 module nằm phẳng cạnh 10 gói con, nên không ai nhìn ra module nào
thuộc việc gì. Nay mỗi nhóm là một gói, TÊN FILE GIỮ NGUYÊN - chuyển nhà chỉ đổi đường dẫn import,
không đổi một dòng logic nào.

`src/api/` là mặt tiền cho ô notebook: notebook chỉ import từ đó, nên chuyển nhà bên trong `src/`
KHÔNG đụng tới notebook (`docs/00_workflow/10_template_notebook.md`).
"""
