# 通用 UI 目标检测数据（v2）

本轮训练一个通用检测模型，包含两个类别：`input_box`（类别编号 0）和 `search_icon`（类别编号 1）。模型在任意应用的截图上提出带类别的候选位置；智能体根据任务、截图及上下文决定点击哪一个。

## 采集

把任意应用的 PNG/JPG 截图放进 `dataset_v2/images/raw/`，文件名不可重复。也可以连接 Android 手机后运行 `python capture_v2.py`，在每个不同页面按 Enter 截图，输入 `q` 退出。`--app` 和 `--scenario` 只是可选记录项。

首批建议采 30～50 张，用来检查标注规则和模型是否能找到小图标；正式训练前再扩充。优先覆盖不同应用、页面布局、分辨率、亮暗主题和键盘弹出前后的状态。不要靠重复截取几乎相同的页面凑数量。使用测试内容，避免把私人聊天和邮件纳入数据集。

## 标注

旧模型可先通过 `prelabel_input_boxes.py` 自动生成 `input_box` 候选框。脚本只补输入框，不覆盖已有人手标签；在本机需使用装有 Ultralytics 的 Python 环境，例如 `D:\anaconda\envs\torch_gpu\python.exe prelabel_input_boxes.py`。已对当前 348 张图片运行过一次，新图片加入后可再次运行。

然后运行 `python annotate_v2.py`。标注界面会从第一张待检查图片开始。按 1 选择输入框或按 2 选择搜索图标，再在图上拖框。错误框可以右键删除。按 S 保存、Enter 保存并下一张、N 下一张、P 上一张、Z 撤销。标签保存到 `dataset_v2/labels/raw/`，检查进度保存在 `dataset_v2/labels/reviewed/`；没有目标的页面也要保存空标签。预标注只是候选，仍需检查是否漏框或误框。

- 对真正可输入文字的区域，标为 `input_box`，框住完整输入区域。
- 对能打开搜索界面的独立放大镜按钮，标为 `search_icon`，框住按钮的可点击区域。
- 如果放大镜位于可编辑的搜索输入框内部且只是装饰，则只把输入区域标为 `input_box`，不要给装饰图标另画框。
- 同屏有多个目标时全部标注；装饰性的放大镜或不可点击的图标不要标注。
- 不要标注发送、返回、关闭等其他控件。

训练前按设备和页面场景分组划分训练/验证/测试集，避免相邻截图泄漏到不同集合。最终同时检查目标检测结果与真实点击是否进入预期界面。

## 组员分工与交付

在克隆仓库并安装依赖后，从仓库根目录启动标注工具：

```powershell
cd gui_yolo_model
python annotate_v2.py
```

`--start`、`--end` 可按文件名排序后的图片序号限定范围，两个端点均包含。例如三人处理现有 348 张图时，可分别运行：

```powershell
python annotate_v2.py --start 1 --end 116
python annotate_v2.py --start 117 --end 232
python annotate_v2.py --start 233 --end 348
```

每张图检查完按 S 或 Enter 保存，包括无目标的空标签。现有仓库的截图文件名相同，组员交付自己负责范围的 `dataset_v2/labels/raw/<同名>.txt` 和 `dataset_v2/labels/reviewed/<同名无扩展名>` 即可，不必重复传截图。若新增截图，需同时交付 `dataset_v2/images/raw/` 中对应图片。合并时只覆盖各自分工范围的文件；所有人必须保留 `0=input_box`、`1=search_icon` 类别编号。
