# collect_screenshots.py
import subprocess
import os
import time

SAVE_DIR = "dataset/images/all"
os.makedirs(SAVE_DIR, exist_ok=True)

def screenshot(index):
    path = os.path.join(SAVE_DIR, f"screen_{index:04d}.png")
    subprocess.run(
        ["adb", "exec-out", "screencap", "-p"],
        stdout=open(path, "wb")
    )
    print(f"已保存：{path}")
    return path

print("按 S 截图，按 Q 退出")
print(f"保存目录：{SAVE_DIR}")
print("-" * 30)

# 用 pynput 监听键盘，不需要窗口焦点
from pynput import keyboard

index = len(os.listdir(SAVE_DIR))  # 从已有数量续编

def on_press(key):
    global index
    try:
        if key.char == 's':
            screenshot(index)
            index += 1
        elif key.char == 'q':
            print("退出")
            return False  # 停止监听
    except AttributeError:
        pass

with keyboard.Listener(on_press=on_press) as listener:
    listener.join()