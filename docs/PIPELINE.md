# Pipeline

当前骨架包含 9 个阶段：

1. `stage_0_collect.py`
2. `stage_1_normalize.py`
3. `stage_2_extract.py`
4. `stage_3_validate_structure.py`
5. `stage_4_cluster.py`
6. `stage_5_insight.py`
7. `stage_6_report.py`
8. `stage_7_visualize.py`
9. `stage_8_validate_final.py`

每个阶段统一暴露 `run(date, config)` 接口，并将结果写入约定目录。
