# annotate.py
import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw

IMAGE_DIR = "dataset/images/all"
LABEL_DIR = "dataset/labels/all"
os.makedirs(LABEL_DIR, exist_ok=True)

class Annotator:
    def __init__(self, root):
        self.root = root
        self.root.title("输入框标注工具")

        # 加载图片列表
        self.images = sorted([
            f for f in os.listdir(IMAGE_DIR) if f.endswith(".png")
        ])
        self.index = 0
        self.boxes = []       # 当前图片的所有框 [(x1,y1,x2,y2), ...]
        self.click_points = []  # 当前正在画的框的点击点

        self.orig_w = 1
        self.orig_h = 1
        self.scale = 1.0

        self._build_ui()
        self._load_image()

    # ------------------------------------------------------------------ #
    #  UI 布局
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        # 顶部状态栏
        top = tk.Frame(self.root)
        top.pack(fill=tk.X, padx=8, pady=4)

        self.status_var = tk.StringVar()
        tk.Label(top, textvariable=self.status_var, anchor="w").pack(side=tk.LEFT)

        btn_frame = tk.Frame(top)
        btn_frame.pack(side=tk.RIGHT)
        tk.Button(btn_frame, text="◀ 上一张", command=self.prev_image, width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="下一张 ▶", command=self.next_image, width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="撤销框", command=self.undo_box, width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="清空框", command=self.clear_boxes, width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="💾 保存", command=self.save_label, width=8,
                  bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=2)

        # 操作提示
        hint = tk.Label(self.root,
                        text="操作：点击输入框左上角 → 再点击右下角 完成一个框 | 快捷键：S=保存  N=下一张  P=上一张  Z=撤销",
                        fg="gray")
        hint.pack()

        # 画布
        self.canvas = tk.Canvas(self.root, cursor="crosshair", bg="#222")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)

        # 键盘快捷键
        self.root.bind("<s>", lambda e: self.save_label())
        self.root.bind("<n>", lambda e: self.next_image())
        self.root.bind("<p>", lambda e: self.prev_image())
        self.root.bind("<z>", lambda e: self.undo_box())

        # 底部框列表
        bottom = tk.Frame(self.root)
        bottom.pack(fill=tk.X, padx=8, pady=4)
        tk.Label(bottom, text="已标注的框：").pack(side=tk.LEFT)
        self.box_list_var = tk.StringVar()
        tk.Label(bottom, textvariable=self.box_list_var, fg="#2196F3").pack(side=tk.LEFT)

    # ------------------------------------------------------------------ #
    #  图片加载
    # ------------------------------------------------------------------ #
    def _load_image(self):
        self.click_points = []
        fname = self.images[self.index]
        path = os.path.join(IMAGE_DIR, fname)

        img = Image.open(path).convert("RGB")
        self.orig_w, self.orig_h = img.size

        # 自适应缩放到屏幕
        self.root.update()
        max_w = self.canvas.winfo_width() or 900
        max_h = self.canvas.winfo_height() or 700
        self.scale = min(max_w / self.orig_w, max_h / self.orig_h, 1.0)
        disp_w = int(self.orig_w * self.scale)
        disp_h = int(self.orig_h * self.scale)

        self.disp_img = img.resize((disp_w, disp_h), Image.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(self.disp_img)

        # 加载已有标注
        label_path = os.path.join(LABEL_DIR, fname.replace(".png", ".txt"))
        self.boxes = []
        if os.path.exists(label_path):
            with open(label_path) as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 5:
                        _, cx, cy, bw, bh = map(float, parts)
                        x1 = (cx - bw / 2) * self.orig_w
                        y1 = (cy - bh / 2) * self.orig_h
                        x2 = (cx + bw / 2) * self.orig_w
                        y2 = (cy + bh / 2) * self.orig_h
                        self.boxes.append((x1, y1, x2, y2))

        # 判断是否已标注
        labeled = os.path.exists(label_path)
        label_str = "✅ 已标注" if labeled else "⬜ 未标注"

        self.status_var.set(
            f"[{self.index + 1}/{len(self.images)}]  {fname}  {label_str}  |  "
            f"原始尺寸: {self.orig_w}×{self.orig_h}"
        )
        self._redraw()

    # ------------------------------------------------------------------ #
    #  绘制
    # ------------------------------------------------------------------ #
    def _redraw(self, mouse_x=None, mouse_y=None):
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)

        s = self.scale

        # 画已完成的框（绿色）
        for i, (x1, y1, x2, y2) in enumerate(self.boxes):
            self.canvas.create_rectangle(
                x1 * s, y1 * s, x2 * s, y2 * s,
                outline="#4CAF50", width=2
            )
            self.canvas.create_text(
                x1 * s + 4, y1 * s + 4,
                text=f"#{i+1}", fill="#4CAF50", anchor=tk.NW, font=("Arial", 10, "bold")
            )

        # 画第一个点（蓝色圆点）
        if self.click_points:
            px, py = self.click_points[0]
            self.canvas.create_oval(
                px * s - 5, py * s - 5,
                px * s + 5, py * s + 5,
                fill="#2196F3", outline="white", width=1
            )
            # 如果鼠标在移动，画预览框（虚线橙色）
            if mouse_x is not None and mouse_y is not None:
                mx = mouse_x / s
                my = mouse_y / s
                self.canvas.create_rectangle(
                    px * s, py * s, mouse_x, mouse_y,
                    outline="#FF9800", width=2, dash=(6, 3)
                )

        # 更新框列表显示
        if self.boxes:
            info = "  ".join([
                f"#{i+1}({int(x1)},{int(y1)},{int(x2)},{int(y2)})"
                for i, (x1, y1, x2, y2) in enumerate(self.boxes)
            ])
            self.box_list_var.set(info)
        else:
            self.box_list_var.set("无")

    # ------------------------------------------------------------------ #
    #  鼠标事件
    # ------------------------------------------------------------------ #
    def on_click(self, event):
        # 转换为原始坐标
        orig_x = event.x / self.scale
        orig_y = event.y / self.scale

        self.click_points.append((orig_x, orig_y))

        if len(self.click_points) == 2:
            # 两点都有了，生成框
            x1 = min(self.click_points[0][0], self.click_points[1][0])
            y1 = min(self.click_points[0][1], self.click_points[1][1])
            x2 = max(self.click_points[0][0], self.click_points[1][0])
            y2 = max(self.click_points[0][1], self.click_points[1][1])

            # 过滤太小的框（误点）
            if (x2 - x1) > 10 and (y2 - y1) > 5:
                self.boxes.append((x1, y1, x2, y2))
                print(f"新增框：({int(x1)}, {int(y1)}, {int(x2)}, {int(y2)})")
            else:
                print("框太小，忽略")

            self.click_points = []
            self._redraw()

    def on_mouse_move(self, event):
        self._redraw(mouse_x=event.x, mouse_y=event.y)

    # ------------------------------------------------------------------ #
    #  按钮操作
    # ------------------------------------------------------------------ #
    def save_label(self):
        fname = self.images[self.index]
        label_path = os.path.join(LABEL_DIR, fname.replace(".png", ".txt"))

        with open(label_path, "w") as f:
            for (x1, y1, x2, y2) in self.boxes:
                # 转为 YOLO 格式（归一化中心坐标）
                cx = (x1 + x2) / 2 / self.orig_w
                cy = (y1 + y2) / 2 / self.orig_h
                bw = (x2 - x1) / self.orig_w
                bh = (y2 - y1) / self.orig_h
                f.write(f"0 {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n")

        print(f"已保存：{label_path}（{len(self.boxes)} 个框）")
        self.status_var.set(
            self.status_var.get().replace("⬜ 未标注", "✅ 已标注")
        )
        # 自动跳下一张
        self.next_image()

    def undo_box(self):
        if self.click_points:
            self.click_points = []
        elif self.boxes:
            self.boxes.pop()
        self._redraw()

    def clear_boxes(self):
        self.boxes = []
        self.click_points = []
        self._redraw()

    def next_image(self):
        if self.index < len(self.images) - 1:
            self.index += 1
            self._load_image()

    def prev_image(self):
        if self.index > 0:
            self.index -= 1
            self._load_image()


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x800")
    root.title("输入框标注工具")
    app = Annotator(root)
    root.mainloop()