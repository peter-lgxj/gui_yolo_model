"""Validate raw v2 screenshots and YOLO labels before training or merging work."""

from collections import Counter
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent / "dataset_v2"
IMAGES = ROOT / "images" / "raw"
LABELS = ROOT / "labels" / "raw"
REVIEWED = ROOT / "labels" / "reviewed"
EXTENSIONS = {".png", ".jpg", ".jpeg"}


def main() -> None:
    images = sorted(p for p in IMAGES.iterdir() if p.suffix.lower() in EXTENSIONS)
    errors = []
    classes = Counter()
    if len({p.stem for p in images}) != len(images):
        errors.append("Image stems are not unique")
    image_stems = {p.stem for p in images}
    for image in images:
        label = LABELS / f"{image.stem}.txt"
        try:
            with Image.open(image) as opened:
                opened.verify()
        except Exception as exc:
            errors.append(f"{image.name}: invalid image ({exc})")
        if not label.exists():
            errors.append(f"{image.name}: missing label")
            continue
        for number, line in enumerate(label.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            fields = line.split()
            try:
                if len(fields) != 5 or fields[0] not in {"0", "1"}:
                    raise ValueError("expected class 0/1 and four coordinates")
                x, y, w, h = map(float, fields[1:])
                if not all(0 <= value <= 1 for value in (x, y, w, h)) or w <= 0 or h <= 0:
                    raise ValueError("coordinates must be normalized and box size positive")
                tolerance = 1e-5  # six-decimal YOLO labels can round an edge just beyond 1
                if not (w / 2 - tolerance <= x <= 1 - w / 2 + tolerance and
                        h / 2 - tolerance <= y <= 1 - h / 2 + tolerance):
                    raise ValueError("box extends beyond the image")
                classes[fields[0]] += 1
            except ValueError as exc:
                errors.append(f"{label.name}:{number}: {exc}")
    for label in LABELS.glob("*.txt"):
        if label.stem not in image_stems:
            errors.append(f"{label.name}: no matching image")
    print(f"images={len(images)} reviewed={sum((REVIEWED / p.stem).exists() for p in images)} "
          f"input_boxes={classes['0']} search_icons={classes['1']} errors={len(errors)}")
    if errors:
        for error in errors[:20]:
            print(error)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
