# gui_yolo_model

手机 GUI 目标检测项目：使用 Ultralytics YOLO 检测 Android 截图中的输入框，并提供截图采集、标注、数据划分、训练与推理脚本。

## 环境与安装

建议 Python 3.10 或更高版本。连接手机采集或推理需要安装 Android Platform Tools，将 `adb` 加入 PATH，并在手机上启用 USB 调试、完成设备授权。训练脚本默认使用 CUDA GPU（`device=0`）；使用 CPU 时请将其改为 `device="cpu"`。

```bash
git clone https://github.com/peter-lgxj/gui_yolo_model.git
cd gui_yolo_model
pip install -r requirements.txt
```

标注工具使用 Tkinter；若所用 Python 未附带 Tkinter，需另外安装。

## 原版输入框检测

从项目根目录运行：

```bash
# 采集手机截图
python collect_screenshots.py

# 标注输入框
python annotate.py

# 按 8:2 划分已标注数据
python split_dataset.py

# 训练单类别检测器
python train.py

# 连接手机，截图并使用现有权重检测
python test_detector.py
```

原始图片和标签分别放在 `dataset/images/all/` 与 `dataset/labels/all/`。类别为 `input_box`（编号 0），数据配置见 `dataset/data.yaml`。数据集截图和标签未上传，需要自行准备。

## 模型权重

- `yolo11n.pt`：训练脚本使用的初始权重。
- `yolo26n.pt`：目录中保留的另一份初始权重。
- `runs/detect/runs/input_box5/weights/best.pt`：已有的输入框检测权重，推理脚本默认使用它。
- `runs/detect/runs/input_box5/weights/last.pt`：该轮训练的最后一个检查点。

训练指标、曲线及参数文件保留在 `runs/`。包含原始手机截图的训练预览图未上传。训练后的输出目录以 Ultralytics 实际运行日志为准。

## v2 数据采集与标注

`capture_v2.py`、`annotate_v2.py` 和 `dataset_v2/data.yaml` 用于两个类别：`input_box`（0）和 `search_icon`（1）。详细规则见 [DATASET_V2.md](DATASET_V2.md)。现有训练权重来自原版单类别任务，不能据此视为已训练的 v2 双类别模型。

```bash
python capture_v2.py
python annotate_v2.py
```

原版 `train.py` 默认读取 `dataset/data.yaml`；训练 v2 需要先准备并划分数据，再修改相应数据配置路径。

## 与 Phone Agent 配合

将 `runs/detect/runs/input_box5/weights/best.pt` 复制到 Phone Agent 项目的 `models/input_box.pt`，供其输入框检测模块使用。

## 验证范围

上传前检查 Python 文件语法和上传文件清单，未重新训练模型或连接真实手机进行推理测试。
