# split_dataset.py
import os, shutil, random

IMAGE_DIR = "dataset/images/all"
LABEL_DIR = "dataset/labels/all"

images = [f for f in os.listdir(IMAGE_DIR) if f.endswith(".png")]

# 只保留有标注文件的图片
labeled = [f for f in images if os.path.exists(
    os.path.join(LABEL_DIR, f.replace(".png", ".txt"))
)]
print(f"有效标注图片：{len(labeled)} 张")

random.seed(42)
random.shuffle(labeled)
split = int(len(labeled) * 0.8)
train = labeled[:split]
val = labeled[split:]

for folder in [
    "dataset/images/train", "dataset/images/val",
    "dataset/labels/train", "dataset/labels/val"
]:
    os.makedirs(folder, exist_ok=True)

for f in train:
    shutil.copy(f"{IMAGE_DIR}/{f}", f"dataset/images/train/{f}")
    label = f.replace(".png", ".txt")
    shutil.copy(f"{LABEL_DIR}/{label}", f"dataset/labels/train/{label}")

for f in val:
    shutil.copy(f"{IMAGE_DIR}/{f}", f"dataset/images/val/{f}")
    label = f.replace(".png", ".txt")
    shutil.copy(f"{LABEL_DIR}/{label}", f"dataset/labels/val/{label}")

print(f"训练集：{len(train)} 张，验证集：{len(val)} 张")