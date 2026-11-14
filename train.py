from ultralytics import YOLO

if __name__ == '__main__':
    model = YOLO("yolo11n.pt")

    model.train(
        data="dataset/data.yaml",
        epochs=100,
        imgsz=640,
        batch=16,
        device=0,
        project="runs",
        name="input_box",
        patience=15,
        workers=0,      # Windows 上设为 0 最稳定
        hsv_h=0.01,
        hsv_s=0.3,
        hsv_v=0.3,
        fliplr=0.0,
        flipud=0.0,
    )

    print("\n训练完成！模型保存在 runs/detect/input_box/weights/best.pt")