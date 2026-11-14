# test_detector.py
from ultralytics import YOLO
from PIL import Image, ImageDraw
from pathlib import Path
import subprocess
import time

MODEL_PATH = str(Path(__file__).resolve().parent / "runs/detect/runs/input_box5/weights/best.pt")

def detect_input_box(image_path: str, conf=0.5) -> list[dict]:
    """检测截图中的输入框，返回中心坐标列表"""
    model = YOLO(MODEL_PATH)
    results = model(image_path, conf=conf, verbose=False)
    boxes = []
    img = Image.open(image_path)
    w, h = img.size
    for box in results[0].boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)
        conf_val = box.conf[0].item()
        boxes.append({
            "center": (cx, cy),
            "bbox": (int(x1), int(y1), int(x2), int(y2)),
            "confidence": round(conf_val, 3),
            "center_ratio": (round(cx / w, 4), round(cy / h, 4))
        })
    return boxes

def visualize(image_path: str, boxes: list, save_path="detected.png"):
    """画出检测框"""
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    for b in boxes:
        x1, y1, x2, y2 = b["bbox"]
        cx, cy = b["center"]
        draw.rectangle([x1, y1, x2, y2], outline="red", width=3)
        draw.ellipse([cx-6, cy-6, cx+6, cy+6], fill="red")
        draw.text((x1, y1 - 20), f"{b['confidence']:.2f}", fill="red")
    img.save(save_path)
    print(f"可视化保存：{save_path}")

if __name__ == "__main__":
    # 截一张当前手机屏幕
    print("截图中...")
    subprocess.run(["adb", "exec-out", "screencap", "-p"],
                   stdout=open("test_screen.png", "wb"))
    time.sleep(0.5)

    # 检测
    boxes = detect_input_box("test_screen.png")
    print(f"\n检测到 {len(boxes)} 个输入框：")
    for i, b in enumerate(boxes):
        print(f"  #{i+1} 中心像素:{b['center']}  比例:{b['center_ratio']}  置信度:{b['confidence']}")

    # 可视化
    visualize("test_screen.png", boxes)
    print("\n请查看 detected.png 确认检测框是否准确")
    