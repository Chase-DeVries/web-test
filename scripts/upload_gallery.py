#!/usr/bin/env python3
"""Generate thumbnails for a folder of photos and upload a gallery to GCS.

The site's gallery convention is: full-size images live under `<folder>/` and
their thumbnails under `<folder>-thumbs/` in the bucket, sharing the same
filename. This script does both halves of that in one command:

    python scripts/upload_gallery.py ukrazy ~/Desktop/ukrazy_photos

  1. reads JPEGs from the source directory,
  2. writes 256px-longest-side thumbnails (EXIF-rotated) to a temp dir,
  3. uploads full-size -> gs://<bucket>/<folder>/ and
            thumbnails -> gs://<bucket>/<folder>-thumbs/.

Requires Pillow (`pip install Pillow`) and an authenticated `gcloud`.
Note: objects are served publicly via storage.googleapis.com, so the bucket must
grant public read at the bucket level (allUsers -> Storage Object Viewer).
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageOps

IMAGE_EXTS = {".jpg", ".jpeg"}


def generate_thumbnail(input_path: Path, output_path: Path, max_length: int = 256):
    """Write a thumbnail whose longest side is `max_length`, honoring EXIF
    orientation. Saved as JPEG so the gallery (which filters image/jpeg) shows it."""
    with Image.open(input_path) as img:
        img = ImageOps.exif_transpose(img)  # rotate per EXIF; no-op when EXIF is absent
        img.thumbnail((max_length, max_length))  # preserves aspect ratio
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(output_path, "JPEG", quality=85)


def run_upload(files, destination: str, dry_run: bool):
    """gcloud storage cp <files...> gs://bucket/prefix/ (trailing slash keeps names)."""
    cmd = ["gcloud", "storage", "cp", *[str(f) for f in files], destination]
    if dry_run:
        print("  DRY RUN:", " ".join(cmd[:4]), f"... ({len(files)} files) ", destination)
        return
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser(
        description="Generate thumbnails and upload a gallery to Google Cloud Storage.",
        epilog="example: python scripts/upload_gallery.py ukrazy ~/Desktop/ukrazy_photos",
    )
    ap.add_argument("folder", help="gallery name, e.g. 'ukrazy' "
                                   "(full-size -> <folder>/, thumbs -> <folder>-thumbs/)")
    ap.add_argument("source", help="local directory of full-size JPEG images")
    ap.add_argument("--bucket", default="chasedv-photos", help="GCS bucket (default: %(default)s)")
    ap.add_argument("--max-length", type=int, default=256,
                    help="thumbnail longest side in px (default: %(default)s)")
    ap.add_argument("--thumbs-dir", help="where to write thumbnails (default: a temp dir)")
    ap.add_argument("--no-upload", action="store_true",
                    help="only generate thumbnails; skip the GCS upload")
    ap.add_argument("--dry-run", action="store_true",
                    help="generate thumbnails but print the upload commands instead of running them")
    args = ap.parse_args()

    source = Path(args.source).expanduser()
    if not source.is_dir():
        sys.exit(f"source directory not found: {source}")

    images = sorted(p for p in source.iterdir()
                    if p.is_file() and p.suffix.lower() in IMAGE_EXTS)
    if not images:
        sys.exit(f"no JPEG images (.jpg/.jpeg) found in {source}")

    if args.thumbs_dir:
        thumbs_dir = Path(args.thumbs_dir).expanduser()
        thumbs_dir.mkdir(parents=True, exist_ok=True)
    else:
        thumbs_dir = Path(tempfile.mkdtemp(prefix=f"{args.folder}-thumbs-"))

    print(f"Generating {len(images)} thumbnails -> {thumbs_dir}")
    thumbs = []
    for p in images:
        out = thumbs_dir / p.name  # same filename so thumb<->full mapping holds
        try:
            generate_thumbnail(p, out, args.max_length)
            thumbs.append(out)
        except Exception as e:
            print(f"  skipped {p.name}: {e}")

    if not thumbs:
        sys.exit("no thumbnails were generated")

    if args.no_upload:
        print(f"Done (no upload). Thumbnails in: {thumbs_dir}")
        return

    print(f"Uploading full-size -> gs://{args.bucket}/{args.folder}/")
    run_upload(images, f"gs://{args.bucket}/{args.folder}/", args.dry_run)
    print(f"Uploading thumbnails -> gs://{args.bucket}/{args.folder}-thumbs/")
    run_upload(thumbs, f"gs://{args.bucket}/{args.folder}-thumbs/", args.dry_run)
    print("Done.")


if __name__ == "__main__":
    main()
