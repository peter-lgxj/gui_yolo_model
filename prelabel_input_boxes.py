"""Prelabel input boxes with the existing one-class YOLO model.

Existing input-box annotations are kept. Existing search-icon annotations are
always kept. Every generated label still needs visual review in annotate_v2.py.
"""

import argparse
from pathlib import Path

from ultralytics import YOLO


ROOT = Path(__file__).resolve().parent
IMAGES = ROOT / "dataset_v2" / "images" / "raw"
LABELS = ROOT / "dataset_v2" / "labels" / "raw"
REVIEWED = ROOT / "dataset_v2" / "labels" / "reviewed"
WEIGHTS = ROOT / "runs" / "detect" / "runs" / "input_box5" / "weights" / "best.pt"
EXTENSIONS = {".png", ".jpg", ".jpeg"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--conf", type=float, default=0.4,
                        help="Minimum confidence for input-box proposals (default: 0.4)")
    parser.add_argument("--limit", type=int, default=0,
                        help="Process only this many images, for a pilot run")
    args = parser.parse_args()
    if not 0 < args.conf <= 1 or args.limit < 0:
        parser.error("--conf must be in (0, 1] and --limit must be nonnegative")
    if not WEIGHTS.is_file():
        parser.error(f"Model weights not found: {WEIGHTS}")

    images = sorted(p for p in IMAGES.iterdir() if p.suffix.lower() in EXTENSIONS)
    stems = [p.stem for p in images]
    if len(stems) != len(set(stems)):
        parser.error("Images with duplicate stems would share a label file")
    if args.limit:
        images = images[:args.limit]
    LABELS.mkdir(parents=True, exist_ok=True)
    model = YOLO(str(WEIGHTS))

    created = added = preserved = proposals = empty = 0
    for index, image in enumerate(images, 1):
        label = LABELS / f"{image.stem}.txt"
        existing = label.read_text(encoding="utf-8").splitlines() if label.exists() else []
        classes = [line.split()[0] for line in existing if line.strip()]
        if any(cls not in {"0", "1"} for cls in classes):
            raise ValueError(f"Unexpected class in {label}")
        # Any existing input-box label, including a manually reviewed negative
        # (empty label), takes precedence over model predictions.
        if "0" in classes or (label.exists() and not existing) or (REVIEWED / image.stem).exists():
            preserved += 1
            continue

        result = model.predict(source=str(image), imgsz=640,
                               conf=args.conf, verbose=False)[0]
        generated = []
        for box in result.boxes:
            cx, cy, width, height = box.xywhn[0].tolist()
            generated.append(f"0 {cx:.6f} {cy:.6f} {width:.6f} {height:.6f}")
        if not generated:
            empty += 1
        proposals += len(generated)
        lines = existing + generated
        label.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        if existing:
            added += 1
        else:
            created += 1
        if index % 25 == 0:
            print(f"Processed {index}/{len(images)} images", flush=True)

    print(f"Done: {len(images)} images; {created} new labels; {added} labels extended; "
          f"{preserved} preserved; {proposals} input-box proposals; "
          f"{empty} images with no proposal.")
    print("Open annotate_v2.py to review input boxes and add search icons.")


if __name__ == "__main__":
    main()
