"""Create reproducible train/val splits from dataset_v2 raw images and labels."""

from pathlib import Path
import random
import shutil


ROOT = Path(__file__).resolve().parent / "dataset_v2"
IMAGES = ROOT / "images" / "raw"
LABELS = ROOT / "labels" / "raw"
EXTENSIONS = {".png", ".jpg", ".jpeg"}


def has_search_icon(label: Path) -> bool:
    return any(line.split()[0] == "1" for line in label.read_text(encoding="utf-8").splitlines()
               if line.strip())


def partition(images: list[Path], rng: random.Random) -> tuple[list[Path], list[Path]]:
    rng.shuffle(images)
    if len(images) < 2:
        return images, []
    val_count = max(1, round(len(images) * 0.2))
    return images[val_count:], images[:val_count]


def main() -> None:
    images = sorted(p for p in IMAGES.iterdir() if p.suffix.lower() in EXTENSIONS)
    if not images:
        raise RuntimeError(f"No images in {IMAGES}")
    labels = {p.stem: LABELS / f"{p.stem}.txt" for p in images}
    missing = [p.name for p in images if not labels[p.stem].exists()]
    if missing:
        raise RuntimeError(f"Missing labels for {len(missing)} images: {missing[:5]}")
    if len(labels) != len(images):
        raise RuntimeError("Image stems must be unique across extensions")

    search = [p for p in images if has_search_icon(labels[p.stem])]
    other = [p for p in images if p not in search]
    rng = random.Random(42)
    search_train, search_val = partition(search, rng)
    other_train, other_val = partition(other, rng)

    for split, group in (("train", search_train + other_train),
                         ("val", search_val + other_val)):
        image_dir = ROOT / "images" / split
        label_dir = ROOT / "labels" / split
        image_dir.mkdir(parents=True, exist_ok=True)
        label_dir.mkdir(parents=True, exist_ok=True)
        for folder, suffixes in ((image_dir, EXTENSIONS), (label_dir, {".txt"})):
            for old in folder.iterdir():
                if old.is_file() and old.suffix.lower() in suffixes:
                    old.unlink()
        for image in group:
            shutil.copy2(image, image_dir / image.name)
            shutil.copy2(labels[image.stem], label_dir / labels[image.stem].name)
        print(f"{split}: {len(group)} images, {sum(p in search for p in group)} with search_icon")


if __name__ == "__main__":
    main()
