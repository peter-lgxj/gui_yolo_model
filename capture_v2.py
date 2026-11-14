"""Collect screenshots for the input-box/search-icon detector.

Run from any directory, for example:
    python capture_v2.py

Press Enter after navigating to each new screen; type q to finish. Existing
screenshots and the original dataset are never overwritten.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import uuid

from PIL import Image


ROOT = Path(__file__).resolve().parent / "dataset_v2"
IMAGE_DIR = ROOT / "images" / "raw"
MANIFEST = ROOT / "capture_manifest.jsonl"


def adb(*args: str) -> bytes:
    result = subprocess.run(["adb", *args], capture_output=True, check=False)
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"ADB failed: {detail or result.returncode}")
    return result.stdout


def connected_device() -> str:
    lines = adb("devices").decode("utf-8", errors="replace").splitlines()[1:]
    devices = [line.split()[0] for line in lines if line.strip().endswith("\tdevice")]
    if len(devices) != 1:
        raise RuntimeError(f"Expected one authorized device; found {len(devices)}")
    return devices[0]


def capture(app: str, scenario: str, serial: str) -> Path:
    png = adb("-s", serial, "exec-out", "screencap", "-p")
    with Image.open(io.BytesIO(png)) as image:
        image.verify()
    with Image.open(io.BytesIO(png)) as image:
        width, height = image.size

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc)
    filename = f"{stamp:%Y%m%dT%H%M%S%fZ}_{uuid.uuid4().hex[:8]}.png"
    path = IMAGE_DIR / filename
    path.write_bytes(png)

    record = {
        "image": str(path.relative_to(ROOT)).replace("\\", "/"),
        "captured_at_utc": stamp.isoformat(),
        "device_id": hashlib.sha256(serial.encode("utf-8")).hexdigest()[:12],
        "width": width,
        "height": height,
        "app": app,
        "scenario": scenario,
    }
    with MANIFEST.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", default="", help="Optional app name")
    parser.add_argument("--scenario", default="", help="Optional screen description")
    args = parser.parse_args()
    for value in (args.app, args.scenario):
        if not value:
            continue
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", value):
            parser.error("--app and --scenario must use letters, digits, _ or -")

    serial = connected_device()
    print(f"Connected: {serial}. Screenshots go to {IMAGE_DIR}")
    print("Navigate to a screen, then press Enter to capture. Type q to finish.")
    while True:
        answer = input("capture> ").strip().lower()
        if answer == "q":
            break
        try:
            path = capture(args.app, args.scenario, serial)
            print(f"Saved {path.name}")
        except RuntimeError as exc:
            print(exc)
            break


if __name__ == "__main__":
    main()
