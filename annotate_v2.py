"""Label input fields and search icons as two YOLO classes.

Copy screenshots into dataset_v2/images/raw, then run this script.
Drag a box around each relevant target. Save an empty label for a screen
with no relevant target. Labels are written to dataset_v2/labels/raw.
"""

import argparse
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageTk


ROOT = Path(__file__).resolve().parent / "dataset_v2"
IMAGE_DIR = ROOT / "images" / "raw"
LABEL_DIR = ROOT / "labels" / "raw"
REVIEWED_DIR = ROOT / "labels" / "reviewed"
EXTENSIONS = {".png", ".jpg", ".jpeg"}
CLASS_NAMES = {0: "input_box", 1: "search_icon"}
CLASS_COLORS = {0: "#00e676", 1: "#ffb300"}


class Annotator:
    def __init__(self, root: tk.Tk, images: list[Path], start_index: int = 0):
        self.root = root
        self.images = images
        self.index = start_index
        self.boxes: list[tuple[int, float, float, float, float]] = []
        self.selected_class = tk.IntVar(value=0)
        self.start: tuple[int, int] | None = None
        self.dirty = False
        self.scale = 1.0
        self.image_size = (1, 1)

        root.title("UI annotation — input boxes and search icons")
        root.geometry("1100x850")
        bar = tk.Frame(root)
        bar.pack(fill=tk.X, padx=8, pady=6)
        self.status = tk.Label(bar, anchor="w")
        self.status.pack(side=tk.LEFT, fill=tk.X, expand=True)
        for class_id, name in CLASS_NAMES.items():
            tk.Radiobutton(bar, text=f"{class_id+1}: {name}", variable=self.selected_class,
                           value=class_id).pack(side=tk.LEFT, padx=3)
        for title, command in [
            ("Previous (P)", self.previous),
            ("Undo (Z)", self.undo),
            ("Clear", self.clear),
            ("Save (S)", self.save),
            ("Save & Next (Enter)", self.save_and_next),
            ("Next (N)", self.next),
        ]:
            tk.Button(bar, text=title, command=command).pack(side=tk.LEFT, padx=2)
        tk.Label(
            root,
            text="Select 1=input box or 2=search icon, then drag around each target. "
                 "Save an empty label when neither is present.",
        ).pack(anchor="w", padx=8)
        self.canvas = tk.Canvas(root, width=1060, height=750, bg="#222", cursor="crosshair")
        self.canvas.pack(padx=8, pady=8)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.remove_at)
        for key, command in [("s", self.save), ("n", self.next),
                             ("p", self.previous), ("z", self.undo)]:
            root.bind(key, lambda event, fn=command: fn())
        root.bind("1", lambda event: self.selected_class.set(0))
        root.bind("2", lambda event: self.selected_class.set(1))
        root.bind("<Return>", lambda event: self.save_and_next())
        self.load()

    def label_path(self) -> Path:
        return LABEL_DIR / f"{self.images[self.index].stem}.txt"

    def load(self) -> None:
        path = self.images[self.index]
        with Image.open(path) as opened:
            image = opened.convert("RGB")
        width, height = image.size
        self.image_size = (width, height)
        self.scale = min(1060 / width, 750 / height)
        resized = image.resize((round(width * self.scale), round(height * self.scale)), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(resized)
        self.boxes = []
        self.dirty = False
        label = self.label_path()
        if label.exists():
            for line in label.read_text(encoding="utf-8").splitlines():
                cls, cx, cy, bw, bh = line.split()
                class_id = int(cls)
                if class_id not in CLASS_NAMES:
                    raise ValueError(f"Unexpected class in {label}: {cls}")
                cx, cy, bw, bh = map(float, (cx, cy, bw, bh))
                self.boxes.append((class_id, (cx-bw/2)*width, (cy-bh/2)*height,
                                   (cx+bw/2)*width, (cy+bh/2)*height))
        state = "reviewed" if (REVIEWED_DIR / path.stem).exists() else "needs review"
        self.status.config(text=f"{self.index+1}/{len(self.images)}  {path.name}  "
                                f"{width}×{height}  {state}")
        self.draw()

    def draw(self, preview=None) -> None:
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        for class_id, x1, y1, x2, y2 in self.boxes:
            self.canvas.create_rectangle(x1*self.scale, y1*self.scale,
                                         x2*self.scale, y2*self.scale,
                                         outline=CLASS_COLORS[class_id], width=2)
            self.canvas.create_text(x1*self.scale+3, y1*self.scale+3,
                                    text=CLASS_NAMES[class_id], anchor=tk.NW,
                                    fill=CLASS_COLORS[class_id])
        if preview:
            self.canvas.create_rectangle(*preview,
                                         outline=CLASS_COLORS[self.selected_class.get()], width=2)

    def on_press(self, event) -> None:
        self.start = (event.x, event.y)

    def on_drag(self, event) -> None:
        if self.start:
            self.draw((*self.start, event.x, event.y))

    def on_release(self, event) -> None:
        if not self.start:
            return
        sx, sy = self.start
        self.start = None
        width, height = self.image_size
        x1, x2 = sorted((max(0, min(width, sx/self.scale)),
                         max(0, min(width, event.x/self.scale))))
        y1, y2 = sorted((max(0, min(height, sy/self.scale)),
                         max(0, min(height, event.y/self.scale))))
        if x2-x1 >= 4 and y2-y1 >= 4:
            self.boxes.append((self.selected_class.get(), x1, y1, x2, y2))
            self.dirty = True
        self.draw()

    def remove_at(self, event) -> None:
        x, y = event.x / self.scale, event.y / self.scale
        for index in range(len(self.boxes)-1, -1, -1):
            _, x1, y1, x2, y2 = self.boxes[index]
            if x1 <= x <= x2 and y1 <= y <= y2:
                self.boxes.pop(index)
                self.dirty = True
                self.draw()
                return

    def undo(self) -> None:
        if self.boxes:
            self.boxes.pop()
            self.dirty = True
            self.draw()

    def clear(self) -> None:
        self.boxes.clear()
        self.dirty = True
        self.draw()

    def save(self) -> None:
        LABEL_DIR.mkdir(parents=True, exist_ok=True)
        REVIEWED_DIR.mkdir(parents=True, exist_ok=True)
        width, height = self.image_size
        lines = []
        for class_id, x1, y1, x2, y2 in self.boxes:
            cx, cy = (x1+x2)/2/width, (y1+y2)/2/height
            bw, bh = (x2-x1)/width, (y2-y1)/height
            lines.append(f"{class_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
        self.label_path().write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        (REVIEWED_DIR / self.images[self.index].stem).touch()
        self.dirty = False
        self.status.config(text=self.status.cget("text").replace("needs review", "reviewed"))

    def save_and_next(self) -> None:
        self.save()
        if self.index < len(self.images)-1:
            self.index += 1
            self.load()

    def may_leave(self) -> bool:
        if not self.dirty:
            return True
        answer = messagebox.askyesnocancel("Unsaved edits", "Save changes before leaving this image?")
        if answer is None:
            return False
        if answer:
            self.save()
        return True

    def next(self) -> None:
        if self.index < len(self.images)-1 and self.may_leave():
            self.index += 1
            self.load()

    def previous(self) -> None:
        if self.index > 0 and self.may_leave():
            self.index -= 1
            self.load()


def main() -> None:
    parser = argparse.ArgumentParser(description="Review input boxes and label search icons")
    parser.add_argument("--start", type=int, default=1,
                        help="First image in sorted order (1-based, inclusive)")
    parser.add_argument("--end", type=int, default=None,
                        help="Last image in sorted order (1-based, inclusive)")
    args = parser.parse_args()
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    images = sorted(path for path in IMAGE_DIR.iterdir() if path.suffix.lower() in EXTENSIONS)
    if not images:
        root = tk.Tk()
        messagebox.showinfo("No screenshots", f"Copy screenshots into:\n{IMAGE_DIR}")
        root.destroy()
        return
    end = args.end if args.end is not None else len(images)
    if args.start < 1 or end < args.start or end > len(images):
        parser.error(f"Expected 1 <= --start <= --end <= {len(images)}")
    images = images[args.start - 1:end]
    print(f"Assigned images {args.start}-{end}; {len(images)} images")
    root = tk.Tk()
    stems = [path.stem for path in images]
    if len(stems) != len(set(stems)):
        messagebox.showerror("Duplicate names", "Images with the same stem would share a label file.")
        root.destroy()
        return
    first_unreviewed = next(
        (index for index, path in enumerate(images)
         if not (REVIEWED_DIR / path.stem).exists()),
        0,
    )
    Annotator(root, images, start_index=first_unreviewed)
    root.mainloop()


if __name__ == "__main__":
    main()
