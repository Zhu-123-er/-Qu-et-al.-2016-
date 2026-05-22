# 复现 Qu et al. (2016) 日降水分级方法：长江中游典型城市降水强度结构变化分析

## 1. 项目简介

本项目是 D2RS 课程作业的可复现研究项目。项目复现 Qu et al. (2016) 在 *Daily Precipitation Changes over Large River Basins in China, 1960–2013* 中使用的核心方法：

1. 按固定阈值对逐日降水进行强度分级；
2. 统计不同强度等级的年度降水量、降水日数及其占比；
3. 使用 Mann-Kendall 检验识别趋势显著性；
4. 使用 Theil-Sen 斜率估计趋势幅度，并换算为每 10 年变化量。

本项目没有复现原文的全部研究对象和全部数据处理流程。原文使用中国气象站点数据并分析中国十大流域；本课程项目为了保证数据公开和代码可复现，使用 Open-Meteo Historical Weather API 获取典型城市点位逐日降水数据，并将原文方法应用到长江中游典型城市。

## 2. 复现对象

复现文章：

> Qu, B.; Lv, A.; Jia, S.; Zhu, W. (2016). Daily Precipitation Changes over Large River Basins in China, 1960–2013. *Water*, 8(5), 185. https://doi.org/10.3390/w8050185

原文方法中的日降水分级为：

| 等级 | 日降水量阈值 |
|---|---:|
| Light precipitation | 0.1 ≤ P < 10 mm/day |
| Moderate precipitation | 10 ≤ P < 25 mm/day |
| Heavy precipitation | 25 ≤ P < 50 mm/day |
| Extreme precipitation | P ≥ 50 mm/day |

说明：原文将 P < 10 mm/day 作为 light precipitation。本项目在年度统计时同时保留 dry/trace 天数，并将 light precipitation 明确处理为 0.1 ≤ P < 10 mm/day，以避免把无雨日计入降水事件。

## 3. 研究区与城市

本项目选择长江中游及相关湖区、干流沿岸典型城市：

- 武汉 Wuhan
- 宜昌 Yichang
- 荆州 Jingzhou
- 长沙 Changsha
- 岳阳 Yueyang
- 南昌 Nanchang
- 九江 Jiujiang

城市经纬度保存在 `data/city_locations.csv`。

## 4. 数据来源

逐日降水数据来自 Open-Meteo Historical Weather API。

- API endpoint: `https://archive-api.open-meteo.com/v1/archive`
- Daily variable: `precipitation_sum`
- Time range: 2000-01-01 to 2024-12-31
- Timezone: Asia/Shanghai

## 5. 仓库结构

```text
Qu2016-precip-reproduction-middle-yangtze/
│
├── README.md
├── requirements.txt
├── environment.yml
├── references.bib
├── report.qmd
├── run_project.bat
├── run_demo.bat
├── run_project.sh
├── run_demo.sh
│
├── data/
│   ├── city_locations.csv
│   ├── raw/
│   └── processed/
│
├── scripts/
│   ├── 00_run_all.py
│   ├── 01_download_data.py
│   ├── 02_preprocess.py
│   ├── 03_analysis.py
│   ├── 04_visualization.py
│   └── 05_check_outputs.py
│
└── outputs/
    ├── figures/
    └── tables/
```

## 6. 一键运行方法

### Windows：真实数据运行

双击：

```text
run_project.bat
```

该脚本会自动创建 `.venv` 虚拟环境、安装依赖、下载真实 Open-Meteo 数据并运行完整分析流程。

### Windows：离线演示运行

双击：

```text
run_demo.bat
```

该脚本不访问网络，会生成一份可复现的模拟逐日降水数据，用于检查代码是否能在新电脑上完整跑通。

### macOS / Linux

```bash
bash run_project.sh      # 真实数据
bash run_demo.sh         # 离线演示数据
```

## 7. 手动运行方法

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS / Linux:

```bash
source .venv/bin/activate
```

安装依赖：

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

运行真实数据流程：

```bash
python scripts/00_run_all.py --force-download
```

运行离线演示流程：

```bash
python scripts/00_run_all.py --demo
```

渲染 Quarto 报告：

```bash
quarto render report.qmd
```

如果没有安装 Quarto，也可以直接查看 `outputs/figures/` 和 `outputs/tables/` 中的结果。

## 8. 输出文件

运行后生成：

```text
data/raw/city_daily_precip_2000_2024.csv
data/processed/city_annual_precip_intensity_indices.csv
outputs/tables/city_summary_statistics.csv
outputs/tables/city_mk_theilsen_trends.csv
outputs/tables/city_intensity_composition.csv
outputs/figures/fig1_city_map.png
outputs/figures/fig2_annual_precip_trend.png
outputs/figures/fig3_intensity_composition.png
outputs/figures/fig4_extreme_ratio_heatmap.png
outputs/figures/fig5_trend_slope_by_city.png
outputs/figures/fig6_method_workflow.png
```

## 9. 小组成员贡献

| 成员 | 主要任务 | 建议提交文件 |
|---|---|---|
| 祝佳琦 | 数据下载与城市点位整理 | `data/city_locations.csv`, `scripts/01_download_data.py` |
| 祝佳琦 | 降水分级与年度指标计算 | `scripts/02_preprocess.py` |
| 祝佳琦 | Mann-Kendall 和 Theil-Sen 趋势分析 | `scripts/03_analysis.py` |
| 祝佳琦 | 可视化、README 和 Quarto 报告 | `scripts/04_visualization.py`, `README.md`, `report.qmd` |


## 10. 本项目复现范围与局限性

本项目复现的是 Qu et al. (2016) 的核心分析思想和主要统计方法，而不是完全复刻原文所有数据和结论。

已复现：

- 固定阈值日降水强度分级；
- 不同强度等级降水量和占比统计；
- Mann-Kendall 趋势显著性检验；
- Theil-Sen 趋势斜率估计；
- 趋势斜率换算为每 10 年变化量。

