# gui_yolo_model

通用手机 GUI 检测项目，目标类别为 `input_box`（0）和 `search_icon`（1）。`dataset_v2/` 是当前数据集；原单类别 `dataset/` 已移除。旧单类别权重仍保留，可用于输入框预标注，但**不能识别搜索图标**。

## 安装

```powershell
pip install -r requirements.txt
```

采集手机截图需要 Android Platform Tools、USB 调试和设备授权。标注界面还需要 Tkinter。

## 数据状态

当前 v2 数据包含 348 张截图和对应的 348 份标签，类别 0 有 280 个框，类别 1 有 6 个框。目前仅 1 张标记为人工复核，其他输入框标签主要来自旧模型预标注。**数据仍需逐张复核并补充搜索图标标注；上传不代表双类别模型已训练完成。** 详细规则见 [DATASET_V2.md](DATASET_V2.md)。

`dataset_v2/images/raw/`、`dataset_v2/labels/raw/` 和 `dataset_v2/labels/reviewed/` 是源数据。`images/train|val` 与 `labels/train|val` 由划分脚本生成，不提交到 Git。

组员启动标注的命令是 `python annotate_v2.py`；分段标注可用 `python annotate_v2.py --start 1 --end 116`。交付文件及完整分工示例见 [DATASET_V2.md](DATASET_V2.md#组员分工与交付)。

## 工作流

```powershell
# 连接手机采集，或将现有 PNG/JPG 截图放到 dataset_v2/images/raw/
python capture_v2.py

# 用旧的单类别权重补充输入框候选，不覆盖人工复核标签
python prelabel_input_boxes.py

# 人工检查输入框，补充搜索图标；允许无目标页面保存空标签
python annotate_v2.py

# 合并组员标签后检查图片、类别编号与坐标
python validate_dataset_v2.py

# 生成固定种子的训练/验证划分，保证有足够样本时两边都有搜索图标
python split_dataset.py

# 训练双类别模型（需 CUDA GPU；CPU 用户修改 train.py 中 device）
python train.py
```

`train.py` 读取 `dataset_v2/data.yaml`。划分脚本使用原始图像和标签，重新运行会重建生成的 train/val 文件。当前只有 6 个搜索图标框，训练结果不宜当作可用的通用搜索检测器。

## 现有权重

`runs/detect/runs/input_box5/weights/best.pt` 是原单类别 `input_box` 模型。`test_detector.py` 用它对当前手机截图做输入框推理；`yolo11n.pt` 和 `yolo26n.pt` 是保留的初始权重。真正接入 Phone Agent 的搜索图标检测需等待 v2 标注、训练和验证完成。
